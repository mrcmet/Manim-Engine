from PySide6.QtWidgets import QApplication

from app.constants import APP_NAME, ORG_NAME, DATA_DIR, PROJECTS_DIR
from app.signals import get_signal_bus
from core.services.settings_service import SettingsService
from core.services.auth_service import AuthService
from core.services.project_service import ProjectService
from core.services.version_service import VersionService
from core.services.snippets_service import SnippetsService


class ManimEngineApp(QApplication):
    def __init__(self, argv):
        super().__init__(argv)
        self.setApplicationName(APP_NAME)
        self.setOrganizationName(ORG_NAME)
        self._ensure_data_dirs()
        self._signal_bus = get_signal_bus()
        self._settings_service = SettingsService()
        self._auth_service = AuthService(self._settings_service)
        self._project_service = ProjectService()
        self._version_service = VersionService()
        self._snippets_service = SnippetsService()

    def _ensure_data_dirs(self):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        PROJECTS_DIR.mkdir(parents=True, exist_ok=True)

    def run(self):
        if not self._auth_service.authenticate():
            return 1

        from ai.ai_service import AIService
        from ai.provider_registry import ProviderRegistry
        from ai.providers.anthropic_provider import AnthropicProvider
        from ai.providers.openai_provider import OpenAIProvider
        from ai.providers.gemini_provider import GeminiProvider
        from ai.providers.ollama_provider import OllamaProvider
        from renderer.render_service import RenderService
        from ui.theme import ThemeManager
        from ui.main_window import MainWindow
        from app.event_bus import EventBus
        from app.service_container import ServiceContainer
        from app.controller import AppController
        from ui.qt_bridge import QtBridge

        # Setup AI providers
        registry = ProviderRegistry()
        registry.register("anthropic", AnthropicProvider)
        registry.register("openai", OpenAIProvider)
        registry.register("gemini", GeminiProvider)
        registry.register("ollama", OllamaProvider)

        # Initialize provider instances from settings (skip unconfigured ones)
        settings = self._settings_service.load()

        # Pre-populate Ollama defaults on first launch
        if "ollama" not in settings.ai_providers:
            from core.models.ai_config import AIProviderConfig
            settings.ai_providers["ollama"] = AIProviderConfig(
                provider_name="ollama",
                model_name="llama3",
                base_url="http://localhost:11434",
            )
            self._settings_service.save(settings)

        for name, config in settings.ai_providers.items():
            try:
                registry.create_provider(name, config)
            except Exception:
                pass  # Provider not yet configured (e.g. missing API key)

        ai_service = AIService(registry, self._signal_bus)
        render_service = RenderService(self._signal_bus)
        theme_manager = ThemeManager(self._settings_service)

        # Architecture layers
        event_bus = EventBus()
        container = ServiceContainer(
            project_service=self._project_service,
            version_service=self._version_service,
            settings_service=self._settings_service,
            snippets_service=self._snippets_service,
            ai_service=ai_service,
        )
        controller = AppController(container, event_bus, render_service)
        bridge = QtBridge(controller, event_bus, self._signal_bus)

        self._main_window = MainWindow(
            controller=controller,
            bridge=bridge,
            signal_bus=self._signal_bus,
            theme_manager=theme_manager,
            snippets_service=self._snippets_service,
        )
        self._main_window.show()
        return self.exec()
