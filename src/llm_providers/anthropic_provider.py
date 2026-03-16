"""
Anthropic Provider Implementation

Supports Claude 3 Opus, Sonnet, Haiku, and other Anthropic models.
"""

import os
from typing import List, Optional, Iterator
from anthropic import Anthropic

from .base_provider import BaseLLMProvider, LLMMessage, LLMResponse


class AnthropicProvider(BaseLLMProvider):
    """Anthropic (Claude) LLM provider implementation."""

    def __init__(self, api_key: str = None, model: str = "claude-3-opus-20240229", **kwargs):
        """
        Initialize Anthropic provider.

        Args:
            api_key: Anthropic API key (defaults to ANTHROPIC_API_KEY env var)
            model: Model name (claude-3-opus-20240229, claude-3-sonnet-20240229, etc.)
            **kwargs: Additional Anthropic-specific parameters
        """
        api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        super().__init__(api_key, model, **kwargs)
        self.initialize()

    def initialize(self) -> None:
        """Initialize the Anthropic client."""
        if not self.validate_config():
            raise ValueError("Invalid Anthropic configuration. API key is required.")

        self._client = Anthropic(api_key=self.api_key)

    def generate(
        self,
        messages: List[LLMMessage],
        temperature: float = 0.7,
        max_tokens: Optional[int] = 4096,
        **kwargs
    ) -> LLMResponse:
        """
        Generate a response using Anthropic's API.

        Args:
            messages: List of conversation messages
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional Anthropic parameters

        Returns:
            LLMResponse object
        """
        # Separate system message from conversation
        system_message = None
        conversation_messages = []

        for msg in messages:
            if msg.role == "system":
                system_message = msg.content
            else:
                conversation_messages.append({
                    "role": msg.role,
                    "content": msg.content
                })

        # Prepare API call parameters
        api_params = {
            "model": self.model,
            "messages": conversation_messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            **kwargs
        }

        if system_message:
            api_params["system"] = system_message

        # Make API call
        response = self._client.messages.create(**api_params)

        # Extract response data
        usage = {
            "prompt_tokens": response.usage.input_tokens,
            "completion_tokens": response.usage.output_tokens,
            "total_tokens": response.usage.input_tokens + response.usage.output_tokens
        }

        return LLMResponse(
            content=response.content[0].text,
            model=response.model,
            usage=usage,
            finish_reason=response.stop_reason,
            raw_response=response
        )

    def stream_generate(
        self,
        messages: List[LLMMessage],
        temperature: float = 0.7,
        max_tokens: Optional[int] = 4096,
        **kwargs
    ) -> Iterator[str]:
        """
        Generate a streaming response using Anthropic's API.

        Args:
            messages: List of conversation messages
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional Anthropic parameters

        Yields:
            Chunks of the generated response
        """
        # Separate system message from conversation
        system_message = None
        conversation_messages = []

        for msg in messages:
            if msg.role == "system":
                system_message = msg.content
            else:
                conversation_messages.append({
                    "role": msg.role,
                    "content": msg.content
                })

        # Prepare API call parameters
        api_params = {
            "model": self.model,
            "messages": conversation_messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": True,
            **kwargs
        }

        if system_message:
            api_params["system"] = system_message

        # Make streaming API call
        with self._client.messages.stream(**api_params) as stream:
            for text in stream.text_stream:
                yield text

    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text.

        Note: Anthropic uses a different tokenizer. This is an approximation.

        Args:
            text: Text to count tokens for

        Returns:
            Approximate number of tokens
        """
        # Anthropic's tokenizer is not publicly available
        # Use approximation: ~4 characters per token
        return len(text) // 4

    def get_model_info(self) -> dict:
        """Get Anthropic model information."""
        info = super().get_model_info()
        info.update({
            "provider": "Anthropic",
            "supports_streaming": True,
            "supports_function_calling": False,
            "context_window": self._get_context_window()
        })
        return info

    def _get_context_window(self) -> int:
        """Get context window size for the model."""
        if "opus" in self.model:
            return 200000
        elif "sonnet" in self.model:
            return 200000
        elif "haiku" in self.model:
            return 200000
        else:
            return 100000  # Default
