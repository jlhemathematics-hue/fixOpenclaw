"""
LLM Provider Factory

Factory class for creating LLM provider instances.
"""

from typing import Dict, Any, Optional
from .base_provider import BaseLLMProvider
from .openai_provider import OpenAIProvider
from .anthropic_provider import AnthropicProvider
from .google_provider import GoogleProvider


class ProviderFactory:
    """Factory for creating LLM provider instances."""

    _providers = {
        "openai": OpenAIProvider,
        "anthropic": AnthropicProvider,
        "google": GoogleProvider,
    }

    @classmethod
    def create(
        cls,
        provider_name: str,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        **kwargs
    ) -> BaseLLMProvider:
        """
        Create an LLM provider instance.

        Args:
            provider_name: Name of the provider (openai, anthropic, google, etc.)
            api_key: API key for the provider
            model: Model name to use
            **kwargs: Additional provider-specific configuration

        Returns:
            Initialized provider instance

        Raises:
            ValueError: If provider name is not supported
        """
        provider_name = provider_name.lower()

        if provider_name not in cls._providers:
            raise ValueError(
                f"Unsupported provider: {provider_name}. "
                f"Supported providers: {', '.join(cls._providers.keys())}"
            )

        provider_class = cls._providers[provider_name]

        # Create provider with default model if not specified
        if model is None:
            model = cls._get_default_model(provider_name)

        return provider_class(api_key=api_key, model=model, **kwargs)

    @classmethod
    def register_provider(
        cls,
        name: str,
        provider_class: type
    ) -> None:
        """
        Register a custom provider.

        Args:
            name: Name to register the provider under
            provider_class: Provider class (must inherit from BaseLLMProvider)
        """
        if not issubclass(provider_class, BaseLLMProvider):
            raise ValueError(
                f"Provider class must inherit from BaseLLMProvider"
            )

        cls._providers[name.lower()] = provider_class

    @classmethod
    def list_providers(cls) -> list:
        """
        List all available providers.

        Returns:
            List of provider names
        """
        return list(cls._providers.keys())

    @classmethod
    def _get_default_model(cls, provider_name: str) -> str:
        """Get default model for a provider."""
        defaults = {
            "openai": "gpt-4",
            "anthropic": "claude-3-opus-20240229",
            "google": "gemini-pro",
        }
        return defaults.get(provider_name, "default")


class LLMManager:
    """Manager for handling multiple LLM providers with fallback support."""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize LLM manager.

        Args:
            config: Configuration dictionary with provider settings
        """
        self.config = config
        self.providers: Dict[str, BaseLLMProvider] = {}
        self.default_provider_name = config.get("default", "openai")
        self._initialize_providers()

    def _initialize_providers(self) -> None:
        """Initialize all configured providers."""
        for provider_name, provider_config in self.config.items():
            if provider_name == "default":
                continue

            try:
                provider = ProviderFactory.create(
                    provider_name=provider_name,
                    **provider_config
                )
                self.providers[provider_name] = provider
            except Exception as e:
                print(f"Warning: Failed to initialize {provider_name}: {e}")

    def get_provider(self, name: Optional[str] = None) -> BaseLLMProvider:
        """
        Get a provider instance.

        Args:
            name: Provider name (uses default if not specified)

        Returns:
            Provider instance

        Raises:
            ValueError: If provider is not available
        """
        provider_name = name or self.default_provider_name

        if provider_name not in self.providers:
            raise ValueError(f"Provider not available: {provider_name}")

        return self.providers[provider_name]

    def switch_provider(self, name: str) -> None:
        """
        Switch the default provider.

        Args:
            name: Provider name to switch to

        Raises:
            ValueError: If provider is not available
        """
        if name not in self.providers:
            raise ValueError(f"Provider not available: {name}")

        self.default_provider_name = name

    def list_available_providers(self) -> list:
        """
        List all initialized providers.

        Returns:
            List of provider names
        """
        return list(self.providers.keys())

    def generate_with_fallback(
        self,
        messages: list,
        preferred_provider: Optional[str] = None,
        **kwargs
    ):
        """
        Generate response with automatic fallback to other providers.

        Args:
            messages: Conversation messages
            preferred_provider: Preferred provider name
            **kwargs: Generation parameters

        Returns:
            LLMResponse from successful provider

        Raises:
            Exception: If all providers fail
        """
        # Try preferred provider first
        providers_to_try = []

        if preferred_provider and preferred_provider in self.providers:
            providers_to_try.append(preferred_provider)

        # Add default provider
        if self.default_provider_name not in providers_to_try:
            providers_to_try.append(self.default_provider_name)

        # Add remaining providers as fallback
        for name in self.providers.keys():
            if name not in providers_to_try:
                providers_to_try.append(name)

        # Try each provider
        last_error = None
        for provider_name in providers_to_try:
            try:
                provider = self.providers[provider_name]
                return provider.generate(messages, **kwargs)
            except Exception as e:
                last_error = e
                print(f"Provider {provider_name} failed: {e}")
                continue

        raise Exception(f"All providers failed. Last error: {last_error}")
