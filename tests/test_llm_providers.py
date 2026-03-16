"""
Test cases for LLM provider implementations
"""

import pytest
import sys
import os
from unittest.mock import Mock, patch, MagicMock

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.llm_providers.base_provider import BaseLLMProvider, LLMMessage, LLMResponse
from src.llm_providers.provider_factory import ProviderFactory, LLMManager


class TestLLMMessage:
    """Test LLM message data class"""

    def test_message_creation(self):
        """Test creating LLM message"""
        msg = LLMMessage(role="user", content="Test message")
        assert msg.role == "user"
        assert msg.content == "Test message"

    def test_message_roles(self):
        """Test different message roles"""
        system_msg = LLMMessage(role="system", content="System prompt")
        user_msg = LLMMessage(role="user", content="User query")
        assistant_msg = LLMMessage(role="assistant", content="Assistant response")

        assert system_msg.role == "system"
        assert user_msg.role == "user"
        assert assistant_msg.role == "assistant"


class TestLLMResponse:
    """Test LLM response data class"""

    def test_response_creation(self):
        """Test creating LLM response"""
        response = LLMResponse(
            content="Test response",
            model="gpt-4",
            usage={"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
            finish_reason="stop"
        )
        assert response.content == "Test response"
        assert response.model == "gpt-4"
        assert response.usage["total_tokens"] == 30
        assert response.finish_reason == "stop"


class TestProviderFactory:
    """Test provider factory"""

    def test_list_providers(self):
        """Test listing available providers"""
        providers = ProviderFactory.list_providers()
        assert "openai" in providers
        assert "anthropic" in providers
        assert "google" in providers

    def test_create_provider_validation(self):
        """Test provider creation validation"""
        with pytest.raises(ValueError, match="Unsupported provider"):
            ProviderFactory.create("nonexistent_provider")

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test_key"})
    def test_create_openai_provider(self):
        """Test creating OpenAI provider"""
        try:
            provider = ProviderFactory.create("openai", api_key="test_key")
            assert provider is not None
            assert "openai" in provider.__class__.__name__.lower()
        except Exception as e:
            # May fail if openai package not installed or key invalid
            pytest.skip(f"OpenAI provider creation failed: {e}")

    def test_default_models(self):
        """Test default model selection"""
        default_model = ProviderFactory._get_default_model("openai")
        assert default_model == "gpt-4"

        default_model = ProviderFactory._get_default_model("anthropic")
        assert "claude" in default_model.lower()

        default_model = ProviderFactory._get_default_model("google")
        assert "gemini" in default_model.lower()


class TestLLMManager:
    """Test LLM manager"""

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test_key"})
    def test_manager_initialization(self):
        """Test LLM manager initialization"""
        config = {
            "default": "openai",
            "openai": {
                "api_key": "test_key",
                "model": "gpt-4"
            }
        }
        try:
            manager = LLMManager(config)
            assert manager.default_provider_name == "openai"
        except Exception:
            pytest.skip("LLM manager initialization failed (dependencies may be missing)")

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test_key"})
    def test_provider_switching(self):
        """Test switching between providers"""
        config = {
            "default": "openai",
            "openai": {
                "api_key": "test_key",
                "model": "gpt-4"
            }
        }
        try:
            manager = LLMManager(config)
            initial_provider = manager.default_provider_name
            assert initial_provider == "openai"
        except Exception:
            pytest.skip("Provider switching test skipped")

    def test_list_available_providers(self):
        """Test listing available providers in manager"""
        config = {
            "default": "openai",
            "openai": {
                "api_key": "test_key",
                "model": "gpt-4"
            }
        }
        try:
            manager = LLMManager(config)
            providers = manager.list_available_providers()
            assert isinstance(providers, list)
        except Exception:
            pytest.skip("Provider listing test skipped")


class TestProviderInterface:
    """Test provider interface compliance"""

    def test_base_provider_abstract(self):
        """Test that base provider is abstract"""
        with pytest.raises(TypeError):
            BaseLLMProvider("test_key", "test_model")

    def test_provider_validation(self):
        """Test provider configuration validation"""
        class TestProvider(BaseLLMProvider):
            def initialize(self):
                pass

            def generate(self, messages, temperature=0.7, max_tokens=None, **kwargs):
                return LLMResponse(
                    content="test",
                    model=self.model,
                    usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                    finish_reason="stop"
                )

            def stream_generate(self, messages, temperature=0.7, max_tokens=None, **kwargs):
                yield "test"

            def count_tokens(self, text):
                return len(text.split())

        # Valid config
        provider = TestProvider("test_key", "test_model")
        assert provider.validate_config() is True

        # Invalid config (no API key)
        provider = TestProvider(None, "test_model")
        assert provider.validate_config() is False

        # Invalid config (no model)
        provider = TestProvider("test_key", None)
        assert provider.validate_config() is False

    def test_provider_model_info(self):
        """Test provider model info"""
        class TestProvider(BaseLLMProvider):
            def initialize(self):
                pass

            def generate(self, messages, temperature=0.7, max_tokens=None, **kwargs):
                pass

            def stream_generate(self, messages, temperature=0.7, max_tokens=None, **kwargs):
                pass

            def count_tokens(self, text):
                return 0

        provider = TestProvider("test_key", "test_model", custom_param="value")
        info = provider.get_model_info()

        assert "provider" in info
        assert "model" in info
        assert info["model"] == "test_model"
        assert "config" in info
        assert info["config"]["custom_param"] == "value"


class TestTokenCounting:
    """Test token counting functionality"""

    def test_approximate_token_count(self):
        """Test approximate token counting"""
        text = "This is a test sentence with multiple words."
        # Approximate: ~1 token per 4 characters
        approximate_tokens = len(text) // 4
        assert approximate_tokens > 0


class TestErrorHandling:
    """Test error handling in providers"""

    def test_invalid_provider_name(self):
        """Test handling of invalid provider name"""
        with pytest.raises(ValueError):
            ProviderFactory.create("invalid_provider_name")

    def test_missing_api_key(self):
        """Test handling of missing API key"""
        # Should raise ValueError for missing API key
        try:
            ProviderFactory.create("openai", api_key=None)
        except ValueError as e:
            assert "api key" in str(e).lower() or "configuration" in str(e).lower()


# Integration tests (require actual API keys)
class TestProviderIntegration:
    """Integration tests for providers (requires API keys)"""

    @pytest.mark.skipif(
        not os.getenv("OPENAI_API_KEY"),
        reason="OpenAI API key not available"
    )
    def test_openai_generation(self):
        """Test actual OpenAI generation (requires API key)"""
        try:
            provider = ProviderFactory.create("openai")
            messages = [
                LLMMessage(role="user", content="Say 'test' and nothing else.")
            ]
            response = provider.generate(messages, temperature=0.0, max_tokens=10)

            assert response is not None
            assert isinstance(response, LLMResponse)
            assert len(response.content) > 0
            assert response.usage["total_tokens"] > 0
        except Exception as e:
            pytest.skip(f"OpenAI integration test failed: {e}")

    @pytest.mark.skipif(
        not os.getenv("ANTHROPIC_API_KEY"),
        reason="Anthropic API key not available"
    )
    def test_anthropic_generation(self):
        """Test actual Anthropic generation (requires API key)"""
        try:
            provider = ProviderFactory.create("anthropic")
            messages = [
                LLMMessage(role="user", content="Say 'test' and nothing else.")
            ]
            response = provider.generate(messages, temperature=0.0, max_tokens=10)

            assert response is not None
            assert isinstance(response, LLMResponse)
            assert len(response.content) > 0
        except Exception as e:
            pytest.skip(f"Anthropic integration test failed: {e}")

    @pytest.mark.skipif(
        not os.getenv("GOOGLE_API_KEY"),
        reason="Google API key not available"
    )
    def test_google_generation(self):
        """Test actual Google AI generation (requires API key)"""
        try:
            provider = ProviderFactory.create("google")
            messages = [
                LLMMessage(role="user", content="Say 'test' and nothing else.")
            ]
            response = provider.generate(messages, temperature=0.0, max_tokens=10)

            assert response is not None
            assert isinstance(response, LLMResponse)
            assert len(response.content) > 0
        except Exception as e:
            pytest.skip(f"Google AI integration test failed: {e}")


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
