"""Scene file management for temporary Manim files."""

import shutil
import tempfile
from pathlib import Path
from typing import Optional


class SceneFileManager:
    """Manages temporary scene files and output video location.

    Handles creation of temporary directories for Manim scene files,
    locating output videos, and cleanup of temporary resources.
    """

    # Quality mapping from config quality to Manim output directory names
    QUALITY_MAP = {
        "l": "480p15",
        "m": "720p30",
        "h": "1080p60",
        "k": "2160p60",
    }

    def __init__(self) -> None:
        """Initialize with a temporary directory."""
        self.temp_dir = Path(tempfile.mkdtemp(prefix="manim_engine_"))

    def write_scene_file(self, code: str, scene_name: str) -> Path:
        """Write scene code to a temporary Python file.

        Args:
            code: Python code containing the Manim scene
            scene_name: Name of the scene class

        Returns:
            Path to the created scene file
        """
        scene_file = self.temp_dir / f"{scene_name}.py"
        scene_file.write_text(code, encoding="utf-8")
        return scene_file

    def find_output_video(
        self,
        scene_file: Path,
        scene_name: str,
        quality: str,
        media_dir: Path,
    ) -> Optional[Path]:
        """Locate the output video file from Manim render.

        Manim outputs videos to a structured directory:
        media_dir/videos/scene_file_stem/quality/scene_name.mp4

        Args:
            scene_file: Path to the scene file that was rendered
            scene_name: Name of the scene class
            quality: Quality setting used ("l", "m", "h", "k")
            media_dir: Media directory passed to Manim

        Returns:
            Path to output video if found, None otherwise
        """
        quality_dir = self.QUALITY_MAP.get(quality, "480p15")
        scene_file_stem = scene_file.stem

        # Expected path: media_dir/videos/scene_file_stem/quality_dir/scene_name.mp4
        expected_path = (
            media_dir / "videos" / scene_file_stem / quality_dir / f"{scene_name}.mp4"
        )

        if expected_path.exists():
            return expected_path

        # Fallback: glob for any mp4 in the quality directory
        quality_path = media_dir / "videos" / scene_file_stem / quality_dir
        if quality_path.exists():
            mp4_files = list(quality_path.glob("*.mp4"))
            if mp4_files:
                return mp4_files[0]

        # Broader fallback: search entire videos dir for scene name
        videos_dir = media_dir / "videos"
        if videos_dir.exists():
            for video_file in videos_dir.rglob(f"{scene_name}.*"):
                if video_file.suffix in (".mp4", ".gif", ".webm", ".mov"):
                    return video_file

        return None

    def copy_to_project(self, source: Path, dest_dir: Path) -> Path:
        """Copy video file to project output directory.

        Args:
            source: Source video file path
            dest_dir: Destination directory

        Returns:
            Path to the copied file
        """
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest_path = dest_dir / source.name
        shutil.copy2(source, dest_path)
        return dest_path

    def cleanup(self) -> None:
        """Remove temporary directory and all contents."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir, ignore_errors=True)
