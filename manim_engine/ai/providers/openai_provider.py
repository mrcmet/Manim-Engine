"""OpenAI GPT provider implementation.

This module provides integration with OpenAI's Chat Completions API
for generating Manim animation code.
"""

import httpx
from ai.provider_base import AIProvider, AIProviderError
from core.models.ai_config import AIProviderConfig


class OpenAIProvider(AIProvider):
    """Provider for OpenAI's GPT API.

    Uses the Chat Completions API to generate responses from GPT models.
    """

    API_URL = "https://api.openai.com/v1/chat/completions"
    DEFAULT_MODEL = "gpt-4o"
    DEFAULT_MAX_TOKENS = 4096

    def __init__(self, config: AIProviderConfig):
        """Initialize the OpenAI provider.

        Args:
            config: Provider configuration with api_key and optional model_name.
        """
        super().__init__(config)

        # Use configured model or fall back to default
        if not self._config.model_name:
            self._config.model_name = self.DEFAULT_MODEL

    def validate_config(self) -> tuple[bool, str | None]:
        """Validate the OpenAI configuration.

        Returns:
            Tuple of (is_valid, error_message).
        """
        if not self._config.api_key:
            return False, "API key is required for OpenAI provider"

        if not isinstance(self._config.api_key, str) or len(self._config.api_key.strip()) == 0:
            return False, "API key must be a non-empty string"

        return True, None

    async def generate(
        self,
        messages: list[dict],
        system_prompt: str | None = None
    ) -> str:
        """Generate a response using GPT.

        Args:
            messages: List of message dicts with 'role' and 'content' keys.
            system_prompt: Optional system prompt (added as first message with role='system').

        Returns:
            The generated text response.

        Raises:
            AIProviderError: If the API call fails or returns an error.
        """
        if not messages and not system_prompt:
            raise AIProviderError("Either messages or system_prompt must be provided")

        # Build the messages array for OpenAI format
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

        headers = {
            "Authorization": f"Bearer {self._config.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "messages": api_messages,
            "max_tokens": self._config.max_tokens or self.DEFAULT_MAX_TOKENS,
        }

        # Add temperature if configured
        if hasattr(self._config, 'temperature') and self._config.temperature is not None:
            payload["temperature"] = self._config.temperature

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
                        f"OpenAI API returned status {response.status_code}: {error_detail}"
                    )

                response_data = response.json()

                # Extract the message content from the response
                choices = response_data.get("choices", [])
                if not choices or not isinstance(choices, list):
                    raise AIProviderError("Invalid response format: missing choices")

                first_choice = choices[0]
                if not isinstance(first_choice, dict):
                    raise AIProviderError("Invalid response format: invalid choice structure")

                message = first_choice.get("message", {})
                content = message.get("content")

                if content is None:
                    raise AIProviderError("No content found in response")

                return content

        except httpx.TimeoutException as e:
            raise AIProviderError(
                f"Request to OpenAI API timed out after 60 seconds"
            ) from e
        except httpx.NetworkError as e:
            raise AIProviderError(
                f"Network error connecting to OpenAI API: {str(e)}"
            ) from e
        except httpx.HTTPError as e:
            raise AIProviderError(
                f"HTTP error during OpenAI API call: {str(e)}"
            ) from e
        except AIProviderError:
            raise
        except Exception as e:
            raise AIProviderError(
                f"Unexpected error during OpenAI API call: {str(e)}"
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
