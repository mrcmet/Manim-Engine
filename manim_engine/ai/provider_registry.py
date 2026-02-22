"""Registry for managing AI provider instances.

This module provides a centralized registry for creating, storing,
and retrieving AI provider instances.
"""

from typing import Type, Dict, Optional
from ai.provider_base import AIProvider, AIProviderError
from core.models.ai_config import AIProviderConfig


class ProviderRegistry:
    """Registry for AI provider factories and instances.

    This class maintains a registry of provider classes and manages
    provider instances. It uses a factory pattern to create providers
    from configuration objects.
    """

    def __init__(self):
        """Initialize an empty provider registry."""
        self._provider_classes: Dict[str, Type[AIProvider]] = {}
        self._provider_instances: Dict[str, AIProvider] = {}

    def register(self, provider_name: str, provider_class: Type[AIProvider]) -> None:
        """Register a provider class.

        Args:
            provider_name: Unique name for the provider (e.g., 'anthropic', 'openai').
            provider_class: The provider class to register.

        Raises:
            ValueError: If provider_name is empty or provider_class is not valid.
        """
        if not provider_name or not isinstance(provider_name, str):
            raise ValueError("Provider name must be a non-empty string")

        if not isinstance(provider_class, type) or not issubclass(provider_class, AIProvider):
            raise ValueError(
                f"Provider class must be a subclass of AIProvider, got {provider_class}"
            )

        if provider_name in self._provider_classes:
            # Allow re-registration for flexibility, but could log a warning
            pass

        self._provider_classes[provider_name] = provider_class

    def create_provider(self, name_or_config, config: AIProviderConfig | None = None) -> AIProvider:
        """Create a provider instance from configuration.

        Can be called as:
            create_provider(config)
            create_provider(name, config)

        Args:
            name_or_config: Either a provider name string or an AIProviderConfig.
            config: Provider configuration (when first arg is name).

        Returns:
            A new provider instance.

        Raises:
            AIProviderError: If the provider is not registered or creation fails.
        """
        if config is not None:
            # Called as create_provider(name, config)
            config = config
        elif isinstance(name_or_config, AIProviderConfig):
            config = name_or_config
        else:
            raise AIProviderError("Provider configuration cannot be None")

        provider_name = config.provider_name

        if provider_name not in self._provider_classes:
            available = ", ".join(self._provider_classes.keys())
            raise AIProviderError(
                f"Provider '{provider_name}' is not registered. "
                f"Available providers: {available or 'none'}"
            )

        try:
            provider_class = self._provider_classes[provider_name]
            provider = provider_class(config)

            # Validate the provider configuration
            is_valid, error_msg = provider.validate_config()
            if not is_valid:
                raise AIProviderError(
                    f"Invalid configuration for provider '{provider_name}': {error_msg}"
                )

            # Store the instance for later retrieval
            self._provider_instances[provider_name] = provider

            return provider

        except AIProviderError:
            raise
        except Exception as e:
            raise AIProviderError(
                f"Failed to create provider '{provider_name}': {str(e)}"
            ) from e

    def get_provider(self, provider_name: str) -> Optional[AIProvider]:
        """Get a cached provider instance by name.

        Args:
            provider_name: The name of the provider to retrieve.

        Returns:
            The provider instance if found, None otherwise.
        """
        return self._provider_instances.get(provider_name)

    def list_providers(self) -> list[str]:
        """List all registered provider names.

        Returns:
            A sorted list of registered provider names.
        """
        return sorted(self._provider_classes.keys())

    def has_provider(self, provider_name: str) -> bool:
        """Check if a provider is registered.

        Args:
            provider_name: The name of the provider to check.

        Returns:
            True if the provider is registered, False otherwise.
        """
        return provider_name in self._provider_classes

    def clear_instances(self) -> None:
        """Clear all cached provider instances.

        This is useful when configuration changes and providers
        need to be recreated.
        """
        self._provider_instances.clear()
