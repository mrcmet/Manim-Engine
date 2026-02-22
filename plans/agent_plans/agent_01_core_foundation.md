# Agent 1: Core Foundation & Data Layer

## Scope
Build all data models, core services, the application signal bus, settings persistence, and simple PIN authentication. This is the foundation every other module depends on.

## Files to Create

```
manim_engine/
├── main.py
├── requirements.txt
├── pyproject.toml
├── .gitignore
├── app/
│   ├── __init__.py
│   ├── application.py
│   ├── constants.py
│   └── signals.py
├── core/
│   ├── __init__.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── project.py
│   │   ├── version.py
│   │   ├── scene_code.py
│   │   ├── ai_config.py
│   │   └── settings.py
│   └── services/
│       ├── __init__.py
│       ├── project_service.py
│       ├── version_service.py
│       ├── settings_service.py
│       ├── variable_parser.py
│       ├── code_validator.py
│       └── auth_service.py
├── resources/
│   └── __init__.py
└── tests/
    ├── __init__.py
    └── test_core/
        ├── __init__.py
        ├── test_project_service.py
        ├── test_version_service.py
        ├── test_variable_parser.py
        └── test_auth_service.py
```

---

## Detailed Specifications

### `app/signals.py` — Signal Bus

Singleton `SignalBus(QObject)` with all application-wide signals. This is the backbone — every module communicates through it.

```python
from PySide6.QtCore import QObject, Signal

class SignalBus(QObject):
    # AI workflow
    prompt_submitted = Signal(str, bool)         # (prompt_text, include_code)
    ai_generation_started = Signal()
    ai_generation_finished = Signal(str)         # generated_code
    ai_generation_failed = Signal(str)           # error_message

    # Code editor
    code_changed = Signal(str)                   # current_code
    code_run_requested = Signal(str)             # code_to_render
    variables_extracted = Signal(list)            # list[VariableInfo]

    # Rendering
    render_started = Signal()
    render_progress = Signal(int)                # percent 0-100
    render_finished = Signal(str)                # output_video_path
    render_failed = Signal(str)                  # error_message

    # Version timeline
    version_created = Signal(str)                # version_id
    version_selected = Signal(str)               # version_id
    version_loaded = Signal(str, str)            # (version_id, code)

    # Project
    project_opened = Signal(str)                 # project_id
    project_created = Signal(str)                # project_id
    project_list_changed = Signal()

    # Variable explorer
    variable_changed = Signal(str, object)       # (var_name, new_value)

    # Settings
    theme_changed = Signal(dict)                 # theme_dict
    settings_changed = Signal()

_bus_instance = None

def get_signal_bus() -> SignalBus:
    global _bus_instance
    if _bus_instance is None:
        _bus_instance = SignalBus()
    return _bus_instance
```

### `app/constants.py`

```python
APP_NAME = "Manim Engine"
APP_VERSION = "0.1.0"
ORG_NAME = "ManimEngine"
DATA_DIR = Path.home() / ".manim_engine"
PROJECTS_DIR = DATA_DIR / "projects"
SETTINGS_FILE = DATA_DIR / "settings.json"
MAX_RENDER_TIMEOUT = 30  # seconds
DEFAULT_QUALITY = "l"     # low quality for iteration
```

### `app/application.py`

QApplication subclass. Handles:
- Creating `DATA_DIR` and `PROJECTS_DIR` if they don't exist
- Instantiating `SignalBus`
- Instantiating all services
- Showing PIN dialog before main window (delegates to `auth_service`)
- Creating and showing `MainWindow`

```python
class ManimEngineApp(QApplication):
    def __init__(self, argv):
        super().__init__(argv)
        self.setApplicationName(APP_NAME)
        self.setOrganizationName(ORG_NAME)
        self._ensure_data_dirs()
        self._signal_bus = get_signal_bus()
        self._settings_service = SettingsService()
        self._auth_service = AuthService(self._settings_service)
        self._project_service = ProjectService()
        self._version_service = VersionService()

    def run(self):
        if not self._auth_service.authenticate():
            return 1
        # MainWindow creation delegated to Agent 7
        # For now, stub: self._main_window = MainWindow(...)
        return self.exec()
```

### Data Models (`core/models/`)

All models are `@dataclass` classes. No Qt dependencies.

**`project.py`**
```python
@dataclass
class Project:
    id: str                    # UUID string
    name: str
    description: str
    created_at: datetime
    updated_at: datetime
    current_version_id: str | None
    directory_path: Path
```

**`version.py`**
```python
@dataclass
class Version:
    id: str                    # UUID string
    project_id: str
    code: str                  # full Manim source code
    prompt: str | None         # prompt that generated this (if AI)
    source: str                # "ai" | "manual_edit" | "variable_tweak"
    parent_version_id: str | None
    created_at: datetime
    video_path: Path | None
    thumbnail_path: Path | None
```

**`scene_code.py`**
```python
@dataclass
class VariableInfo:
    name: str
    value: Any
    var_type: str              # "int", "float", "str", "color", "tuple", "list", "bool"
    line_number: int
    editable: bool
```

**`ai_config.py`**
```python
@dataclass
class AIProviderConfig:
    provider_name: str         # "anthropic", "openai", "gemini", "ollama"
    api_key: str | None
    model_name: str
    base_url: str | None       # for Ollama
    max_tokens: int = 4096
    temperature: float = 0.7
```

**`settings.py`**
```python
@dataclass
class AppSettings:
    # Editor
    editor_font_family: str = "Courier New"
    editor_font_size: int = 14
    editor_theme: str = "dark"
    editor_tab_width: int = 4

    # Rendering
    default_quality: str = "l"
    render_timeout: int = 30
    output_format: str = "mp4"

    # AI
    active_provider: str = "anthropic"
    ai_providers: dict[str, AIProviderConfig] = field(default_factory=dict)

    # App
    last_project_id: str | None = None
    window_geometry: bytes | None = None
    window_state: bytes | None = None

    # Auth
    pin_hash: str | None = None
```

### Services (`core/services/`)

**`project_service.py`**
```python
class ProjectService:
    def __init__(self, projects_dir: Path = PROJECTS_DIR):
        ...

    def create_project(self, name: str, description: str = "") -> Project:
        """Create project directory and metadata file. Returns Project."""

    def open_project(self, project_id: str) -> Project:
        """Load project metadata from disk."""

    def list_projects(self) -> list[Project]:
        """List all projects sorted by updated_at descending."""

    def delete_project(self, project_id: str) -> None:
        """Remove project directory and all versions."""

    def update_project(self, project: Project) -> None:
        """Save updated project metadata."""
```

Storage format: `~/.manim_engine/projects/<uuid>/project.json`

**`version_service.py`**
```python
class VersionService:
    def __init__(self, projects_dir: Path = PROJECTS_DIR):
        ...

    def create_version(self, project_id: str, code: str,
                       prompt: str | None = None,
                       source: str = "manual_edit",
                       parent_version_id: str | None = None) -> Version:
        """Create version directory, write scene.py and version.json."""

    def get_version(self, project_id: str, version_id: str) -> Version:
        """Load version from disk."""

    def list_versions(self, project_id: str) -> list[Version]:
        """All versions for a project, sorted by created_at."""

    def set_video_path(self, project_id: str, version_id: str, video_path: Path) -> None:
        """Update version with rendered video path."""
```

Storage: `~/.manim_engine/projects/<uuid>/versions/<version-uuid>/`

**`settings_service.py`**
```python
class SettingsService:
    def __init__(self, settings_file: Path = SETTINGS_FILE):
        ...

    def load(self) -> AppSettings:
        """Load from JSON file, return defaults if file missing."""

    def save(self, settings: AppSettings) -> None:
        """Write to JSON file."""

    def get(self, key: str, default: Any = None) -> Any:
        """Get a single setting value."""

    def set(self, key: str, value: Any) -> None:
        """Set and persist a single setting."""
```

API keys stored via `keyring` library (system keychain). Fallback to settings.json with a warning.

**`variable_parser.py`**
```python
import ast

class VariableParser:
    @staticmethod
    def extract_variables(code: str) -> list[VariableInfo]:
        """Parse code with ast module. Find top-level assignments (before class def).
        Identify type from ast node (Constant, List, Tuple).
        Mark as editable if type is int, float, str, bool, tuple of numbers, or
        if variable name contains 'color'."""

    @staticmethod
    def replace_variable(code: str, var_name: str, new_value: Any) -> str:
        """Find the assignment line for var_name in code.
        Replace the value portion while preserving the rest of the line.
        Use ast to locate, string manipulation to replace (preserves formatting)."""
```

Implementation notes for `extract_variables`:
- Parse with `ast.parse(code)`
- Walk top-level `ast.Assign` and `ast.AnnAssign` nodes
- For each, extract: target name, value (via `ast.literal_eval` if possible), type string, line number
- Skip assignments inside class/function bodies (only top-level)
- Color detection: if var name contains "color" or value looks like a hex string or Manim color constant

**`code_validator.py`**
```python
class CodeValidator:
    @staticmethod
    def validate_syntax(code: str) -> tuple[bool, str | None]:
        """Try ast.parse(code). Return (True, None) or (False, error_message)."""

    @staticmethod
    def has_scene_class(code: str) -> tuple[bool, str | None]:
        """Check if code contains a class inheriting from Scene. Return (found, class_name)."""
```

**`auth_service.py`**
```python
import hashlib

class AuthService:
    def __init__(self, settings_service: SettingsService):
        ...

    def is_pin_set(self) -> bool:
        """Check if a PIN hash exists in settings."""

    def set_pin(self, pin: str) -> None:
        """Hash PIN with hashlib.pbkdf2_hmac and store hash + salt in settings."""

    def verify_pin(self, pin: str) -> bool:
        """Hash input and compare to stored hash."""

    def authenticate(self) -> bool:
        """Show PIN dialog. If no PIN set, show setup dialog. Returns True if authenticated.
        Uses a simple QInputDialog for PIN entry (4-6 digit PIN)."""

    def remove_pin(self) -> None:
        """Remove PIN requirement."""
```

### `main.py`

```python
import sys
from app.application import ManimEngineApp

def main():
    app = ManimEngineApp(sys.argv)
    sys.exit(app.run())

if __name__ == "__main__":
    main()
```

### `requirements.txt`

```
PySide6>=6.6.0
httpx>=0.25.0
keyring>=24.0.0
manim>=0.18.0
```

### `pyproject.toml`

Standard Python project config with the above dependencies. Set `requires-python = ">=3.11"`.

### `.gitignore`

Standard Python gitignore + `__pycache__/`, `.venv/`, `*.pyc`, `media/`, `*.mp4`, `*.gif`.

---

## Tests

**`test_project_service.py`**: Create/list/delete projects, verify JSON files on disk (use tmp_path fixture).
**`test_version_service.py`**: Create versions, verify parent chain, list versions for project.
**`test_variable_parser.py`**: Parse sample Manim code, verify extracted variables, test replace_variable.
**`test_auth_service.py`**: Set PIN, verify correct/incorrect PIN, remove PIN.

## Verification

```bash
cd manim_engine
python -m pytest tests/test_core/ -v
python -c "from app.signals import get_signal_bus; print('Signal bus OK')"
python -c "from core.services.variable_parser import VariableParser; print(VariableParser.extract_variables('x = 5\ny = 3.14\ncolor = \"#FF0000\"'))"
```

## Dependencies on Other Agents

None. This is the foundation package.

## What Other Agents Need From You

Every other agent imports:
- `app.signals.get_signal_bus`
- `app.constants.*`
- `core.models.*` (dataclasses)
- Services as needed
