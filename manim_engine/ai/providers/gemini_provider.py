"""Google Gemini AI provider implementation.

This module provides integration with Google's Gemini API
for generating Manim animation code.
"""

import httpx
from ai.provider_base import AIProvider, AIProviderError
from core.models.ai_config import AIProviderConfig


class GeminiProvider(AIProvider):
    """Provider for Google's Gemini API.

    Uses the generateContent endpoint to generate responses from Gemini models.
    """

    API_URL_TEMPLATE = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    DEFAULT_MODEL = "gemini-2.0-flash"

    def __init__(self, config: AIProviderConfig):
        """Initialize the Gemini provider.

        Args:
            config: Provider configuration with api_key and optional model_name.
        """
        super().__init__(config)

        # Use configured model or fall back to default
        if not self._config.model_name:
            self._config.model_name = self.DEFAULT_MODEL

    def validate_config(self) -> tuple[bool, str | None]:
        """Validate the Gemini configuration.

        Returns:
            Tuple of (is_valid, error_message).
        """
        if not self._config.api_key:
            return False, "API key is required for Gemini provider"

        if not isinstance(self._config.api_key, str) or len(self._config.api_key.strip()) == 0:
            return False, "API key must be a non-empty string"

        return True, None

    async def generate(
        self,
        messages: list[dict],
        system_prompt: str | None = None
    ) -> str:
        """Generate a response using Gemini.

        Args:
            messages: List of message dicts with 'role' and 'content' keys.
            system_prompt: Optional system prompt (prepended to first user message).

        Returns:
            The generated text response.

        Raises:
            AIProviderError: If the API call fails or returns an error.
        """
        if not messages:
            raise AIProviderError("Messages list cannot be empty")

        # Convert messages to Gemini format
        contents = self._convert_messages_to_gemini_format(messages, system_prompt)

        # Build the API URL with the model name
        api_url = self.API_URL_TEMPLATE.format(model=self.model)

        # API key is passed as a query parameter
        params = {
            "key": self._config.api_key
        }

        payload = {
            "contents": contents,
        }

        # Add generation config if max_tokens is specified
        if self._config.max_tokens:
            payload["generationConfig"] = {
                "maxOutputTokens": self._config.max_tokens
            }

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    api_url,
                    params=params,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                )

                if response.status_code != 200:
                    error_detail = self._extract_error_message(response)
                    raise AIProviderError(
                        f"Gemini API returned status {response.status_code}: {error_detail}"
                    )

                response_data = response.json()

                # Extract the text content from the response
                candidates = response_data.get("candidates", [])
                if not candidates or not isinstance(candidates, list):
                    raise AIProviderError("Invalid response format: missing candidates")

                first_candidate = candidates[0]
                if not isinstance(first_candidate, dict):
                    raise AIProviderError("Invalid response format: invalid candidate structure")

                content = first_candidate.get("content", {})
                parts = content.get("parts", [])

                if not parts:
                    raise AIProviderError("No content parts found in response")

                # Concatenate all text parts
                text_parts = []
                for part in parts:
                    if isinstance(part, dict) and "text" in part:
                        text_parts.append(part["text"])

                if not text_parts:
                    raise AIProviderError("No text content found in response")

                return "".join(text_parts)

        except httpx.TimeoutException as e:
            raise AIProviderError(
                f"Request to Gemini API timed out after 60 seconds"
            ) from e
        except httpx.NetworkError as e:
            raise AIProviderError(
                f"Network error connecting to Gemini API: {str(e)}"
            ) from e
        except httpx.HTTPError as e:
            raise AIProviderError(
                f"HTTP error during Gemini API call: {str(e)}"
            ) from e
        except AIProviderError:
            raise
        except Exception as e:
            raise AIProviderError(
                f"Unexpected error during Gemini API call: {str(e)}"
            ) from e

    def _convert_messages_to_gemini_format(
        self,
        messages: list[dict],
        system_prompt: str | None
    ) -> list[dict]:
        """Convert standard message format to Gemini's format.

        Gemini uses a different message format with 'role' (user/model)
        and 'parts' array containing text content.

        Args:
            messages: Standard format messages.
            system_prompt: Optional system prompt.

        Returns:
            List of Gemini-formatted content objects.
        """
        contents = []

        for idx, msg in enumerate(messages):
            if not isinstance(msg, dict):
                raise AIProviderError(f"Message at index {idx} must be a dict")
            if 'role' not in msg or 'content' not in msg:
                raise AIProviderError(
                    f"Message at index {idx} must have 'role' and 'content' keys"
                )

            # Map role to Gemini's role system (user/model)
            role = msg['role']
            if role == 'assistant':
                role = 'model'
            elif role == 'system':
                # Gemini doesn't have a system role, prepend to next user message
                continue

            content_text = msg['content']

            # If this is the first user message and we have a system prompt, prepend it
            if role == 'user' and system_prompt and idx == 0:
                content_text = f"{system_prompt}\n\n{content_text}"

            contents.append({
                "role": role,
                "parts": [{"text": content_text}]
            })

        return contents

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
