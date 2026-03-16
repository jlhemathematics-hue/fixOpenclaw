"""
OpenAI Provider Implementation

Supports GPT-4, GPT-3.5-turbo, and other OpenAI models.
"""

import os
from typing import List, Optional, Iterator
import tiktoken
from openai import OpenAI

from .base_provider import BaseLLMProvider, LLMMessage, LLMResponse


class OpenAIProvider(BaseLLMProvider):
    """OpenAI LLM provider implementation."""

    def __init__(self, api_key: str = None, model: str = "gpt-4", **kwargs):
        """
        Initialize OpenAI provider.

        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            model: Model name (gpt-4, gpt-3.5-turbo, etc.)
            **kwargs: Additional OpenAI-specific parameters
        """
        api_key = api_key or os.getenv("OPENAI_API_KEY")
        super().__init__(api_key, model, **kwargs)
        self.initialize()

    def initialize(self) -> None:
        """Initialize the OpenAI client."""
        if not self.validate_config():
            raise ValueError("Invalid OpenAI configuration. API key is required.")

        self._client = OpenAI(api_key=self.api_key)

        # Initialize tokenizer
        try:
            self._tokenizer = tiktoken.encoding_for_model(self.model)
        except KeyError:
            # Fallback to cl100k_base for newer models
            self._tokenizer = tiktoken.get_encoding("cl100k_base")

    def generate(
        self,
        messages: List[LLMMessage],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> LLMResponse:
        """
        Generate a response using OpenAI's API.

        Args:
            messages: List of conversation messages
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional OpenAI parameters

        Returns:
            LLMResponse object
        """
        # Convert LLMMessage to OpenAI format
        openai_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]

        # Make API call
        response = self._client.chat.completions.create(
            model=self.model,
            messages=openai_messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )

        # Extract response data
        choice = response.choices[0]
        usage = {
            "prompt_tokens": response.usage.prompt_tokens,
            "completion_tokens": response.usage.completion_tokens,
            "total_tokens": response.usage.total_tokens
        }

        return LLMResponse(
            content=choice.message.content,
            model=response.model,
            usage=usage,
            finish_reason=choice.finish_reason,
            raw_response=response
        )

    def stream_generate(
        self,
        messages: List[LLMMessage],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> Iterator[str]:
        """
        Generate a streaming response using OpenAI's API.

        Args:
            messages: List of conversation messages
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional OpenAI parameters

        Yields:
            Chunks of the generated response
        """
        # Convert LLMMessage to OpenAI format
        openai_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]

        # Make streaming API call
        stream = self._client.chat.completions.create(
            model=self.model,
            messages=openai_messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
            **kwargs
        )

        for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                yield chunk.choices[0].delta.content

    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text using tiktoken.

        Args:
            text: Text to count tokens for

        Returns:
            Number of tokens
        """
        return len(self._tokenizer.encode(text))

    def get_model_info(self) -> dict:
        """Get OpenAI model information."""
        info = super().get_model_info()
        info.update({
            "provider": "OpenAI",
            "supports_streaming": True,
            "supports_function_calling": "gpt-4" in self.model or "gpt-3.5-turbo" in self.model
        })
        return info
