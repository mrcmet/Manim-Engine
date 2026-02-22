"""Anthropic Claude AI provider implementation.

This module provides integration with Anthropic's Claude API
for generating Manim animation code.
"""

import httpx
from ai.provider_base import AIProvider, AIProviderError
from core.models.ai_config import AIProviderConfig


class AnthropicProvider(AIProvider):
    """Provider for Anthropic's Claude API.

    Uses the Messages API to generate responses from Claude models.
    """

    API_URL = "https://api.anthropic.com/v1/messages"
    API_VERSION = "2023-06-01"
    DEFAULT_MODEL = "claude-sonnet-4-5-20250929"
    DEFAULT_MAX_TOKENS = 4096

    def __init__(self, config: AIProviderConfig):
        """Initialize the Anthropic provider.

        Args:
            config: Provider configuration with api_key and optional model_name.
        """
        super().__init__(config)

        # Use configured model or fall back to default
        if not self._config.model_name:
            self._config.model_name = self.DEFAULT_MODEL

    def validate_config(self) -> tuple[bool, str | None]:
        """Validate the Anthropic configuration.

        Returns:
            Tuple of (is_valid, error_message).
        """
        if not self._config.api_key:
            return False, "API key is required for Anthropic provider"

        if not isinstance(self._config.api_key, str) or len(self._config.api_key.strip()) == 0:
            return False, "API key must be a non-empty string"

        return True, None

    async def generate(
        self,
        messages: list[dict],
        system_prompt: str | None = None
    ) -> str:
        """Generate a response using Claude.

        Args:
            messages: List of message dicts with 'role' and 'content' keys.
            system_prompt: Optional system prompt.

        Returns:
            The generated text response.

        Raises:
            AIProviderError: If the API call fails or returns an error.
        """
        if not messages:
            raise AIProviderError("Messages list cannot be empty")

        # Validate messages format
        for idx, msg in enumerate(messages):
            if not isinstance(msg, dict):
                raise AIProviderError(f"Message at index {idx} must be a dict")
            if 'role' not in msg or 'content' not in msg:
                raise AIProviderError(
                    f"Message at index {idx} must have 'role' and 'content' keys"
                )

        headers = {
            "x-api-key": self._config.api_key,
            "anthropic-version": self.API_VERSION,
            "content-type": "application/json",
        }

        payload = {
            "model": self.model,
            "max_tokens": self._config.max_tokens or self.DEFAULT_MAX_TOKENS,
            "messages": messages,
        }

        if system_prompt:
            payload["system"] = system_prompt

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    self.API_URL,
                    headers=headers,
                    json=payload,
                )

                if response.status_code != 200:
                    error_detail = self._extract_error_message(response)
                    raise AIProviderError(
                        f"Anthropic API returned status {response.status_code}: {error_detail}"
                    )

                response_data = response.json()

                # Extract the text content from the response
                content = response_data.get("content", [])
                if not content or not isinstance(content, list):
                    raise AIProviderError("Invalid response format: missing content")

                # Find the text block
                text_content = None
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "text":
                        text_content = block.get("text")
                        break

                if text_content is None:
                    raise AIProviderError("No text content found in response")

                return text_content

        except httpx.TimeoutException as e:
            raise AIProviderError(
                f"Request to Anthropic API timed out after 60 seconds"
            ) from e
        except httpx.NetworkError as e:
            raise AIProviderError(
                f"Network error connecting to Anthropic API: {str(e)}"
            ) from e
        except httpx.HTTPError as e:
            raise AIProviderError(
                f"HTTP error during Anthropic API call: {str(e)}"
            ) from e
        except AIProviderError:
            raise
        except Exception as e:
            raise AIProviderError(
                f"Unexpected error during Anthropic API call: {str(e)}"
            ) from e

    def _extract_error_message(self, response: httpx.Response) -> str:
        """Extract error message from API response.

        Args:
            response: The HTTP response object.

        Returns:
            A human-readable error message.
        """
        try:
            error_data = response.json()
            if isinstance(error_data, dict):
                if "error" in error_data:
                    error_obj = error_data["error"]
                    if isinstance(error_obj, dict):
                        return error_obj.get("message", str(error_obj))
                    return str(error_obj)
            return response.text[:200]  # First 200 chars if JSON parsing fails
        except Exception:
            return response.text[:200]
