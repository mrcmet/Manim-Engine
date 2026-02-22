"""Abstract base class for AI providers.

This module defines the interface that all AI providers must implement,
ensuring consistent behavior across different AI services.
"""

from abc import ABC, abstractmethod
from core.models.ai_config import AIProviderConfig


class AIProviderError(Exception):
    """Exception raised when AI provider operations fail.

    This wraps provider-specific errors with additional context
    about what operation failed and why.
    """
    pass


class AIProvider(ABC):
    """Abstract base class for AI providers.

    All AI provider implementations must inherit from this class
    and implement the required abstract methods.
    """

    def __init__(self, config: AIProviderConfig):
        """Initialize the provider with configuration.

        Args:
            config: Provider configuration containing API keys,
                   model names, and other settings.
        """
        if config is None:
            raise ValueError("Provider configuration cannot be None")
        self._config = config

    @abstractmethod
    async def generate(
        self,
        messages: list[dict],
        system_prompt: str | None = None
    ) -> str:
        """Generate a response from the AI model.

        Args:
            messages: List of message dicts with 'role' and 'content' keys.
            system_prompt: Optional system prompt to guide the model's behavior.

        Returns:
            The generated text response from the model.

        Raises:
            AIProviderError: If generation fails for any reason.
        """
        pass

    @abstractmethod
    def validate_config(self) -> tuple[bool, str | None]:
        """Validate the provider configuration.

        Checks that required configuration values are present and valid
        (e.g., API keys are not empty, URLs are well-formed).

        Returns:
            A tuple of (is_valid, error_message). If valid, error_message is None.
        """
        pass

    @property
    def name(self) -> str:
        """Get the provider name."""
        return self._config.provider_name

    @property
    def model(self) -> str:
        """Get the model name."""
        return self._config.model_name
