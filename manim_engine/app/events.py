from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# ── Active events ──────────────────────────────────────

@dataclass(frozen=True)
class RenderStarted:
    pass

@dataclass(frozen=True)
class RenderFinished:
    video_path: Path

@dataclass(frozen=True)
class RenderImageFinished:
    image_path: Path

@dataclass(frozen=True)
class RenderFailed:
    error: str
    parsed_error: Any = None   # ParsedError | None
    stdout: str = ""
    stderr: str = ""

@dataclass(frozen=True)
class AIStarted:
    pass

@dataclass(frozen=True)
class AIFinished:
    code: str

@dataclass(frozen=True)
class AIFailed:
    error: str

@dataclass(frozen=True)
class CodeChanged:
    code: str

@dataclass(frozen=True)
class ProjectOpened:
    project_id: str
    project_name: str

@dataclass(frozen=True)
class VersionCreated:
    version_id: str

@dataclass(frozen=True)
class SettingsChanged:
    pass

@dataclass(frozen=True)
class ThemeChanged:
    theme: dict

# ── Future placeholders (wire up when features land) ───

@dataclass(frozen=True)
class DiagnosticsUpdated:          # LSP lint results
    diagnostics: list = field(default_factory=list)

@dataclass(frozen=True)
class CompletionsReady:            # LSP autocomplete results
    completions: list = field(default_factory=list)

@dataclass(frozen=True)
class TimelineChanged:             # Animation timeline scrub/edit
    position_ms: float = 0.0

@dataclass(frozen=True)
class PlaybackStateChanged:        # Play/pause/stop
    is_playing: bool = False
    position_ms: float = 0.0
