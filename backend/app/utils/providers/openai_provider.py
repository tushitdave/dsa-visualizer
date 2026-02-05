"""
OpenAI Provider - Implementation for OpenAI API

Uses the OpenAI SDK to make API calls.
Only requires an API key (no endpoint URL).
"""

from typing import Optional
from openai import OpenAI
from .base import BaseLLMProvider
from app.utils.logger import get_logger

logger = get_logger("llm_provider.openai")


class OpenAIProvider(BaseLLMProvider):
    """
    OpenAI provider implementation.

    Uses OpenAI's direct API.
    Requires: api_key, model
    """

    MODELS = [
        'gpt-4o',
        'gpt-4o-mini',
        'gpt-4.1',
        'gpt-4.1-mini',
        'gpt-4.1-nano'
    ]

    def __init__(self, request_id: str, api_key: str, model: str, endpoint: Optional[str] = None):
        """
        Initialize OpenAI provider.

        Args:
            request_id: Unique request identifier
            api_key: OpenAI API key
            model: Model name (e.g., 'gpt-4o')
            endpoint: Not used for OpenAI (ignored)
        """
        super().__init__(request_id, api_key, model, endpoint)

        logger.debug(f"[{self.request_id}] OpenAIProvider initialized: model={self.model}")

    async def _make_api_call(
        self,
        prompt: str,
        system_instruction: Optional[str],
        json_mode: bool
    ) -> str:
        """
        Make OpenAI API call.

        Args:
            prompt: User prompt
            system_instruction: System instruction
            json_mode: Request JSON response format

        Returns:
            Response text
        """
        logger.debug(f"[{self.request_id}] OpenAI API call: model={self.model}")

        client = OpenAI(api_key=self.api_key)

        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})

        response = client.chat.completions.create(
            model=self.model,
            messages=messages,
            response_format={"type": "json_object"} if json_mode else {"type": "text"},
            temperature=0.3
        )

        result = response.choices[0].message.content
        logger.debug(f"[{self.request_id}] OpenAI response: {len(result)} chars")

        return result

    def validate_credentials(self) -> bool:
        """
        Validate OpenAI credentials with a minimal API call.

        Returns:
            True if credentials are valid
        """
        if self._is_mock_mode():
            return False

        try:
            client = OpenAI(api_key=self.api_key)

            # Minimal test call
            response = client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "test"}],
                max_tokens=5
            )

            return response.choices[0].message.content is not None

        except Exception as e:
            logger.error(f"[{self.request_id}] OpenAI credential validation failed: {e}")
            return False
