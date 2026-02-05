"""
Azure OpenAI Provider - Implementation for Azure OpenAI Service

Uses the Azure OpenAI SDK to make API calls.
Requires both an API key and an endpoint URL.
"""

import os
from typing import Optional
from openai import AzureOpenAI
from .base import BaseLLMProvider
from app.utils.logger import get_logger

logger = get_logger("llm_provider.azure")


class AzureOpenAIProvider(BaseLLMProvider):
    """
    Azure OpenAI provider implementation.

    Uses Azure's deployment-based model hosting.
    Requires: api_key, endpoint, model (deployment name)
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
        Initialize Azure OpenAI provider.

        Args:
            request_id: Unique request identifier
            api_key: Azure OpenAI API key
            model: Deployment name (e.g., 'gpt-4o')
            endpoint: Azure endpoint URL (required)
        """
        if not endpoint:
            raise ValueError("Azure OpenAI requires an endpoint URL")

        super().__init__(request_id, api_key, model, endpoint)

        self.api_version = os.getenv('AZURE_API_VERSION', '2024-08-01-preview')

        logger.debug(f"[{self.request_id}] AzureOpenAIProvider initialized: "
                    f"model={self.model}, endpoint={self.endpoint[:30]}...")

    async def _make_api_call(
        self,
        prompt: str,
        system_instruction: Optional[str],
        json_mode: bool
    ) -> str:
        """
        Make Azure OpenAI API call.

        Args:
            prompt: User prompt
            system_instruction: System instruction
            json_mode: Request JSON response format

        Returns:
            Response text
        """
        logger.debug(f"[{self.request_id}] Azure API call: deployment={self.model}")

        client = AzureOpenAI(
            api_key=self.api_key,
            api_version=self.api_version,
            azure_endpoint=self.endpoint
        )

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
        logger.debug(f"[{self.request_id}] Azure response: {len(result)} chars")

        return result

    def validate_credentials(self) -> bool:
        """
        Validate Azure OpenAI credentials with a minimal API call.

        Returns:
            True if credentials are valid
        """
        if self._is_mock_mode():
            return False

        try:
            client = AzureOpenAI(
                api_key=self.api_key,
                api_version=self.api_version,
                azure_endpoint=self.endpoint
            )

            # Minimal test call
            response = client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "test"}],
                max_tokens=5
            )

            return response.choices[0].message.content is not None

        except Exception as e:
            logger.error(f"[{self.request_id}] Azure credential validation failed: {e}")
            return False
