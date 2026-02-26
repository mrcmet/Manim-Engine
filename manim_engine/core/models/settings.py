from dataclasses import dataclass, field

from core.models.ai_config import AIProviderConfig


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
    pin_salt: str | None = None

    # AI Context
    custom_prompt_context: str = ""

    def to_dict(self) -> dict:
        data = {
            "editor_font_family": self.editor_font_family,
            "editor_font_size": self.editor_font_size,
            "editor_theme": self.editor_theme,
            "editor_tab_width": self.editor_tab_width,
            "default_quality": self.default_quality,
            "render_timeout": self.render_timeout,
            "output_format": self.output_format,
            "active_provider": self.active_provider,
            "ai_providers": {
                name: config.to_dict()
                for name, config in self.ai_providers.items()
            },
            "last_project_id": self.last_project_id,
            "window_geometry": bytes(self.window_geometry).hex() if self.window_geometry else None,
            "window_state": bytes(self.window_state).hex() if self.window_state else None,
            "pin_hash": self.pin_hash,
            "pin_salt": self.pin_salt,
            "custom_prompt_context": self.custom_prompt_context,
        }
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "AppSettings":
        ai_providers = {}
        for name, config_data in data.get("ai_providers", {}).items():
            ai_providers[name] = AIProviderConfig.from_dict(config_data)

        geometry = data.get("window_geometry")
        state = data.get("window_state")

        return cls(
            editor_font_family=data.get("editor_font_family", "Courier New"),
            editor_font_size=data.get("editor_font_size", 14),
            editor_theme=data.get("editor_theme", "dark"),
            editor_tab_width=data.get("editor_tab_width", 4),
            default_quality=data.get("default_quality", "l"),
            render_timeout=data.get("render_timeout", 30),
            output_format=data.get("output_format", "mp4"),
            active_provider=data.get("active_provider", "anthropic"),
            ai_providers=ai_providers,
            last_project_id=data.get("last_project_id"),
            window_geometry=bytes.fromhex(geometry) if geometry else None,
            window_state=bytes.fromhex(state) if state else None,
            pin_hash=data.get("pin_hash"),
            pin_salt=data.get("pin_salt"),
            custom_prompt_context=data.get("custom_prompt_context", ""),
        )
