"""
Google Gemini Provider - Implementation for Google Gemini API

Uses the Google GenAI SDK to make API calls.
Only requires an API key.
"""

from typing import Optional
from google import genai
from .base import BaseLLMProvider
from app.utils.logger import get_logger

logger = get_logger("llm_provider.gemini")


class GeminiProvider(BaseLLMProvider):
    """
    Google Gemini provider implementation.

    Uses Google's GenAI API.
    Requires: api_key, model
    """

    MODELS = [
        'gemini-1.5-flash',
        'gemini-1.5-pro',
        'gemini-2.0-flash',
        'gemini-2.0-flash-lite',
        'gemini-2.5-flash',
        'gemini-2.5-flash-lite',
        'gemini-2.5-pro',
    ]

    def __init__(self, request_id: str, api_key: str, model: str, endpoint: Optional[str] = None):
        """
        Initialize Gemini provider.

        Args:
            request_id: Unique request identifier
            api_key: Google API key
            model: Model name (e.g., 'gemini-2.5-flash')
            endpoint: Not used for Gemini (ignored)
        """
        super().__init__(request_id, api_key, model, endpoint)

        logger.debug(f"[{self.request_id}] GeminiProvider initialized: model={self.model}")

    async def _make_api_call(
        self,
        prompt: str,
        system_instruction: Optional[str],
        json_mode: bool
    ) -> str:
        """
        Make Gemini API call.

        Args:
            prompt: User prompt
            system_instruction: System instruction
            json_mode: Request JSON response format

        Returns:
            Response text
        """
        logger.debug(f"[{self.request_id}] Gemini API call: model={self.model}")

        client = genai.Client(api_key=self.api_key)

        config = {}
        if system_instruction:
            config["system_instruction"] = system_instruction
        if json_mode:
            config["response_mime_type"] = "application/json"

        response = client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=config
        )

        result = response.text
        logger.debug(f"[{self.request_id}] Gemini response: {len(result)} chars")

        return result

    def validate_credentials(self) -> bool:
        """
        Validate Gemini credentials with a minimal API call.

        Returns:
            True if credentials are valid
        """
        if self._is_mock_mode():
            return False

        try:
            client = genai.Client(api_key=self.api_key)

            # Minimal test call
            response = client.models.generate_content(
                model=self.model,
                contents="test"
            )

            return response.text is not None

        except Exception as e:
            logger.error(f"[{self.request_id}] Gemini credential validation failed: {e}")
            return False
