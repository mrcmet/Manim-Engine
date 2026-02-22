"""Render configuration for Manim Engine."""

from dataclasses import dataclass
from pathlib import Path


@dataclass
class RenderConfig:
    """Configuration settings for Manim rendering.

    Attributes:
        quality: Quality preset - "l" (480p), "m" (720p), "h" (1080p), "k" (4K)
        format: Output format (mp4, mov, gif, etc.)
        timeout: Maximum render time in seconds
        output_dir: Optional custom output directory
        disable_caching: Whether to disable Manim's caching
        fps: Frames per second
    """
    quality: str = "l"
    format: str = "mp4"
    timeout: int = 30
    output_dir: Path | None = None
    disable_caching: bool = True
    fps: int = 30

    @property
    def quality_flag(self) -> str:
        """Returns the quality flag for Manim CLI."""
        return self.quality
