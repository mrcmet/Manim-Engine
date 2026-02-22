# Agent 3: Manim Render Engine

## Scope
Build the subprocess-based Manim rendering pipeline, temp file management, QThread render worker, and render configuration.

## Files to Create

```
manim_engine/
└── renderer/
    ├── __init__.py
    ├── render_service.py
    ├── render_worker.py
    ├── render_config.py
    ├── scene_file_manager.py
    └── render_result.py
└── tests/
    └── test_renderer/
        ├── __init__.py
        ├── test_render_service.py
        └── test_scene_file_manager.py
```

---

## Detailed Specifications

### `render_config.py`

```python
from dataclasses import dataclass
from pathlib import Path

@dataclass
class RenderConfig:
    quality: str = "l"            # "l" (480p), "m" (720p), "h" (1080p), "k" (4K)
    format: str = "mp4"           # "mp4", "gif", "webm"
    timeout: int = 30             # seconds
    output_dir: Path | None = None  # if None, use temp dir
    disable_caching: bool = True  # avoid stale renders
    fps: int = 30

    @property
    def quality_flag(self) -> str:
        """Returns the -q flag value for manim CLI."""
        return self.quality
```

### `render_result.py`

```python
@dataclass
class RenderResult:
    success: bool
    video_path: Path | None       # path to output video
    duration: float | None        # render time in seconds
    error_message: str | None
    stdout: str
    stderr: str
```

### `scene_file_manager.py`

Manages writing code to temp files and locating Manim's output.

```python
import tempfile
from pathlib import Path

class SceneFileManager:
    def __init__(self):
        self._temp_dir = Path(tempfile.mkdtemp(prefix="manim_engine_"))

    def write_scene_file(self, code: str, scene_name: str) -> Path:
        """Write code to a .py file in temp directory.
        Returns the file path.
        File is named after the scene for Manim's output structure."""
        file_path = self._temp_dir / f"{scene_name.lower()}_scene.py"
        file_path.write_text(code, encoding="utf-8")
        return file_path

    def find_output_video(self, scene_file: Path, scene_name: str,
                          quality: str, media_dir: Path) -> Path | None:
        """Locate Manim's output video.
        Manim outputs to: media_dir/videos/<filename_no_ext>/<quality_dir>/<SceneName>.mp4
        Quality dirs: 480p15 (l), 720p30 (m), 1080p60 (h), 2160p60 (k)"""
        quality_map = {
            "l": "480p15",
            "m": "720p30",
            "h": "1080p60",
            "k": "2160p60",
        }
        stem = scene_file.stem  # e.g., "generatedscene_scene"
        q_dir = quality_map.get(quality, "480p15")
        expected = media_dir / "videos" / stem / q_dir / f"{scene_name}.mp4"
        if expected.exists():
            return expected
        # Fallback: glob for any video in the output directory
        search_dir = media_dir / "videos" / stem
        if search_dir.exists():
            for mp4 in search_dir.rglob("*.mp4"):
                return mp4
        return None

    def copy_to_project(self, source: Path, dest_dir: Path) -> Path:
        """Copy rendered video to project version directory."""
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / source.name
        shutil.copy2(source, dest)
        return dest

    def cleanup(self):
        """Remove temp directory."""
        shutil.rmtree(self._temp_dir, ignore_errors=True)
```

### `render_worker.py` — QThread Worker

```python
import sys
import subprocess
import time
from PySide6.QtCore import QThread, Signal
from pathlib import Path

class RenderWorker(QThread):
    """Runs manim render in a subprocess on a background thread."""

    finished = Signal(object)    # RenderResult
    progress = Signal(int)       # percentage (approximate)

    def __init__(self, scene_file: Path, scene_name: str,
                 config: RenderConfig, media_dir: Path):
        super().__init__()
        self._scene_file = scene_file
        self._scene_name = scene_name
        self._config = config
        self._media_dir = media_dir
        self._process: subprocess.Popen | None = None
        self._cancelled = False

    def run(self):
        start_time = time.time()
        cmd = [
            sys.executable, "-m", "manim", "render",
            str(self._scene_file),
            self._scene_name,
            f"-q{self._config.quality_flag}",
            "--format", self._config.format,
            "--media_dir", str(self._media_dir),
        ]
        if self._config.disable_caching:
            cmd.append("--disable_caching")

        try:
            self._process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            stdout, stderr = self._process.communicate(
                timeout=self._config.timeout
            )
            elapsed = time.time() - start_time

            if self._cancelled:
                self.finished.emit(RenderResult(
                    success=False, video_path=None, duration=elapsed,
                    error_message="Render cancelled", stdout=stdout, stderr=stderr
                ))
                return

            if self._process.returncode != 0:
                self.finished.emit(RenderResult(
                    success=False, video_path=None, duration=elapsed,
                    error_message=f"Manim exited with code {self._process.returncode}\n{stderr}",
                    stdout=stdout, stderr=stderr
                ))
                return

            # Find output video
            file_mgr = SceneFileManager()
            video_path = file_mgr.find_output_video(
                self._scene_file, self._scene_name,
                self._config.quality, self._media_dir
            )

            self.finished.emit(RenderResult(
                success=True, video_path=video_path, duration=elapsed,
                error_message=None, stdout=stdout, stderr=stderr
            ))

        except subprocess.TimeoutExpired:
            if self._process:
                self._process.kill()
            self.finished.emit(RenderResult(
                success=False, video_path=None,
                duration=self._config.timeout,
                error_message=f"Render timed out after {self._config.timeout}s",
                stdout="", stderr=""
            ))
        except Exception as e:
            self.finished.emit(RenderResult(
                success=False, video_path=None,
                duration=time.time() - start_time,
                error_message=str(e), stdout="", stderr=""
            ))

    def cancel(self):
        self._cancelled = True
        if self._process:
            self._process.terminate()
```

### `render_service.py` — Orchestrator

```python
from PySide6.QtCore import QObject
from pathlib import Path
import tempfile

class RenderService(QObject):
    """Orchestrates the rendering pipeline."""

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
        """Start an async render. Results emitted via signal bus.

        If scene_name is None, auto-detect from code using CodeValidator.
        """
        if self._worker and self._worker.isRunning():
            self._worker.cancel()
            self._worker.wait()

        cfg = config or self._config

        # Auto-detect scene name
        if scene_name is None:
            from core.services.code_validator import CodeValidator
            found, name = CodeValidator.has_scene_class(code)
            scene_name = name if found else "GeneratedScene"

        # Write temp file
        scene_file = self._file_manager.write_scene_file(code, scene_name)

        # Start worker
        self._bus.render_started.emit()
        self._worker = RenderWorker(scene_file, scene_name, cfg, self._media_dir)
        self._worker.finished.connect(self._on_render_finished)
        self._worker.progress.connect(lambda p: self._bus.render_progress.emit(p))
        self._worker.start()

    def _on_render_finished(self, result: RenderResult):
        if result.success and result.video_path:
            self._last_output = result.video_path
            self._bus.render_finished.emit(str(result.video_path))
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
        """Call on app shutdown."""
        self._file_manager.cleanup()
```

---

## Tests

**`test_scene_file_manager.py`**:
- Test write_scene_file creates file with correct content
- Test find_output_video locates video in Manim output structure (create mock dir structure)
- Test copy_to_project copies file correctly

**`test_render_service.py`**:
- Test render with mock subprocess (patch subprocess.Popen)
- Test cancel_render terminates process
- Test timeout handling
- Test scene name auto-detection

## Verification

```bash
python -m pytest tests/test_renderer/ -v

# Integration test (requires manim installed):
python -c "
from renderer.render_service import RenderService
from app.signals import get_signal_bus
bus = get_signal_bus()
bus.render_finished.connect(lambda p: print(f'Video at: {p}'))
bus.render_failed.connect(lambda e: print(f'Error: {e}'))
rs = RenderService(bus)
code = '''from manim import *
class TestScene(Scene):
    def construct(self):
        circle = Circle()
        self.play(Create(circle))
        self.wait(1)
'''
rs.render(code)
# Wait for worker thread to complete
import time; time.sleep(15)
"
```

## Dependencies on Other Agents
- Agent 1: `app.signals.get_signal_bus`, `core.services.code_validator.CodeValidator`

## What Other Agents Need From You
- Agent 7: `RenderService` with `render()`, `cancel_render()`, `set_config()`, `cleanup()`
