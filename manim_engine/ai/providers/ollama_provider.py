"""Ollama local AI provider implementation.

This module provides integration with Ollama for running
local AI models to generate Manim animation code.
"""

import httpx
from ai.provider_base import AIProvider, AIProviderError
from core.models.ai_config import AIProviderConfig


class OllamaProvider(AIProvider):
    """Provider for Ollama local AI models.

    Uses the Ollama chat API to generate responses from locally-hosted models.
    """

    DEFAULT_BASE_URL = "http://localhost:11434"
    DEFAULT_MODEL = "llama3"
    DEFAULT_TIMEOUT = 120.0  # 2 minutes for local models

    def __init__(self, config: AIProviderConfig):
        """Initialize the Ollama provider.

        Args:
            config: Provider configuration with optional base_url and model_name.
        """
        super().__init__(config)

        # Use configured values or fall back to defaults
        if not self._config.model_name:
            self._config.model_name = self.DEFAULT_MODEL

        # Get base URL from config or use default
        self._base_url = getattr(self._config, 'base_url', None) or self.DEFAULT_BASE_URL

        # Ensure base_url doesn't end with a slash
        if self._base_url.endswith('/'):
            self._base_url = self._base_url[:-1]

    def validate_config(self) -> tuple[bool, str | None]:
        """Validate the Ollama configuration.

        Returns:
            Tuple of (is_valid, error_message).
        """
        # Ollama doesn't require an API key for local usage
        # Just validate that base_url is set
        if not self._base_url:
            return False, "Base URL is required for Ollama provider"

        if not isinstance(self._base_url, str) or len(self._base_url.strip()) == 0:
            return False, "Base URL must be a non-empty string"

        # Basic URL validation
        if not (self._base_url.startswith('http://') or self._base_url.startswith('https://')):
            return False, "Base URL must start with http:// or https://"

        return True, None

    async def generate(
        self,
        messages: list[dict],
        system_prompt: str | None = None
    ) -> str:
        """Generate a response using Ollama.

        Args:
            messages: List of message dicts with 'role' and 'content' keys.
            system_prompt: Optional system prompt (added as first system message).

        Returns:
            The generated text response.

        Raises:
            AIProviderError: If the API call fails or returns an error.
        """
        if not messages and not system_prompt:
            raise AIProviderError("Either messages or system_prompt must be provided")

        # Build the messages array
        api_messages = []

        # Add system prompt as a system message if provided
        if system_prompt:
            api_messages.append({
                "role": "system",
                "content": system_prompt
            })

        # Add user messages
        for idx, msg in enumerate(messages):
            if not isinstance(msg, dict):
                raise AIProviderError(f"Message at index {idx} must be a dict")
            if 'role' not in msg or 'content' not in msg:
                raise AIProviderError(
                    f"Message at index {idx} must have 'role' and 'content' keys"
                )
            api_messages.append(msg)

        api_url = f"{self._base_url}/api/chat"

        payload = {
            "model": self.model,
            "messages": api_messages,
            "stream": False,  # We want a single response, not streaming
        }

        try:
            async with httpx.AsyncClient(timeout=self.DEFAULT_TIMEOUT) as client:
                response = await client.post(
                    api_url,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                )

                if response.status_code != 200:
                    error_detail = self._extract_error_message(response)
                    raise AIProviderError(
                        f"Ollama API returned status {response.status_code}: {error_detail}"
                    )

                response_data = response.json()

                # Extract the message content from the response
                message = response_data.get("message", {})
                if not isinstance(message, dict):
                    raise AIProviderError("Invalid response format: missing or invalid message")

                content = message.get("content")

                if content is None:
                    raise AIProviderError("No content found in response")

                return content

        except httpx.TimeoutException as e:
            raise AIProviderError(
                f"Request to Ollama API timed out after {self.DEFAULT_TIMEOUT} seconds. "
                f"This may indicate the model is not loaded or the server is slow."
            ) from e
        except httpx.ConnectError as e:
            raise AIProviderError(
                f"Could not connect to Ollama at {self._base_url}. "
                f"Please ensure Ollama is running."
            ) from e
        except httpx.NetworkError as e:
            raise AIProviderError(
                f"Network error connecting to Ollama API: {str(e)}"
            ) from e
        except httpx.HTTPError as e:
            raise AIProviderError(
                f"HTTP error during Ollama API call: {str(e)}"
            ) from e
        except AIProviderError:
            raise
        except Exception as e:
            raise AIProviderError(
                f"Unexpected error during Ollama API call: {str(e)}"
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
                    return str(error_data["error"])
            return response.text[:200]  # First 200 chars if JSON parsing fails
        except Exception:
            return response.text[:200]
