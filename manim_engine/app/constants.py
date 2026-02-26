from pathlib import Path

APP_NAME = "Manim Engine"
APP_VERSION = "0.1.0"
ORG_NAME = "ManimEngine"
DATA_DIR = Path.home() / ".manim_engine"
PROJECTS_DIR = DATA_DIR / "projects"
SETTINGS_FILE = DATA_DIR / "settings.json"
SNIPPETS_FILE = DATA_DIR / "snippets.json"
MAX_RENDER_TIMEOUT = 30  # seconds
DEFAULT_QUALITY = "l"  # low quality for iteration
