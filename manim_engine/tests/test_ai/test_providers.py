"""Tests for AI provider configuration validation."""

import pytest
from core.models.ai_config import AIProviderConfig
from ai.providers.anthropic_provider import AnthropicProvider
from ai.providers.openai_provider import OpenAIProvider
from ai.providers.gemini_provider import GeminiProvider
from ai.providers.ollama_provider import OllamaProvider


class TestAnthropicProvider:
    """Test suite for AnthropicProvider configuration validation."""

    def test_validate_config_with_valid_api_key(self):
        """Test that validation succeeds with a valid API key."""
        config = AIProviderConfig(
            provider_name="anthropic",
            api_key="sk-ant-test-key-123",
            model_name="claude-sonnet-4-5-20250929"
        )
        provider = AnthropicProvider(config)

        is_valid, error = provider.validate_config()

        assert is_valid is True
        assert error is None

    def test_validate_config_with_missing_api_key(self):
        """Test that validation fails when API key is missing."""
        config = AIProviderConfig(
            provider_name="anthropic",
            api_key=None,
            model_name="claude-sonnet-4-5-20250929"
        )
        provider = AnthropicProvider(config)

        is_valid, error = provider.validate_config()

        assert is_valid is False
        assert "API key" in error

    def test_validate_config_with_empty_api_key(self):
        """Test that validation fails when API key is empty."""
        config = AIProviderConfig(
            provider_name="anthropic",
            api_key="   ",
            model_name="claude-sonnet-4-5-20250929"
        )
        provider = AnthropicProvider(config)

        is_valid, error = provider.validate_config()

        assert is_valid is False
        assert "non-empty string" in error

    def test_default_model_is_set(self):
        """Test that default model is set when not provided."""
        config = AIProviderConfig(
            provider_name="anthropic",
            api_key="test-key"
        )
        provider = AnthropicProvider(config)

        assert provider.model == AnthropicProvider.DEFAULT_MODEL


class TestOpenAIProvider:
    """Test suite for OpenAIProvider configuration validation."""

    def test_validate_config_with_valid_api_key(self):
        """Test that validation succeeds with a valid API key."""
        config = AIProviderConfig(
            provider_name="openai",
            api_key="sk-test-key-123",
            model_name="gpt-4o"
        )
        provider = OpenAIProvider(config)

        is_valid, error = provider.validate_config()

        assert is_valid is True
        assert error is None

    def test_validate_config_with_missing_api_key(self):
        """Test that validation fails when API key is missing."""
        config = AIProviderConfig(
            provider_name="openai",
            api_key=None,
            model_name="gpt-4o"
        )
        provider = OpenAIProvider(config)

        is_valid, error = provider.validate_config()

        assert is_valid is False
        assert "API key" in error

    def test_validate_config_with_empty_api_key(self):
        """Test that validation fails when API key is empty."""
        config = AIProviderConfig(
            provider_name="openai",
            api_key="",
            model_name="gpt-4o"
        )
        provider = OpenAIProvider(config)

        is_valid, error = provider.validate_config()

        assert is_valid is False
        assert "API key" in error

    def test_default_model_is_set(self):
        """Test that default model is set when not provided."""
        config = AIProviderConfig(
            provider_name="openai",
            api_key="test-key"
        )
        provider = OpenAIProvider(config)

        assert provider.model == OpenAIProvider.DEFAULT_MODEL


class TestGeminiProvider:
    """Test suite for GeminiProvider configuration validation."""

    def test_validate_config_with_valid_api_key(self):
        """Test that validation succeeds with a valid API key."""
        config = AIProviderConfig(
            provider_name="gemini",
            api_key="test-api-key-123",
            model_name="gemini-2.0-flash"
        )
        provider = GeminiProvider(config)

        is_valid, error = provider.validate_config()

        assert is_valid is True
        assert error is None

    def test_validate_config_with_missing_api_key(self):
        """Test that validation fails when API key is missing."""
        config = AIProviderConfig(
            provider_name="gemini",
            api_key=None,
            model_name="gemini-2.0-flash"
        )
        provider = GeminiProvider(config)

        is_valid, error = provider.validate_config()

        assert is_valid is False
        assert "API key" in error

    def test_validate_config_with_empty_api_key(self):
        """Test that validation fails when API key is empty."""
        config = AIProviderConfig(
            provider_name="gemini",
            api_key="   ",
            model_name="gemini-2.0-flash"
        )
        provider = GeminiProvider(config)

        is_valid, error = provider.validate_config()

        assert is_valid is False
        assert "non-empty string" in error

    def test_default_model_is_set(self):
        """Test that default model is set when not provided."""
        config = AIProviderConfig(
            provider_name="gemini",
            api_key="test-key"
        )
        provider = GeminiProvider(config)

        assert provider.model == GeminiProvider.DEFAULT_MODEL


class TestOllamaProvider:
    """Test suite for OllamaProvider configuration validation."""

    def test_validate_config_with_default_base_url(self):
        """Test that validation succeeds with default base URL."""
        config = AIProviderConfig(
            provider_name="ollama",
            model_name="llama3"
        )
        provider = OllamaProvider(config)

        is_valid, error = provider.validate_config()

        assert is_valid is True
        assert error is None

    def test_validate_config_with_custom_base_url(self):
        """Test that validation succeeds with custom base URL."""
        config = AIProviderConfig(
            provider_name="ollama",
            model_name="llama3"
        )
        config.base_url = "http://192.168.1.100:11434"
        provider = OllamaProvider(config)

        is_valid, error = provider.validate_config()

        assert is_valid is True
        assert error is None

    def test_validate_config_with_invalid_base_url(self):
        """Test that validation fails with invalid base URL."""
        config = AIProviderConfig(
            provider_name="ollama",
            model_name="llama3"
        )
        config.base_url = "not-a-valid-url"
        provider = OllamaProvider(config)

        is_valid, error = provider.validate_config()

        assert is_valid is False
        assert "http://" in error or "https://" in error

    def test_default_model_is_set(self):
        """Test that default model is set when not provided."""
        config = AIProviderConfig(provider_name="ollama")
        provider = OllamaProvider(config)

        assert provider.model == OllamaProvider.DEFAULT_MODEL

    def test_base_url_trailing_slash_removed(self):
        """Test that trailing slashes are removed from base URL."""
        config = AIProviderConfig(provider_name="ollama")
        config.base_url = "http://localhost:11434/"
        provider = OllamaProvider(config)

        assert not provider._base_url.endswith('/')
