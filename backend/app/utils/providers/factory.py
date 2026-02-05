"""
LLM Provider Factory - Creates provider instances based on configuration

Uses the Factory pattern to instantiate the correct provider
based on the user's selection.
"""

from typing import Dict, List, Type
from .base import BaseLLMProvider
from .azure_provider import AzureOpenAIProvider
from .openai_provider import OpenAIProvider
from .gemini_provider import GeminiProvider
from app.utils.logger import get_logger

logger = get_logger("llm_provider.factory")


class LLMProviderFactory:
    """
    Factory for creating LLM provider instances.

    Provides:
    - Provider creation based on name
    - Model validation for each provider
    - Available providers and models listing
    """

    # Map provider names to their implementation classes
    PROVIDER_MAP: Dict[str, Type[BaseLLMProvider]] = {
        'azure': AzureOpenAIProvider,
        'openai': OpenAIProvider,
        'gemini': GeminiProvider
    }

    # Provider metadata for frontend
    PROVIDER_INFO = {
        'azure': {
            'name': 'Azure OpenAI',
            'requires_endpoint': True,
            'description': 'Microsoft Azure hosted OpenAI models'
        },
        'openai': {
            'name': 'OpenAI',
            'requires_endpoint': False,
            'description': 'OpenAI direct API'
        },
        'gemini': {
            'name': 'Google Gemini',
            'requires_endpoint': False,
            'description': 'Google Gemini models'
        }
    }

    @classmethod
    def create(
        cls,
        request_id: str,
        provider: str,
        model: str,
        api_key: str,
        endpoint: str = None
    ) -> BaseLLMProvider:
        """
        Create an LLM provider instance.

        Args:
            request_id: Unique request identifier for logging
            provider: Provider name ('azure', 'openai', 'gemini')
            model: Model name
            api_key: API key for authentication
            endpoint: API endpoint (required for Azure)

        Returns:
            BaseLLMProvider instance

        Raises:
            ValueError: If provider is unknown or model is invalid
        """
        # Validate provider
        if provider not in cls.PROVIDER_MAP:
            raise ValueError(
                f"Unknown provider: '{provider}'. "
                f"Available providers: {list(cls.PROVIDER_MAP.keys())}"
            )

        provider_class = cls.PROVIDER_MAP[provider]

        # Validate model
        valid_models = provider_class.MODELS
        if model not in valid_models:
            raise ValueError(
                f"Invalid model '{model}' for provider '{provider}'. "
                f"Valid models: {valid_models}"
            )

        # Validate Azure-specific requirements
        if provider == 'azure' and not endpoint:
            raise ValueError("Azure OpenAI requires 'azure_endpoint' to be provided")

        # Create and return the provider
        provider_instance = provider_class(
            request_id=request_id,
            api_key=api_key,
            model=model,
            endpoint=endpoint
        )

        logger.info(f"[{request_id}] Created {provider_class.__name__} with model={model}")

        return provider_instance

    @classmethod
    def create_from_context(cls, context) -> BaseLLMProvider:
        """
        Create provider from a RequestContext object.

        Args:
            context: RequestContext instance

        Returns:
            BaseLLMProvider instance
        """
        return cls.create(
            request_id=context.request_id,
            provider=context.provider,
            model=context.model,
            api_key=context.api_key,
            endpoint=context.azure_endpoint
        )

    @classmethod
    def get_available_providers(cls) -> Dict:
        """
        Get all available providers with their models.

        Returns:
            Dict with provider info and models for frontend
        """
        providers = {}

        for provider_name, provider_class in cls.PROVIDER_MAP.items():
            info = cls.PROVIDER_INFO.get(provider_name, {})
            providers[provider_name] = {
                'name': info.get('name', provider_name),
                'models': provider_class.MODELS,
                'requires_endpoint': info.get('requires_endpoint', False),
                'description': info.get('description', '')
            }

        return providers

    @classmethod
    def get_models_for_provider(cls, provider: str) -> List[str]:
        """
        Get available models for a specific provider.

        Args:
            provider: Provider name

        Returns:
            List of model names
        """
        if provider not in cls.PROVIDER_MAP:
            return []

        return cls.PROVIDER_MAP[provider].MODELS

    @classmethod
    def is_valid_provider(cls, provider: str) -> bool:
        """Check if provider name is valid"""
        return provider in cls.PROVIDER_MAP

    @classmethod
    def is_valid_model(cls, provider: str, model: str) -> bool:
        """Check if model is valid for provider"""
        if provider not in cls.PROVIDER_MAP:
            return False
        return model in cls.PROVIDER_MAP[provider].MODELS
