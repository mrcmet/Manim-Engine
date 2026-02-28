from dataclasses import dataclass
from core.services.project_service import ProjectService
from core.services.version_service import VersionService
from core.services.settings_service import SettingsService
from core.services.snippets_service import SnippetsService
from ai.ai_service import AIService


@dataclass
class ServiceContainer:
    project_service: ProjectService
    version_service: VersionService
    settings_service: SettingsService
    snippets_service: SnippetsService
    ai_service: AIService
