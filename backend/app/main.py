
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import os
import traceback
import json
import time

from app.agents.normalizer import run_normalizer
from app.agents.strategist import run_strategist
from app.agents.instrumenter import run_instrumenter
from app.agents.tracer import run_tracer
from app.agents.narrator import run_narrator
from app.agents.educational_flow_generator import generate_educational_flow
from app.agents.algorithm_explainer import get_algorithm_explanation
from app.utils.logger import get_logger, print_startup_banner, log_error_with_context

load_dotenv()

logger = get_logger("main")

print_startup_banner()

app = FastAPI(title="AlgoInsight Brain API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class UserRequest(BaseModel):
    problem_text: str
    context_toggles: list[str] = []
    recommended_algorithm: str | None = None


class AlgorithmExplainRequest(BaseModel):
    algorithm_name: str
    problem_context: str = ""

STATIC_FALLBACK = {
    "title": "Median of Stream (Static Fallback)",
    "strategy": "Two-Heap Strategy",
    "strategy_details": "This fallback is served when the LLM pipeline fails. It demonstrates the Two-Heap approach to finding a median in O(log N) time.",
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

    logger.info(f"📥 Incoming {request.method} {request.url.path}")

    try:
        response = await call_next(request)
        duration = time.time() - start_time

        logger.info(f"📤 Response {response.status_code} in {duration:.2f}s")
        return response
    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"❌ Request failed after {duration:.2f}s: {str(e)}")
        raise

@app.get("/")
def health_check():
    logger.info("Health check requested")
    return {"status": "AlgoInsight Brain is Active", "backend": True}


@app.post("/algorithm/generate")
async def generate_algorithm_explanation_endpoint(request: AlgorithmExplainRequest):
    logger.info("="*70)
    logger.info(f"📚 ALGORITHM EXPLANATION REQUEST")
    logger.info(f"Algorithm: {request.algorithm_name}")
    if request.problem_context:
        logger.info(f"Problem Context: {request.problem_context[:100]}...")
    logger.info("="*70)

    try:
        start_time = time.time()

        algorithm_data = await get_algorithm_explanation(
            algorithm_name=request.algorithm_name,
            problem_context=request.problem_context
        )

        duration = time.time() - start_time
        logger.info(f"✅ Algorithm explanation ready in {duration:.2f}s")
        logger.info(f"   Algorithm ID: {algorithm_data.get('algorithm_id', 'unknown')}")
        logger.info(f"   Category: {algorithm_data.get('category', 'unknown')}")

        return algorithm_data

    except Exception as e:
        logger.error(f"❌ Failed to generate algorithm explanation: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate algorithm explanation: {str(e)}"
        )


@app.post("/analyze")
async def analyze_algorithm(request: UserRequest):
    logger.info("="*70)
    logger.info(f"🚀 NEW ANALYSIS REQUEST")
    logger.info(f"Problem: {request.problem_text[:100]}{'...' if len(request.problem_text) > 100 else ''}")
    logger.info(f"Context: {request.context_toggles}")
    logger.info("="*70)

    try:
        logger.info("🔹 [1/5] Starting NORMALIZER...")
        start_time = time.time()
        normalized_data = await run_normalizer(request.problem_text, request.context_toggles)
        logger.info(f"✅ [1/5] NORMALIZER completed in {time.time() - start_time:.2f}s")
        logger.debug(f"Normalized data: {json.dumps(normalized_data, indent=2)}")

        logger.info("🔹 [2/5] Starting STRATEGIST...")
        start_time = time.time()

        if request.recommended_algorithm:
            logger.info(f"🎯 Learning mode recommended: {request.recommended_algorithm}")
            normalized_data['recommended_algorithm_hint'] = request.recommended_algorithm

        blueprint = await run_strategist(normalized_data)
        selected_strategy = blueprint.get('selected_strategy_for_instrumentation', 'Unknown')
        logger.info(f"✅ [2/5] STRATEGIST completed in {time.time() - start_time:.2f}s")
        logger.info(f"Selected Strategy: {selected_strategy}")
        logger.debug(f"Blueprint: {json.dumps(blueprint, indent=2)}")

        logger.info("🔹 [3/5] Starting INSTRUMENTER...")
        start_time = time.time()

        example_inputs = normalized_data.get('example_inputs', [])
        if example_inputs:
            logger.info(f"📋 Using {len(example_inputs)} example input(s) from problem statement")
            logger.debug(f"Example inputs: {json.dumps(example_inputs, indent=2)}")

        spy_code_data = await run_instrumenter(blueprint, normalized_data)
        logger.info(f"✅ [3/5] INSTRUMENTER completed in {time.time() - start_time:.2f}s")
        logger.info(f"Entry point: {spy_code_data.get('entry_point', 'Unknown')}")
        logger.debug(f"Generated code preview:\n{spy_code_data.get('code', '')[:500]}...")

        logger.info("🔹 [4/5] Starting TRACER (Sandbox Execution)...")
        start_time = time.time()
        trace_results = run_tracer(spy_code_data['code'], spy_code_data['entry_point'])

        if trace_results.get('status') == 'error':
            logger.error(f"❌ TRACER failed!")
            logger.error(f"Error logs:\n{trace_results.get('logs', 'No logs available')}")
            logger.warning("🔄 Returning STATIC_FALLBACK")
            return STATIC_FALLBACK

        if not trace_results.get('trace_data'):
            logger.warning("⚠️  TRACER returned empty trace_data")
            logger.warning("🔄 Returning STATIC_FALLBACK")
            return STATIC_FALLBACK

        logger.info(f"✅ [4/5] TRACER completed in {time.time() - start_time:.2f}s")
        logger.info(f"Captured {trace_results.get('step_count', 0)} execution steps")

        logger.info("🔹 [5/5] Starting NARRATOR...")
        start_time = time.time()

        logger.info("Providing Narrator with problem context and algorithm rationale")

        final_trace = await run_narrator(
            trace_data=trace_results['trace_data'],
            algo_name=blueprint['selected_strategy_for_instrumentation'],
            normalized_data=normalized_data,
            blueprint=blueprint
        )
        logger.info(f"✅ [5/5] NARRATOR completed in {time.time() - start_time:.2f}s")

        if not final_trace or not final_trace.get('frames'):
            logger.error("❌ NARRATOR produced no frames")
            logger.warning("🔄 Returning STATIC_FALLBACK")
            return STATIC_FALLBACK

        logger.info("="*70)
        logger.info(f"✅ PIPELINE SUCCESS - Generated {len(final_trace.get('frames', []))} frames")
        logger.info(f"Title: {final_trace.get('title', 'N/A')}")
        logger.info("="*70)

        return final_trace

    except Exception as e:
        logger.error("="*70)
        logger.error(f"💥 PIPELINE CRASH!")
        log_error_with_context(logger, e, {
            "problem_text": request.problem_text[:100],
            "context_toggles": request.context_toggles
        })
        logger.error("="*70)
        logger.warning("🔄 Returning STATIC_FALLBACK")
        return STATIC_FALLBACK

@app.post("/learn")
async def learn_algorithm(request: UserRequest):
    logger.info("="*70)
    logger.info(f"🎓 NEW LEARNING REQUEST")
    logger.info(f"Problem: {request.problem_text[:100]}{'...' if len(request.problem_text) > 100 else ''}")
    logger.info(f"Context: {request.context_toggles}")
    logger.info("="*70)

    try:
        logger.info("🔹 Generating educational flow...")
        start_time = time.time()

        educational_flow = await generate_educational_flow(
            problem_text=request.problem_text,
            context_toggles=request.context_toggles
        )

        duration = time.time() - start_time
        logger.info(f"✅ Educational flow generated in {duration:.2f}s")
        logger.info(f"Phases generated: {educational_flow.get('total_phases', 0)}")
        logger.info("="*70)

        return educational_flow

    except Exception as e:
        logger.error("="*70)
        logger.error(f"💥 EDUCATIONAL FLOW GENERATION FAILED!")
        log_error_with_context(logger, e, {
            "problem_text": request.problem_text[:100],
            "context_toggles": request.context_toggles
        })
        logger.error("="*70)

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

@app.on_event("startup")
async def startup_event():
    logger.info("🌟 FastAPI server started successfully")
    logger.info(f"📍 Base URL: http://0.0.0.0:8000")
    logger.info(f"📚 API Docs: http://0.0.0.0:8000/docs")

    api_keys_status = []
    if os.getenv("API_KEY"):
        api_keys_status.append("✓ Gemini API Key")
    if os.getenv("AZURE_OPENAI_API_KEY"):
        api_keys_status.append("✓ Azure OpenAI Key")

    if api_keys_status:
        logger.info(f"🔑 API Keys: {', '.join(api_keys_status)}")
    else:
        logger.warning("⚠️  No API keys detected - will use mock responses")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("🛑 FastAPI server shutting down...")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
