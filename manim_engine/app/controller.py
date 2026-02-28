from __future__ import annotations
from pathlib import Path
from typing import Protocol
from app.event_bus import EventBus
from app.events import (
    RenderStarted, RenderFinished, RenderImageFinished, RenderFailed,
    AIStarted, AIFinished, AIFailed, CodeChanged, ProjectOpened,
    VersionCreated,
)
from app.service_container import ServiceContainer
from core.services.code_validator import CodeValidator
from renderer.render_config import RenderConfig


class IRenderService(Protocol):
    """Interface so AppController never imports Qt-bound RenderService."""
    def render(self, code: str, config: RenderConfig | None = None) -> None: ...
    def cancel_render(self) -> None: ...
    def cleanup(self) -> None: ...


class AppController:
    def __init__(
        self,
        services: ServiceContainer,
        event_bus: EventBus,
        render_service: IRenderService,
    ) -> None:
        self._svc = services
        self._bus = event_bus
        self._render = render_service

        # App state (pure Python, no Qt)
        self._current_project = None
        self._current_version_id: str | None = None
        self._last_version_code: str = ""
        self._snippet_used_since_last_version: bool = False

    # ── Queries ────────────────────────────────────────

    def get_projects(self):
        return self._svc.project_service.list_projects()

    def get_versions(self, project_id: str):
        return self._svc.version_service.list_versions(project_id)

    def get_version(self, project_id: str, version_id: str):
        return self._svc.version_service.get_version(project_id, version_id)

    def get_settings(self):
        return self._svc.settings_service.load()

    def get_snippets(self):
        return self._svc.snippets_service.load()

    def get_active_project(self):
        return self._current_project

    def get_active_providers(self):
        return self._svc.ai_service.get_available_providers()

    def get_settings_service(self):
        return self._svc.settings_service

    def get_current_version_id(self) -> str | None:
        return self._current_version_id

    # ── Commands ───────────────────────────────────────

    def open_project(self, project_id: str) -> None:
        project = self._svc.project_service.open_project(project_id)
        self._current_project = project
        self._svc.settings_service.set("last_project_id", project_id)
        self._bus.emit(ProjectOpened(project_id=project.id, project_name=project.name))

    def create_project(self, name: str, description: str = "") -> None:
        project = self._svc.project_service.create_project(name, description)
        self.open_project(project.id)

    def run_code(self, code: str, source: str = "manual_edit",
                 config: RenderConfig | None = None) -> None:
        if not code.strip():
            return
        valid, _ = CodeValidator.validate_syntax(code)
        if not valid:
            return
        if self._current_project and code.strip() != self._last_version_code.strip():
            effective_source = "snippet" if self._snippet_used_since_last_version else source
            version = self._svc.version_service.create_version(
                self._current_project.id, code,
                source=effective_source,
                parent_version_id=self._current_version_id,
            )
            self._current_version_id = version.id
            self._last_version_code = code
            self._snippet_used_since_last_version = False
            self._bus.emit(VersionCreated(version_id=version.id))
        self._render.render(code, config)

    def cancel_render(self) -> None:
        self._render.cancel_render()

    def submit_prompt(self, prompt: str, current_code: str | None,
                      selected_code: str | None, custom_context: str | None,
                      provider: str | None = None) -> None:
        if provider:
            self._svc.ai_service.set_active_provider(provider)
        self._svc.ai_service.generate_code(prompt, current_code, selected_code, custom_context)

    def load_version(self, version_id: str) -> None:
        if not self._current_project:
            return
        version = self._svc.version_service.get_version(
            self._current_project.id, version_id
        )
        self._current_version_id = version.id
        self._last_version_code = version.code
        self._snippet_used_since_last_version = False
        self._bus.emit(CodeChanged(code=version.code))

    def mark_snippet_used(self) -> None:
        self._snippet_used_since_last_version = True

    def save_window_state(self, geometry: bytes, state: bytes) -> None:
        settings = self._svc.settings_service.load()
        settings.window_geometry = geometry
        settings.window_state = state
        self._svc.settings_service.save(settings)

    def reload_ai_provider(self, name: str, config) -> None:
        self._svc.ai_service.reload_provider(name, config)

    def cleanup(self) -> None:
        self._render.cleanup()

    # ── Render result callbacks (called by QtBridge from Qt thread) ────

    def on_render_finished(self, video_path: Path) -> None:
        if self._current_project and self._current_version_id:
            self._svc.version_service.set_video_path(
                self._current_project.id, self._current_version_id, video_path
            )
        self._bus.emit(RenderFinished(video_path=video_path))

    def on_render_image_finished(self, image_path: Path) -> None:
        if self._current_project and self._current_version_id:
            self._svc.version_service.set_video_path(
                self._current_project.id, self._current_version_id, image_path
            )
        self._bus.emit(RenderImageFinished(image_path=image_path))

    def on_render_failed(self, error: str, parsed_error=None,
                         stdout: str = "", stderr: str = "") -> None:
        self._bus.emit(RenderFailed(
            error=error, parsed_error=parsed_error, stdout=stdout, stderr=stderr
        ))

    def on_render_started(self) -> None:
        self._bus.emit(RenderStarted())

    # ── AI result callbacks ────────────────────────────

    def on_ai_finished(self, code: str) -> None:
        if self._current_project and code.strip() != self._last_version_code.strip():
            version = self._svc.version_service.create_version(
                self._current_project.id, code,
                source="ai", parent_version_id=self._current_version_id,
            )
            self._current_version_id = version.id
            self._last_version_code = code
            self._snippet_used_since_last_version = False
            self._bus.emit(VersionCreated(version_id=version.id))
        self._bus.emit(AIFinished(code=code))
        valid, _ = CodeValidator.validate_syntax(code)
        if valid:
            self._render.render(code)

    def on_ai_failed(self, error: str) -> None:
        self._bus.emit(AIFailed(error=error))

    def on_ai_started(self) -> None:
        self._bus.emit(AIStarted())
