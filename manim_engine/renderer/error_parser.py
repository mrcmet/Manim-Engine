"""Pure-Python stderr parser for Manim render errors."""
from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class ParsedError:
    """Structured representation of a Manim render error."""
    error_type: str | None        # e.g. "NameError"
    message: str | None           # e.g. "name 'Circl' is not defined"
    line_number: int | None       # 1-based line in the user's scene file
    cleaned_stderr: str           # full stderr with ANSI codes stripped
    summary: str                  # one-liner suitable for an overlay


class ManimErrorParser:
    """Parse raw stderr from a failed Manim subprocess into a ParsedError."""

    _ANSI_RE = re.compile(r'\x1b\[[0-9;]*[a-zA-Z]')
    _EXCEPTION_RE = re.compile(r'^(\w[\w.]*): (.+)$')
    _FILE_LINE_RE = re.compile(r'File "([^"]+)", line (\d+)')

    @staticmethod
    def parse(stderr: str, scene_file_path: str | None = None) -> ParsedError:
        """Parse stderr from a Manim render subprocess.

        Args:
            stderr: Raw stderr text (may contain ANSI escape codes).
            scene_file_path: Path to the scene file used for the render.
                Used to prefer traceback frames from the user's own code.

        Returns:
            A ParsedError with all available fields populated.
        """
        cleaned = ManimErrorParser._ANSI_RE.sub('', stderr)

        # Find the last traceback block
        tb_marker = 'Traceback (most recent call last):'
        last_tb_pos = cleaned.rfind(tb_marker)

        error_type: str | None = None
        message: str | None = None
        line_number: int | None = None

        if last_tb_pos != -1:
            tb_block = cleaned[last_tb_pos:]
            lines = tb_block.splitlines()

            # Find exception type/message from the final non-empty line
            for line in reversed(lines):
                line = line.strip()
                if line:
                    m = ManimErrorParser._EXCEPTION_RE.match(line)
                    if m:
                        error_type = m.group(1)
                        message = m.group(2)
                    break

            # Collect all "File ..., line N" frames from the traceback block
            frames: list[tuple[str, int]] = []
            for line in lines:
                fm = ManimErrorParser._FILE_LINE_RE.search(line)
                if fm:
                    frames.append((fm.group(1), int(fm.group(2))))

            # Pick the best frame: prefer scene file, skip site-packages
            if frames:
                # First pass: prefer frames whose path matches the scene file
                if scene_file_path:
                    user_frames = [
                        (path, ln) for path, ln in frames
                        if scene_file_path in path and 'site-packages' not in path
                    ]
                    if user_frames:
                        line_number = user_frames[-1][1]

                # Second pass: any non-site-packages frame
                if line_number is None:
                    non_pkg = [
                        (path, ln) for path, ln in frames
                        if 'site-packages' not in path
                    ]
                    if non_pkg:
                        line_number = non_pkg[-1][1]

                # Last resort: use the last frame regardless
                if line_number is None:
                    line_number = frames[-1][1]

        # Build summary
        if error_type and message:
            if line_number is not None:
                summary = f"{error_type} on line {line_number}: {message}"
            else:
                summary = f"{error_type}: {message}"
        else:
            # Fall back to the first meaningful line of cleaned stderr
            fallback = next(
                (l.strip() for l in cleaned.splitlines() if l.strip()), ""
            )
            summary = fallback[:120] if fallback else "Unknown render error"

        return ParsedError(
            error_type=error_type,
            message=message,
            line_number=line_number,
            cleaned_stderr=cleaned,
            summary=summary,
        )
