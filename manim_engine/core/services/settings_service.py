import json
import logging
from pathlib import Path
from typing import Any

from app.constants import SETTINGS_FILE
from core.models.settings import AppSettings

logger = logging.getLogger(__name__)


class SettingsService:
    def __init__(self, settings_file: Path = SETTINGS_FILE):
        self._settings_file = settings_file
        self._settings: AppSettings | None = None

    def load(self) -> AppSettings:
        if self._settings is not None:
            return self._settings
        if self._settings_file.exists():
            try:
                with open(self._settings_file, "r") as f:
                    data = json.load(f)
                self._settings = AppSettings.from_dict(data)
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning("Failed to load settings: %s. Using defaults.", e)
                self._settings = AppSettings()
        else:
            self._settings = AppSettings()
        return self._settings

    def save(self, settings: AppSettings) -> None:
        self._settings = settings
        self._settings_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self._settings_file, "w") as f:
            json.dump(settings.to_dict(), f, indent=2)

    def get(self, key: str, default: Any = None) -> Any:
        settings = self.load()
        return getattr(settings, key, default)

    def set(self, key: str, value: Any) -> None:
        settings = self.load()
        if hasattr(settings, key):
            setattr(settings, key, value)
            self.save(settings)

    def store_api_key(self, provider_name: str, api_key: str) -> None:
        try:
            import keyring
            keyring.set_password("manim_engine", provider_name, api_key)
        except Exception:
            logger.warning("Keyring unavailable. API key stored in settings (less secure).")
            settings = self.load()
            if provider_name in settings.ai_providers:
                settings.ai_providers[provider_name].api_key = api_key
            self.save(settings)

    def get_api_key(self, provider_name: str) -> str | None:
        try:
            import keyring
            key = keyring.get_password("manim_engine", provider_name)
            if key:
                return key
        except Exception:
            pass
        settings = self.load()
        config = settings.ai_providers.get(provider_name)
        return config.api_key if config else None
