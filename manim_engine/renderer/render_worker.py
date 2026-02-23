"""Background worker thread for Manim rendering."""

import os
import subprocess
import sys
import time
from pathlib import Path

from PySide6.QtCore import QThread, Signal

from renderer.render_config import RenderConfig
from renderer.render_result import RenderResult


class RenderWorker(QThread):
    """QThread worker for executing Manim render subprocess.

    Runs Manim render command in a separate thread to avoid blocking
    the UI. Emits signals for progress updates and completion.
    """

    finished = Signal(RenderResult)
    progress = Signal(int)

    def __init__(
        self,
        scene_file: Path,
        scene_name: str,
        media_dir: Path,
        config: RenderConfig,
    ) -> None:
        """Initialize render worker.

        Args:
            scene_file: Path to temporary scene file
            scene_name: Name of scene class to render
            media_dir: Directory for Manim output
            config: Render configuration
        """
        super().__init__()
        self.scene_file = scene_file
        self.scene_name = scene_name
        self.media_dir = media_dir
        self.config = config
        self._cancelled = False
        self._process: subprocess.Popen | None = None

    def cancel(self) -> None:
        """Request cancellation of the render operation."""
        self._cancelled = True
        if self._process and self._process.poll() is None:
            self._process.terminate()
            try:
                self._process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self._process.kill()

    def run(self) -> None:
        """Execute the Manim render process.

        Builds the Manim CLI command, runs it as a subprocess,
        monitors for timeout and cancellation, and emits the result.
        """
        start_time = time.time()

        # Build Manim command
        command = [
            sys.executable,
            "-m",
            "manim",
            "render",
            str(self.scene_file),
            self.scene_name,
            f"-q{self.config.quality_flag}",
            "--format",
            self.config.format,
            "--media_dir",
            str(self.media_dir),
        ]

        if self.config.disable_caching:
            command.append("--disable_caching")

        # Build environment — ensure TeX tools are on PATH regardless of how
        # the app was launched (macOS GUI apps don't source /etc/paths.d/).
        env = os.environ.copy()
        tex_bin = "/Library/TeX/texbin"
        if tex_bin not in env.get("PATH", ""):
            env["PATH"] = tex_bin + os.pathsep + env.get("PATH", "")

        # Execute subprocess
        try:
            self._process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env,
            )

            # Wait for completion with timeout
            try:
                stdout, stderr = self._process.communicate(timeout=self.config.timeout)
                returncode = self._process.returncode
            except subprocess.TimeoutExpired:
                self._process.kill()
                stdout, stderr = self._process.communicate()
                duration = time.time() - start_time

                result = RenderResult(
                    success=False,
                    video_path=None,
                    duration=duration,
                    error_message=f"Render timed out after {self.config.timeout} seconds",
                    stdout=stdout or "",
                    stderr=stderr or "",
                )
                self.finished.emit(result)
                return

            # Check for cancellation
            if self._cancelled:
                result = RenderResult(
                    success=False,
                    video_path=None,
                    duration=time.time() - start_time,
                    error_message="Render cancelled by user",
                    stdout=stdout or "",
                    stderr=stderr or "",
                )
                self.finished.emit(result)
                return

            # Check return code
            duration = time.time() - start_time

            if returncode != 0:
                result = RenderResult(
                    success=False,
                    video_path=None,
                    duration=duration,
                    error_message=f"Manim render failed with code {returncode}",
                    stdout=stdout or "",
                    stderr=stderr or "",
                )
            else:
                result = RenderResult(
                    success=True,
                    video_path=None,  # Will be set by RenderService
                    duration=duration,
                    error_message=None,
                    stdout=stdout or "",
                    stderr=stderr or "",
                )

            self.finished.emit(result)

        except Exception as e:
            duration = time.time() - start_time
            result = RenderResult(
                success=False,
                video_path=None,
                duration=duration,
                error_message=f"Render exception: {str(e)}",
                stdout="",
                stderr=str(e),
            )
            self.finished.emit(result)
