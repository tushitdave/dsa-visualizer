"""
Request Context - Carries request-specific configuration through the pipeline

This ensures each request is isolated and uses the correct LLM provider/model
even when multiple users are making concurrent requests.
"""

import os
import uuid
from dataclasses import dataclass, field
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


@dataclass
class RequestContext:
    """
    Carries all request-specific configuration through the pipeline.

    Each API request creates its own RequestContext, ensuring:
    - Request isolation (no shared state between requests)
    - Correct provider routing (each user gets their selected provider)
    - Traceability (unique request_id for logging)
    - Session tracking (correlate requests from same user)
    """

    request_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    session_id: str = ""  # Session ID for request correlation and credential lookup
    provider: str = "azure"  # 'azure' | 'openai' | 'gemini'
    model: str = "gpt-4o"
    api_key: str = ""
    azure_endpoint: Optional[str] = None  # Required only for Azure

    def __post_init__(self):
        """Validate the context after initialization"""
        valid_providers = ['azure', 'openai', 'gemini']
        if self.provider not in valid_providers:
            raise ValueError(f"Invalid provider: {self.provider}. Must be one of: {valid_providers}")

        if self.provider == 'azure' and not self.azure_endpoint:
            raise ValueError("Azure OpenAI requires 'azure_endpoint' to be provided")

        if not self.api_key:
            raise ValueError("API key is required")

    @classmethod
    def from_request(cls, llm_config: dict, session_id: str = "") -> 'RequestContext':
        """
        Create context from frontend LLM configuration.

        Args:
            llm_config: Dict with keys: provider, model, api_key, azure_endpoint (optional)
            session_id: Session ID from X-Session-ID header for request correlation

        Returns:
            RequestContext instance
        """
        return cls(
            request_id=str(uuid.uuid4())[:8],
            session_id=session_id,
            provider=llm_config.get('provider', 'azure'),
            model=llm_config.get('model', 'gpt-4o'),
            api_key=llm_config.get('api_key', ''),
            azure_endpoint=llm_config.get('azure_endpoint')
        )

    @classmethod
    def from_env(cls, session_id: str = "") -> 'RequestContext':
        """
        Create context from environment variables (backward compatibility).

        Falls back to .env configuration when no llm_config is provided.

        Args:
            session_id: Session ID from X-Session-ID header for request correlation

        Returns:
            RequestContext instance
        """
        # Determine provider from available keys
        azure_key = os.getenv('AZURE_OPENAI_API_KEY', '')
        gemini_key = os.getenv('API_KEY', '') or os.getenv('GEMINI_API_KEY', '')
        openai_key = os.getenv('OPENAI_API_KEY', '')

        # Priority: Azure > OpenAI > Gemini
        if azure_key and len(azure_key) > 15 and 'YOUR_' not in azure_key:
            return cls(
                request_id=str(uuid.uuid4())[:8],
                session_id=session_id,
                provider='azure',
                model=os.getenv('AZURE_DEPLOYMENT_NAME', 'gpt-4o'),
                api_key=azure_key,
                azure_endpoint=os.getenv('AZURE_OPENAI_ENDPOINT', '')
            )
        elif openai_key and len(openai_key) > 15 and 'YOUR_' not in openai_key:
            return cls(
                request_id=str(uuid.uuid4())[:8],
                session_id=session_id,
                provider='openai',
                model='gpt-4o',
                api_key=openai_key,
                azure_endpoint=None
            )
        elif gemini_key and len(gemini_key) > 15 and 'YOUR_' not in gemini_key:
            return cls(
                request_id=str(uuid.uuid4())[:8],
                session_id=session_id,
                provider='gemini',
                model='gemini-2.5-flash',
                api_key=gemini_key,
                azure_endpoint=None
            )
        else:
            # No valid keys - will use mock responses
            # Create a dummy context that will trigger mock mode
            return cls(
                request_id=str(uuid.uuid4())[:8],
                session_id=session_id,
                provider='azure',
                model='gpt-4o',
                api_key='MOCK_MODE_NO_KEY',
                azure_endpoint='https://mock.openai.azure.com/'
            )

    def to_dict(self) -> dict:
        """Convert context to dictionary (for logging, excluding api_key)"""
        return {
            'request_id': self.request_id,
            'session_id': self.session_id[:8] + '...' if len(self.session_id) > 8 else self.session_id,
            'provider': self.provider,
            'model': self.model,
            'azure_endpoint': self.azure_endpoint[:30] + '...' if self.azure_endpoint else None
        }

    def __repr__(self) -> str:
        """Safe string representation (hides api_key)"""
        session_short = self.session_id[:8] if self.session_id else 'none'
        return (f"RequestContext(request_id='{self.request_id}', "
                f"session_id='{session_short}', "
                f"provider='{self.provider}', model='{self.model}')")
