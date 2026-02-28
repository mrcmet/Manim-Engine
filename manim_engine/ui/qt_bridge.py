from __future__ import annotations
from pathlib import Path
from PySide6.QtCore import QObject, Signal
from app.controller import AppController
from app.event_bus import EventBus
from app.events import (
    RenderStarted, RenderFinished, RenderImageFinished, RenderFailed,
    AIStarted, AIFinished, AIFailed, CodeChanged, ProjectOpened,
    VersionCreated, ThemeChanged,
)
from app.signals import SignalBus


class QtBridge(QObject):
    """Bridges pure-Python EventBus events into Qt signals for the UI."""

    # Qt signals consumed by MainWindow
    render_started = Signal()
    render_finished = Signal(str)                    # video_path
    render_image_finished = Signal(str)              # image_path
    render_failed = Signal(str)                      # error message
    render_failed_detail = Signal(object, str, str)  # parsed_error, stdout, stderr
    ai_started = Signal()
    ai_finished = Signal(str)                        # code
    ai_failed = Signal(str)                          # error
    code_changed_external = Signal(str)              # code (from version load)
    project_opened = Signal(str, str)                # project_id, project_name
    version_created = Signal(str)                    # version_id
    settings_changed = Signal()
    theme_changed = Signal(dict)

    def __init__(
        self,
        controller: AppController,
        event_bus: EventBus,
        signal_bus: SignalBus,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._controller = controller
        self._bus = event_bus
        self._signal_bus = signal_bus

        # Bridge SignalBus (Qt) → AppController callbacks
        signal_bus.render_finished.connect(
            lambda p: controller.on_render_finished(Path(p))
        )
        signal_bus.render_image_finished.connect(
            lambda p: controller.on_render_image_finished(Path(p))
        )
        signal_bus.render_failed.connect(controller.on_render_failed)
        signal_bus.render_failed_detail.connect(
            lambda pe, out, err: controller.on_render_failed(
                pe.summary if pe else err, pe, out, err
            )
        )
        signal_bus.render_started.connect(controller.on_render_started)
        signal_bus.ai_generation_finished.connect(controller.on_ai_finished)
        signal_bus.ai_generation_failed.connect(controller.on_ai_failed)
        signal_bus.ai_generation_started.connect(controller.on_ai_started)

        # Bridge EventBus (pure Python) → Qt signals (for MainWindow)
        event_bus.subscribe(RenderStarted, lambda _: self.render_started.emit())
        event_bus.subscribe(
            RenderFinished,
            lambda e: self.render_finished.emit(str(e.video_path))
        )
        event_bus.subscribe(
            RenderImageFinished,
            lambda e: self.render_image_finished.emit(str(e.image_path))
        )
        event_bus.subscribe(RenderFailed, self._on_render_failed_event)
        event_bus.subscribe(AIStarted, lambda _: self.ai_started.emit())
        event_bus.subscribe(AIFinished, lambda e: self.ai_finished.emit(e.code))
        event_bus.subscribe(AIFailed, lambda e: self.ai_failed.emit(e.error))
        event_bus.subscribe(
            CodeChanged,
            lambda e: self.code_changed_external.emit(e.code)
        )
        event_bus.subscribe(
            ProjectOpened,
            lambda e: self.project_opened.emit(e.project_id, e.project_name)
        )
        event_bus.subscribe(
            VersionCreated,
            lambda e: self.version_created.emit(e.version_id)
        )
        event_bus.subscribe(
            ThemeChanged,
            lambda e: self.theme_changed.emit(e.theme)
        )

    def _on_render_failed_event(self, e: RenderFailed) -> None:
        self.render_failed.emit(e.error)
        if e.parsed_error is not None:
            self.render_failed_detail.emit(e.parsed_error, e.stdout, e.stderr)
