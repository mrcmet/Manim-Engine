from PySide6.QtWidgets import QApplication

from app.constants import APP_NAME, ORG_NAME, DATA_DIR, PROJECTS_DIR
from app.signals import get_signal_bus
from core.services.settings_service import SettingsService
from core.services.auth_service import AuthService
from core.services.project_service import ProjectService
from core.services.version_service import VersionService


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

        # Setup AI providers
        registry = ProviderRegistry()
        registry.register("anthropic", AnthropicProvider)
        registry.register("openai", OpenAIProvider)
        registry.register("gemini", GeminiProvider)
        registry.register("ollama", OllamaProvider)

        # Initialize provider instances from settings
        settings = self._settings_service.load()
        for name, config in settings.ai_providers.items():
            registry.create_provider(name, config)

        ai_service = AIService(registry, self._signal_bus)
        render_service = RenderService(self._signal_bus)
        theme_manager = ThemeManager(self._settings_service)

        self._main_window = MainWindow(
            signal_bus=self._signal_bus,
            project_service=self._project_service,
            version_service=self._version_service,
            ai_service=ai_service,
            render_service=render_service,
            settings_service=self._settings_service,
            theme_manager=theme_manager,
        )
        self._main_window.show()
        return self.exec()
