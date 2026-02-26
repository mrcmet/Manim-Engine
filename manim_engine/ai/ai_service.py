from PySide6.QtCore import QObject
from ai.provider_registry import ProviderRegistry
from ai.provider_base import AIProvider, AIProviderError
from ai.prompt_builder import PromptBuilder
from ai.response_parser import ResponseParser
from ai.ai_worker import AIWorker
from app.signals import SignalBus


class AIService(QObject):
    def __init__(self, registry: ProviderRegistry, signal_bus: SignalBus):
        super().__init__()
        self._registry = registry
        self._bus = signal_bus
        self._prompt_builder = PromptBuilder()
        self._response_parser = ResponseParser()
        self._active_provider_name: str | None = None
        self._worker: AIWorker | None = None

    def set_active_provider(self, name: str) -> None:
        self._active_provider_name = name

    def generate_code(
        self,
        prompt: str,
        current_code: str | None = None,
        selected_code: str | None = None,
        custom_context: str | None = None,
    ) -> None:
        if self._active_provider_name is None:
            self._bus.ai_generation_failed.emit("No AI provider selected")
            return

        provider = self._registry.get_provider(self._active_provider_name)
        if provider is None:
            self._bus.ai_generation_failed.emit(
                f"Provider '{self._active_provider_name}' is not configured. "
                "Check Settings → AI Providers."
            )
            return

        if self._worker and self._worker.isRunning():
            self._worker.cancel()
            self._worker.wait()

        from ai.prompt_builder import SYSTEM_PROMPT
        if custom_context and custom_context.strip():
            effective = SYSTEM_PROMPT + "\n\n## Additional Instructions\n" + custom_context.strip()
            self._prompt_builder.set_system_prompt(effective)
        else:
            self._prompt_builder.set_system_prompt(SYSTEM_PROMPT)

        messages = self._prompt_builder.build(prompt, current_code, selected_code)
        system_prompt = self._prompt_builder.get_system_prompt()

        self._bus.ai_generation_started.emit()
        self._worker = AIWorker(provider, messages, system_prompt, self._response_parser)
        self._worker.finished.connect(self._on_generation_finished)
        self._worker.failed.connect(self._on_generation_failed)
        self._worker.start()

    def _on_generation_finished(self, code: str):
        self._bus.ai_generation_finished.emit(code)

    def _on_generation_failed(self, error: str):
        self._bus.ai_generation_failed.emit(error)

    def reload_provider(self, name: str, config) -> None:
        """Recreate a provider instance from updated config (e.g. after settings change)."""
        try:
            self._registry.create_provider(name, config)
        except Exception:
            pass  # Provider may lack API key — silently skip

    def get_available_providers(self) -> list[str]:
        return self._registry.list_providers()
