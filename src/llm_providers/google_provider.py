"""
Google AI Provider Implementation

Supports Gemini Pro, Gemini Ultra, and other Google AI models.
"""

import os
from typing import List, Optional, Iterator
import google.generativeai as genai

from .base_provider import BaseLLMProvider, LLMMessage, LLMResponse


class GoogleProvider(BaseLLMProvider):
    """Google AI (Gemini) LLM provider implementation."""

    def __init__(self, api_key: str = None, model: str = "gemini-pro", **kwargs):
        """
        Initialize Google AI provider.

        Args:
            api_key: Google API key (defaults to GOOGLE_API_KEY env var)
            model: Model name (gemini-pro, gemini-ultra, etc.)
            **kwargs: Additional Google AI-specific parameters
        """
        api_key = api_key or os.getenv("GOOGLE_API_KEY")
        super().__init__(api_key, model, **kwargs)
        self.initialize()

    def initialize(self) -> None:
        """Initialize the Google AI client."""
        if not self.validate_config():
            raise ValueError("Invalid Google AI configuration. API key is required.")

        genai.configure(api_key=self.api_key)
        self._client = genai.GenerativeModel(self.model)

    def generate(
        self,
        messages: List[LLMMessage],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> LLMResponse:
        """
        Generate a response using Google AI's API.

        Args:
            messages: List of conversation messages
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional Google AI parameters

        Returns:
            LLMResponse object
        """
        # Convert messages to Google AI format
        # Google AI uses a different conversation format
        conversation_parts = []

        for msg in messages:
            if msg.role == "system":
                # System messages are prepended to the first user message
                conversation_parts.insert(0, f"System: {msg.content}\n\n")
            elif msg.role == "user":
                conversation_parts.append(msg.content)
            elif msg.role == "assistant":
                # For multi-turn conversations, we need to use chat
                conversation_parts.append(msg.content)

        # Combine all parts
        prompt = "\n\n".join(conversation_parts)

        # Configure generation
        generation_config = {
            "temperature": temperature,
            "top_p": kwargs.get("top_p", 0.95),
            "top_k": kwargs.get("top_k", 40),
        }

        if max_tokens:
            generation_config["max_output_tokens"] = max_tokens

        # Generate response
        response = self._client.generate_content(
            prompt,
            generation_config=generation_config
        )

        # Extract response data
        usage = {
            "prompt_tokens": response.usage_metadata.prompt_token_count if hasattr(response, 'usage_metadata') else 0,
            "completion_tokens": response.usage_metadata.candidates_token_count if hasattr(response, 'usage_metadata') else 0,
            "total_tokens": response.usage_metadata.total_token_count if hasattr(response, 'usage_metadata') else 0
        }

        return LLMResponse(
            content=response.text,
            model=self.model,
            usage=usage,
            finish_reason=str(response.candidates[0].finish_reason) if response.candidates else "stop",
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
        Generate a streaming response using Google AI's API.

        Args:
            messages: List of conversation messages
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional Google AI parameters

        Yields:
            Chunks of the generated response
        """
        # Convert messages to prompt
        conversation_parts = []

        for msg in messages:
            if msg.role == "system":
                conversation_parts.insert(0, f"System: {msg.content}\n\n")
            else:
                conversation_parts.append(msg.content)

        prompt = "\n\n".join(conversation_parts)

        # Configure generation
        generation_config = {
            "temperature": temperature,
            "top_p": kwargs.get("top_p", 0.95),
            "top_k": kwargs.get("top_k", 40),
        }

        if max_tokens:
            generation_config["max_output_tokens"] = max_tokens

        # Generate streaming response
        response = self._client.generate_content(
            prompt,
            generation_config=generation_config,
            stream=True
        )

        for chunk in response:
            if chunk.text:
                yield chunk.text

    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text.

        Args:
            text: Text to count tokens for

        Returns:
            Number of tokens
        """
        try:
            result = self._client.count_tokens(text)
            return result.total_tokens
        except Exception:
            # Fallback approximation
            return len(text) // 4

    def get_model_info(self) -> dict:
        """Get Google AI model information."""
        info = super().get_model_info()
        info.update({
            "provider": "Google AI",
            "supports_streaming": True,
            "supports_function_calling": True,
            "context_window": self._get_context_window()
        })
        return info

    def _get_context_window(self) -> int:
        """Get context window size for the model."""
        if "gemini-pro" in self.model:
            return 32768
        elif "gemini-ultra" in self.model:
            return 32768
        else:
            return 8192  # Default
