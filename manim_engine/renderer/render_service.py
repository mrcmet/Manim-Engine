from pathlib import Path
import tempfile

from PySide6.QtCore import QObject

from app.signals import SignalBus
from core.services.code_validator import CodeValidator
from renderer.render_config import RenderConfig
from renderer.render_result import RenderResult
from renderer.render_worker import RenderWorker
from renderer.scene_file_manager import SceneFileManager


class RenderService(QObject):
    def __init__(self, signal_bus: SignalBus):
        super().__init__()
        self._bus = signal_bus
        self._file_manager = SceneFileManager()
        self._worker: RenderWorker | None = None
        self._media_dir = Path(tempfile.mkdtemp(prefix="manim_media_"))
        self._config = RenderConfig()
        self._last_output: Path | None = None

    def render(self, code: str, scene_name: str | None = None,
               config: RenderConfig | None = None) -> None:
        if self._worker and self._worker.isRunning():
            self._worker.cancel()
            self._worker.wait()

        cfg = config or self._config

        if scene_name is None:
            found, name = CodeValidator.has_scene_class(code)
            scene_name = name if found else "GeneratedScene"

        scene_file = self._file_manager.write_scene_file(code, scene_name)

        self._bus.render_started.emit()
        self._worker = RenderWorker(scene_file, scene_name, self._media_dir, cfg)
        self._worker.finished.connect(
            lambda result: self._on_render_finished(result, scene_file, scene_name, cfg)
        )
        self._worker.progress.connect(lambda p: self._bus.render_progress.emit(p))
        self._worker.start()

    def _on_render_finished(self, result: RenderResult, scene_file: Path,
                            scene_name: str, config: RenderConfig):
        if result.success:
            video_path = self._file_manager.find_output_video(
                scene_file, scene_name, config.quality, self._media_dir
            )
            if video_path and video_path.exists():
                self._last_output = video_path
                self._bus.render_finished.emit(str(video_path))
            else:
                self._bus.render_failed.emit(
                    "Render completed but output video not found"
                )
        else:
            self._bus.render_failed.emit(result.error_message or "Unknown render error")

    def cancel_render(self):
        if self._worker and self._worker.isRunning():
            self._worker.cancel()

    def get_last_output_path(self) -> Path | None:
        return self._last_output

    def set_config(self, config: RenderConfig):
        self._config = config

    def cleanup(self):
        if self._worker and self._worker.isRunning():
            self._worker.cancel()
            self._worker.wait()
        self._file_manager.cleanup()
