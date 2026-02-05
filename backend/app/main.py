
from fastapi import FastAPI, HTTPException, Request, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Literal, List
import re
from dotenv import load_dotenv
import os
import traceback
import json
import time

from app.utils.request_context import RequestContext
from app.utils.providers.factory import LLMProviderFactory
from app.utils.credential_store import get_credential_store
from app.utils.rate_limiter import get_rate_limiter
from app.pipeline import Pipeline
from app.utils.logger import get_logger, print_startup_banner, log_error_with_context
from app.router.smart_router import get_smart_router, initialize_router

# Legacy imports for backward compatibility
from app.agents.normalizer import run_normalizer
from app.agents.strategist import run_strategist
from app.agents.instrumenter import run_instrumenter
from app.agents.tracer import run_tracer
from app.agents.narrator import run_narrator
from app.agents.educational_flow_generator import generate_educational_flow
from app.agents.algorithm_explainer import get_algorithm_explanation

load_dotenv()

logger = get_logger("main")

print_startup_banner()

app = FastAPI(title="AlgoInsight Brain API")

# =============================================================================
# CORS Configuration (SECURITY)
# =============================================================================
# Set ALLOWED_ORIGINS env var to comma-separated list of allowed origins
# Example: ALLOWED_ORIGINS=https://your-app.vercel.app,http://localhost:5173
# WARNING: Using wildcard (*) in production is a security risk!

ALLOWED_ORIGINS_RAW = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:5173")
ALLOWED_ORIGINS = [origin.strip() for origin in ALLOWED_ORIGINS_RAW.split(",") if origin.strip()]

# SECURITY: Don't allow credentials with wildcard origins
is_wildcard = "*" in ALLOWED_ORIGINS or len(ALLOWED_ORIGINS) == 0
if is_wildcard:
    logger.warning("SECURITY WARNING: CORS configured with wildcard (*) - credentials will be disabled")
    logger.warning("Set ALLOWED_ORIGINS environment variable for production!")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if is_wildcard else ALLOWED_ORIGINS,
    allow_credentials=not is_wildcard,  # SECURITY: Disable credentials with wildcard
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],  # Only methods we actually use
    allow_headers=["Content-Type", "Accept", "X-Session-ID", "X-Admin-Key"],  # Only headers we need
)


# =============================================================================
# Request Models with Input Validation (SECURITY)
# =============================================================================

# Constants for validation
MAX_PROBLEM_LENGTH = 50000  # 50KB max for problem text
MAX_MODEL_LENGTH = 100
MAX_API_KEY_LENGTH = 500
MAX_ENDPOINT_LENGTH = 500
MAX_ALGORITHM_NAME_LENGTH = 200
MAX_CONTEXT_TOGGLES = 10
VALID_CONTEXT_TOGGLES = {'Embedded System', 'High Throughput', 'Low Memory'}


class LLMConfig(BaseModel):
    """LLM provider configuration from frontend"""
    provider: Literal['azure', 'openai', 'gemini']
    model: str = Field(..., min_length=1, max_length=MAX_MODEL_LENGTH)
    api_key: str = Field(..., min_length=10, max_length=MAX_API_KEY_LENGTH)
    azure_endpoint: Optional[str] = Field(None, max_length=MAX_ENDPOINT_LENGTH)

    @field_validator('model')
    @classmethod
    def validate_model(cls, v: str) -> str:
        # Only allow alphanumeric, dots, and hyphens
        if not re.match(r'^[\w\.\-]+$', v):
            raise ValueError('Model name contains invalid characters')
        return v

    @field_validator('azure_endpoint')
    @classmethod
    def validate_endpoint(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v.strip():
            v = v.strip()
            # Must be a valid HTTPS URL
            if not v.startswith('https://'):
                raise ValueError('Azure endpoint must use HTTPS')
            # Allow various Azure domains: openai.azure.com, cognitiveservices.azure.com, etc.
            if not re.match(r'^https://[\w\.\-]+\.azure\.com/?.*$', v):
                raise ValueError('Invalid Azure endpoint URL format')
        return v


class UserRequest(BaseModel):
    """Analysis/Learning request with input validation"""
    problem_text: str = Field(..., min_length=10, max_length=MAX_PROBLEM_LENGTH)
    context_toggles: List[str] = Field(default_factory=list, max_length=MAX_CONTEXT_TOGGLES)
    recommended_algorithm: Optional[str] = Field(None, max_length=MAX_ALGORITHM_NAME_LENGTH)
    llm_config: Optional[LLMConfig] = None

    @field_validator('context_toggles')
    @classmethod
    def validate_context_toggles(cls, v: List[str]) -> List[str]:
        # Validate each toggle is from the allowed set
        for toggle in v:
            if toggle not in VALID_CONTEXT_TOGGLES:
                raise ValueError(f'Invalid context toggle: {toggle}. Allowed: {VALID_CONTEXT_TOGGLES}')
        return v

    @field_validator('recommended_algorithm')
    @classmethod
    def validate_algorithm(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            # Allow common characters in algorithm names (alphanumeric, spaces, punctuation)
            # Block only dangerous characters: < > { } | \ ` $
            if re.search(r'[<>{}|\\`$]', v):
                raise ValueError('Algorithm name contains invalid characters')
        return v


class AlgorithmExplainRequest(BaseModel):
    """Algorithm explanation request with validation"""
    algorithm_name: str = Field(..., min_length=1, max_length=MAX_ALGORITHM_NAME_LENGTH)
    problem_context: str = Field("", max_length=MAX_PROBLEM_LENGTH)
    llm_config: Optional[LLMConfig] = None

    @field_validator('algorithm_name')
    @classmethod
    def validate_algorithm_name(cls, v: str) -> str:
        # Allow common characters in algorithm names (alphanumeric, spaces, common punctuation)
        # Block only dangerous characters that could be used for injection: < > { } | \ ` $
        if re.search(r'[<>{}|\\`$]', v):
            raise ValueError('Algorithm name contains invalid characters')
        return v.strip()


class StoreCredentialsRequest(BaseModel):
    """Request to store credentials securely on backend"""
    session_id: str = Field(..., min_length=32, max_length=64)  # UUID format
    provider: Literal['azure', 'openai', 'gemini']
    model: str = Field(..., min_length=1, max_length=MAX_MODEL_LENGTH)
    api_key: str = Field(..., min_length=10, max_length=MAX_API_KEY_LENGTH)
    azure_endpoint: Optional[str] = Field(None, max_length=MAX_ENDPOINT_LENGTH)

    @field_validator('session_id')
    @classmethod
    def validate_session_id(cls, v: str) -> str:
        # Must be a valid UUID format (allow both upper and lowercase)
        if not re.match(r'^[a-fA-F0-9\-]{32,64}$', v):
            raise ValueError('Invalid session ID format')
        return v.lower()  # Normalize to lowercase


# =============================================================================
# Admin Authentication (SECURITY)
# =============================================================================

ADMIN_API_KEY = os.getenv("ADMIN_API_KEY", "")


async def verify_admin_key(x_admin_key: Optional[str] = Header(None, alias="X-Admin-Key")):
    """
    Dependency to verify admin API key for protected endpoints.
    Returns True if valid, raises HTTPException if not.
    """
    if not ADMIN_API_KEY:
        # If no admin key is configured, log warning but allow access in development
        logger.warning("SECURITY WARNING: ADMIN_API_KEY not set - admin endpoints unprotected!")
        return True

    if not x_admin_key:
        raise HTTPException(
            status_code=401,
            detail="Admin authentication required. Provide X-Admin-Key header."
        )

    # Constant-time comparison to prevent timing attacks
    if not _secure_compare(x_admin_key, ADMIN_API_KEY):
        logger.warning(f"Failed admin authentication attempt")
        raise HTTPException(
            status_code=403,
            detail="Invalid admin key"
        )

    return True


def _secure_compare(a: str, b: str) -> bool:
    """Constant-time string comparison to prevent timing attacks."""
    import hmac
    return hmac.compare_digest(a.encode(), b.encode())


# =============================================================================
# Rate Limiting (SECURITY)
# =============================================================================

def get_client_ip(request: Request) -> str:
    """Extract client IP from request, handling proxies."""
    # Check for forwarded header (from reverse proxy)
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        # Take the first IP in the chain
        return forwarded.split(",")[0].strip()
    # Fall back to direct client IP
    return request.client.host if request.client else "unknown"


async def check_rate_limit(request: Request, endpoint: str = "default"):
    """
    Check rate limit for the current request.
    Raises HTTPException if rate limit exceeded.
    """
    rate_limiter = get_rate_limiter()
    client_ip = get_client_ip(request)

    allowed, current, limit = rate_limiter.is_allowed(client_ip, endpoint)

    if not allowed:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Try again later. ({current}/{limit} requests per minute)",
            headers={"Retry-After": "60"}
        )


async def rate_limit_default(request: Request):
    """Rate limit dependency for general endpoints."""
    await check_rate_limit(request, "default")


async def rate_limit_analyze(request: Request):
    """Rate limit dependency for analysis endpoints (stricter limit)."""
    await check_rate_limit(request, "analyze")


STATIC_FALLBACK = {
    "title": "Median of Stream (Static Fallback)",
    "strategy": "Two-Heap Strategy",
    "strategy_details": "This fallback is served when the LLM pipeline fails.",
    "complexity": {"time": "O(log n)", "space": "O(n)"},
    "frames": [
        {
            "step_id": 0,
            "commentary": "System initialized. Pushing 10 into the Max Heap.",
            "state": {"visual_type": "heap", "data": {"max_heap": [10], "min_heap": []}, "highlights": ["max_heap"]},
            "quiz": None
        },
        {
            "step_id": 1,
            "commentary": "Balanced: Moving 10 to Min Heap.",
            "state": {"visual_type": "heap", "data": {"max_heap": [], "min_heap": [10]}, "highlights": ["min_heap"]},
            "quiz": {"question": "Why use two heaps?", "options": ["Balance", "Speed", "Random"], "correct": 0}
        }
    ]
}


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    logger.info(f"Incoming {request.method} {request.url.path}")

    try:
        response = await call_next(request)
        duration = time.time() - start_time
        logger.info(f"Response {response.status_code} in {duration:.2f}s")
        return response
    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"Request failed after {duration:.2f}s: {str(e)}")
        raise


@app.get("/")
def health_check():
    """Health check endpoint"""
    logger.info("Health check requested")
    return {"status": "AlgoInsight Brain is Active", "backend": True}


@app.get("/providers")
def get_providers():
    """
    Get available LLM providers and their models.
    Used by frontend to populate provider/model dropdowns.
    """
    providers = LLMProviderFactory.get_available_providers()
    return {"providers": providers}


@app.post("/validate-credentials")
async def validate_credentials(config: LLMConfig):
    """
    Validate LLM credentials before analysis.
    Makes a minimal API call to verify the key works.
    """
    logger.info(f"Validating credentials for provider: {config.provider}")

    try:
        # Create a temporary context for validation
        context = RequestContext(
            provider=config.provider,
            model=config.model,
            api_key=config.api_key,
            azure_endpoint=config.azure_endpoint
        )

        provider = LLMProviderFactory.create_from_context(context)
        is_valid = provider.validate_credentials()

        if is_valid:
            logger.info(f"Credentials valid for {config.provider}/{config.model}")
            return {"valid": True, "message": "Credentials validated successfully"}
        else:
            logger.warning(f"Credentials invalid for {config.provider}")
            return {"valid": False, "message": "Invalid credentials"}

    except ValueError as e:
        # SECURITY: Log details server-side, return safe message to client
        logger.error(f"Validation error: {e}")
        # ValueError usually contains user-facing info like "Azure endpoint required"
        error_msg = str(e)
        # Only pass through safe error messages
        safe_messages = ["Azure endpoint required", "Invalid provider", "API key is required"]
        if any(msg.lower() in error_msg.lower() for msg in safe_messages):
            return {"valid": False, "message": error_msg}
        return {"valid": False, "message": "Invalid configuration"}
    except Exception as e:
        # SECURITY: Never expose internal errors to client
        logger.error(f"Validation failed: {e}")
        return {"valid": False, "message": "Validation failed. Please check your credentials."}


@app.post("/algorithm/generate")
async def generate_algorithm_explanation_endpoint(request: AlgorithmExplainRequest, req: Request):
    """Generate algorithm deep-dive explanation"""
    # Extract session ID from header for request correlation
    session_id = req.headers.get("X-Session-ID", "anonymous")

    logger.info("=" * 70)
    logger.info(f"ALGORITHM EXPLANATION REQUEST")
    logger.info(f"Session: {session_id[:8]}..." if len(session_id) > 8 else f"Session: {session_id}")
    logger.info(f"Algorithm: {request.algorithm_name}")
    logger.info("=" * 70)

    try:
        start_time = time.time()

        # Create context from config or environment
        if request.llm_config:
            context = RequestContext.from_request(request.llm_config.dict(), session_id)
            pipeline = Pipeline(context)
            algorithm_data = await pipeline.get_algorithm_explanation(
                request.algorithm_name,
                request.problem_context
            )
        else:
            # Legacy path - use global provider
            algorithm_data = await get_algorithm_explanation(
                algorithm_name=request.algorithm_name,
                problem_context=request.problem_context
            )

        duration = time.time() - start_time
        logger.info(f"Algorithm explanation ready in {duration:.2f}s")

        return algorithm_data

    except Exception as e:
        # SECURITY: Log details server-side only, return generic message to client
        logger.error(f"Failed to generate algorithm explanation: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail="Failed to generate algorithm explanation. Please try again later."
        )


@app.post("/analyze")
async def analyze_algorithm(request: UserRequest, req: Request, _: None = Depends(rate_limit_analyze)):
    """Main analysis endpoint - runs 5-agent pipeline (rate limited)"""
    # Extract session ID from header for request correlation
    session_id = req.headers.get("X-Session-ID", "anonymous")

    logger.info("=" * 70)
    logger.info(f"NEW ANALYSIS REQUEST")
    logger.info(f"Session: {session_id[:8]}..." if len(session_id) > 8 else f"Session: {session_id}")
    logger.info(f"Problem: {request.problem_text[:100]}{'...' if len(request.problem_text) > 100 else ''}")
    logger.info(f"Context: {request.context_toggles}")
    if request.llm_config:
        logger.info(f"Provider: {request.llm_config.provider}/{request.llm_config.model}")
    logger.info("=" * 70)

    try:
        # Create context: Priority is Request body > Stored credentials > Environment
        if request.llm_config and request.llm_config.api_key:
            # Use credentials from request body
            context = RequestContext.from_request(request.llm_config.dict(), session_id)
            logger.info(f"[{session_id[:8]}] Using credentials from request body")
        elif session_id and session_id != "anonymous":
            # Try to get stored credentials for this session
            store = get_credential_store()
            stored_creds = store.get_credentials(session_id)
            if stored_creds:
                context = RequestContext.from_request(stored_creds, session_id)
                logger.info(f"[{session_id[:8]}] Using stored session credentials")
            else:
                context = RequestContext.from_env(session_id)
                logger.info(f"[{session_id[:8]}] No stored credentials, using environment")
        else:
            context = RequestContext.from_env(session_id)
            logger.info(f"[{session_id[:8]}] Using environment credentials")

        logger.info(f"[{context.request_id}][{session_id[:8]}] Using provider: {context.provider}/{context.model}")

        # Create pipeline with this request's context
        pipeline = Pipeline(context)

        # Run the full analysis
        result = await pipeline.run_analysis(
            problem_text=request.problem_text,
            context_toggles=request.context_toggles,
            recommended_algorithm=request.recommended_algorithm
        )

        if not result:
            logger.warning(f"[{context.request_id}][{session_id[:8]}] Pipeline returned None, using fallback")
            fallback = STATIC_FALLBACK.copy()
            fallback['_meta'] = {
                'request_id': context.request_id,
                'provider_used': context.provider,
                'model_used': context.model,
                'fallback': True
            }
            return fallback

        logger.info(f"[{context.request_id}][{session_id[:8]}] PIPELINE SUCCESS - {len(result.get('frames', []))} frames")
        return result

    except Exception as e:
        logger.error("=" * 70)
        logger.error(f"PIPELINE CRASH!")
        log_error_with_context(logger, e, {
            "problem_text": request.problem_text[:100],
            "context_toggles": request.context_toggles
        })
        logger.error("=" * 70)

        fallback = STATIC_FALLBACK.copy()
        fallback['_meta'] = {'error': str(e), 'fallback': True}
        return fallback


@app.post("/learn")
async def learn_algorithm(request: UserRequest, req: Request, _: None = Depends(rate_limit_analyze)):
    """Educational flow generation endpoint (rate limited)"""
    # Extract session ID from header for request correlation
    session_id = req.headers.get("X-Session-ID", "anonymous")

    logger.info("=" * 70)
    logger.info(f"NEW LEARNING REQUEST")
    logger.info(f"Session: {session_id[:8]}..." if len(session_id) > 8 else f"Session: {session_id}")
    logger.info(f"Problem: {request.problem_text[:100]}{'...' if len(request.problem_text) > 100 else ''}")
    logger.info(f"Context: {request.context_toggles}")
    if request.llm_config:
        logger.info(f"Provider: {request.llm_config.provider}/{request.llm_config.model}")
    logger.info("=" * 70)

    try:
        # Create context: Priority is Request body > Stored credentials > Environment
        if request.llm_config and request.llm_config.api_key:
            # Use credentials from request body
            context = RequestContext.from_request(request.llm_config.dict(), session_id)
            logger.info(f"[{session_id[:8]}] Using credentials from request body")
        elif session_id and session_id != "anonymous":
            # Try to get stored credentials for this session
            store = get_credential_store()
            stored_creds = store.get_credentials(session_id)
            if stored_creds:
                context = RequestContext.from_request(stored_creds, session_id)
                logger.info(f"[{session_id[:8]}] Using stored session credentials")
            else:
                context = RequestContext.from_env(session_id)
                logger.info(f"[{session_id[:8]}] No stored credentials, using environment")
        else:
            context = RequestContext.from_env(session_id)
            logger.info(f"[{session_id[:8]}] Using environment credentials")

        logger.info(f"[{context.request_id}][{session_id[:8]}] Using provider: {context.provider}/{context.model}")

        # Create pipeline
        pipeline = Pipeline(context)

        # Run educational flow generation
        educational_flow = await pipeline.run_learning(
            problem_text=request.problem_text,
            context_toggles=request.context_toggles
        )

        logger.info(f"[{context.request_id}][{session_id[:8]}] Educational flow completed")
        return educational_flow

    except Exception as e:
        logger.error("=" * 70)
        logger.error(f"EDUCATIONAL FLOW GENERATION FAILED!")
        log_error_with_context(logger, e, {
            "problem_text": request.problem_text[:100],
            "context_toggles": request.context_toggles
        })
        logger.error("=" * 70)

        return {
            "learning_mode": True,
            "total_phases": 1,
            "phases": [{
                "phase": "understand_problem",
                "phase_number": 1,
                "phase_title": "Understanding the Problem",
                "content": {
                    "problem_statement": request.problem_text,
                    "breakdown": {
                        "objective": "Solve this DSA problem",
                        "input": "See problem statement",
                        "output": "See problem statement",
                        "constraints": []
                    },
                    "key_insights": [
                        "Let's analyze this problem together",
                        "We'll find the best solution step by step"
                    ]
                }
            }],
            "current_phase": 0,
            "error": "Educational flow generation failed - showing basic fallback"
        }


# =============================================================================
# Session Credential Management Endpoints (Phase 3: Secure Credential Storage)
# =============================================================================

@app.post("/session/store-credentials")
async def store_credentials_endpoint(request: StoreCredentialsRequest, req: Request, _: None = Depends(rate_limit_default)):
    """
    Store encrypted credentials for a session (rate limited).
    Credentials are encrypted at rest and automatically expire after 24 hours.
    """
    logger.info(f"Storing credentials for session {request.session_id[:8]}...")

    store = get_credential_store()
    success = store.store_credentials(
        session_id=request.session_id,
        provider=request.provider,
        model=request.model,
        api_key=request.api_key,
        azure_endpoint=request.azure_endpoint
    )

    if success:
        return {"success": True, "message": "Credentials stored securely"}
    else:
        raise HTTPException(status_code=500, detail="Failed to store credentials")


@app.get("/session/{session_id}/credentials")
async def get_credentials_endpoint(session_id: str):
    """
    Get credential metadata (not the actual API key) for a session.
    Used by frontend to check if session has stored credentials.
    """
    store = get_credential_store()
    metadata = store.get_credential_metadata(session_id)

    if not metadata:
        return {"exists": False}

    return metadata


@app.delete("/session/{session_id}")
async def delete_session_endpoint(session_id: str):
    """Delete a session's credentials."""
    logger.info(f"Deleting credentials for session {session_id[:8]}...")

    store = get_credential_store()
    store.delete_session(session_id)
    return {"success": True, "message": "Session credentials deleted"}


@app.get("/session/stats")
async def get_session_stats(_: bool = Depends(verify_admin_key)):
    """Get credential store statistics (admin endpoint - requires X-Admin-Key header)."""
    store = get_credential_store()
    return store.get_stats()


@app.post("/session/cleanup")
async def cleanup_expired_sessions(_: bool = Depends(verify_admin_key)):
    """Clean up expired session credentials (admin endpoint - requires X-Admin-Key header)."""
    store = get_credential_store()
    count = store.cleanup_expired()
    return {"success": True, "cleaned_up": count}


# =============================================================================
# Router and Cache Management Endpoints
# =============================================================================

@app.get("/router/stats")
async def get_router_stats(_: bool = Depends(verify_admin_key)):
    """Get smart router and cache statistics (admin endpoint - requires X-Admin-Key header)."""
    router = get_smart_router()
    return router.get_stats()


@app.get("/router/algorithms")
def get_available_algorithms():
    """Get list of algorithms with instant response capability."""
    router = get_smart_router()
    algorithms = router.get_available_algorithms()
    return {
        "count": len(algorithms),
        "algorithms": algorithms,
        "note": "These algorithms have pre-computed traces for instant (<100ms) response"
    }


@app.post("/router/clear-cache")
async def clear_cache(_: bool = Depends(verify_admin_key)):
    """Clear all cached data (admin endpoint - requires X-Admin-Key header)."""
    from app.cache import get_cache_manager
    cache = get_cache_manager()
    cache.clear_all()
    logger.info("Cache cleared via API (admin action)")
    return {"status": "success", "message": "All caches cleared"}


@app.on_event("startup")
async def startup_event():
    logger.info("FastAPI server started successfully")
    logger.info(f"Base URL: http://0.0.0.0:8000")
    logger.info(f"API Docs: http://0.0.0.0:8000/docs")

    # Initialize smart router and warm up cache
    logger.info("Initializing smart router and warming cache...")
    try:
        router = await initialize_router()
        stats = router.get_stats()
        logger.info(f"Router ready: {stats.get('library_stats', {}).get('total_algorithms', 0)} algorithms loaded")
    except Exception as e:
        logger.error(f"Router initialization failed: {e}")

    # Log available providers
    providers = LLMProviderFactory.get_available_providers()
    logger.info(f"Available providers: {list(providers.keys())}")

    api_keys_status = []
    if os.getenv("API_KEY") or os.getenv("GEMINI_API_KEY"):
        api_keys_status.append("Gemini API Key")
    if os.getenv("AZURE_OPENAI_API_KEY"):
        api_keys_status.append("Azure OpenAI Key")
    if os.getenv("OPENAI_API_KEY"):
        api_keys_status.append("OpenAI Key")

    if api_keys_status:
        logger.info(f"Environment API Keys: {', '.join(api_keys_status)}")
    else:
        logger.warning("No environment API keys - frontend must provide credentials")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("FastAPI server shutting down...")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
