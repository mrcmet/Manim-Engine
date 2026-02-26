"""Render result data structure for Manim Engine."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from renderer.error_parser import ParsedError


@dataclass
class RenderResult:
    """Result of a Manim render operation.

    Attributes:
        success: Whether the render completed successfully
        video_path: Path to the output video file if successful
        duration: Render duration in seconds
        error_message: Error description if render failed
        stdout: Standard output from Manim process
        stderr: Standard error from Manim process
        parsed_error: Structured error info (only populated on failure)
    """
    success: bool
    video_path: Path | None
    duration: float | None
    error_message: str | None
    stdout: str
    stderr: str
    parsed_error: "ParsedError | None" = field(default=None)
