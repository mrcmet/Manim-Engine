from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QTabWidget, QWidget, QFormLayout,
    QComboBox, QLineEdit, QSpinBox, QDoubleSpinBox, QCheckBox,
    QPushButton, QDialogButtonBox, QGroupBox, QFontComboBox,
    QLabel, QHBoxLayout, QMessageBox,
)
from PySide6.QtCore import Qt

from core.services.settings_service import SettingsService
from core.models.ai_config import AIProviderConfig
from ui.theme import ThemeManager


class SettingsDialog(QDialog):
    def __init__(self, settings_service: SettingsService, theme_manager: ThemeManager,
                 parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setMinimumSize(500, 450)
        self._settings = settings_service
        self._theme_manager = theme_manager

        layout = QVBoxLayout(self)
        self._tabs = QTabWidget()
        layout.addWidget(self._tabs)

        self._build_ai_tab()
        self._build_editor_tab()
        self._build_render_tab()
        self._build_security_tab()

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._save_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self._load_settings()

    def _build_ai_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        self._active_provider = QComboBox()
        self._active_provider.addItems(["anthropic", "openai", "gemini", "ollama"])
        form = QFormLayout()
        form.addRow("Active Provider:", self._active_provider)
        layout.addLayout(form)

        # Provider configs
        self._api_keys = {}
        self._model_names = {}
        self._base_urls = {}
        self._max_tokens = {}
        self._temperatures = {}

        for provider in ["anthropic", "openai", "gemini", "ollama"]:
            group = QGroupBox(provider.capitalize())
            gform = QFormLayout(group)

            key_edit = QLineEdit()
            key_edit.setEchoMode(QLineEdit.Password)
            key_edit.setPlaceholderText("Enter API key...")
            self._api_keys[provider] = key_edit
            gform.addRow("API Key:", key_edit)

            model_edit = QLineEdit()
            defaults = {"anthropic": "claude-sonnet-4-5-20250929", "openai": "gpt-4o",
                        "gemini": "gemini-2.0-flash", "ollama": "llama3"}
            model_edit.setPlaceholderText(defaults.get(provider, ""))
            self._model_names[provider] = model_edit
            gform.addRow("Model:", model_edit)

            if provider == "ollama":
                url_edit = QLineEdit()
                url_edit.setPlaceholderText("http://localhost:11434")
                self._base_urls[provider] = url_edit
                gform.addRow("Base URL:", url_edit)

            tokens = QSpinBox()
            tokens.setRange(256, 16384)
            tokens.setValue(4096)
            self._max_tokens[provider] = tokens
            gform.addRow("Max Tokens:", tokens)

            temp = QDoubleSpinBox()
            temp.setRange(0.0, 2.0)
            temp.setSingleStep(0.1)
            temp.setValue(0.7)
            self._temperatures[provider] = temp
            gform.addRow("Temperature:", temp)

            layout.addWidget(group)

        layout.addStretch()
        self._tabs.addTab(tab, "AI Providers")

    def _build_editor_tab(self):
        tab = QWidget()
        layout = QFormLayout(tab)

        self._font_family = QFontComboBox()
        layout.addRow("Font:", self._font_family)

        self._font_size = QSpinBox()
        self._font_size.setRange(8, 32)
        self._font_size.setValue(14)
        layout.addRow("Font Size:", self._font_size)

        self._theme_selector = QComboBox()
        self._theme_selector.addItems(self._theme_manager.list_themes())
        layout.addRow("Theme:", self._theme_selector)

        self._tab_width = QSpinBox()
        self._tab_width.setRange(2, 8)
        self._tab_width.setValue(4)
        layout.addRow("Tab Width:", self._tab_width)

        self._tabs.addTab(tab, "Editor")

    def _build_render_tab(self):
        tab = QWidget()
        layout = QFormLayout(tab)

        self._default_quality = QComboBox()
        self._default_quality.addItems(["Low (480p)", "Medium (720p)", "High (1080p)", "4K"])
        layout.addRow("Default Quality:", self._default_quality)

        self._render_timeout = QSpinBox()
        self._render_timeout.setRange(10, 120)
        self._render_timeout.setValue(30)
        self._render_timeout.setSuffix(" seconds")
        layout.addRow("Timeout:", self._render_timeout)

        self._output_format = QComboBox()
        self._output_format.addItems(["mp4", "gif", "webm"])
        layout.addRow("Format:", self._output_format)

        self._tabs.addTab(tab, "Rendering")

    def _build_security_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        change_pin_btn = QPushButton("Change PIN")
        change_pin_btn.clicked.connect(self._change_pin)
        layout.addWidget(change_pin_btn)

        remove_pin_btn = QPushButton("Remove PIN")
        remove_pin_btn.clicked.connect(self._remove_pin)
        layout.addWidget(remove_pin_btn)

        layout.addStretch()
        self._tabs.addTab(tab, "Security")

    def _load_settings(self):
        s = self._settings.load()
        idx = self._active_provider.findText(s.active_provider)
        if idx >= 0:
            self._active_provider.setCurrentIndex(idx)

        for name, config in s.ai_providers.items():
            if name in self._model_names:
                self._model_names[name].setText(config.model_name)
            if name in self._max_tokens:
                self._max_tokens[name].setValue(config.max_tokens)
            if name in self._temperatures:
                self._temperatures[name].setValue(config.temperature)
            if name in self._base_urls and config.base_url:
                self._base_urls[name].setText(config.base_url)
            # Load API keys from keyring
            key = self._settings.get_api_key(name)
            if key and name in self._api_keys:
                self._api_keys[name].setText(key)

        self._font_family.setCurrentFont(self._font_family.font())
        self._font_size.setValue(s.editor_font_size)
        tidx = self._theme_selector.findText(s.editor_theme)
        if tidx >= 0:
            self._theme_selector.setCurrentIndex(tidx)
        self._tab_width.setValue(s.editor_tab_width)

        quality_map = {"l": 0, "m": 1, "h": 2, "k": 3}
        self._default_quality.setCurrentIndex(quality_map.get(s.default_quality, 0))
        self._render_timeout.setValue(s.render_timeout)
        fmt_idx = self._output_format.findText(s.output_format)
        if fmt_idx >= 0:
            self._output_format.setCurrentIndex(fmt_idx)

    def _save_and_accept(self):
        s = self._settings.load()

        s.active_provider = self._active_provider.currentText()
        s.editor_font_family = self._font_family.currentFont().family()
        s.editor_font_size = self._font_size.value()
        s.editor_theme = self._theme_selector.currentText()
        s.editor_tab_width = self._tab_width.value()

        quality_map = {0: "l", 1: "m", 2: "h", 3: "k"}
        s.default_quality = quality_map.get(self._default_quality.currentIndex(), "l")
        s.render_timeout = self._render_timeout.value()
        s.output_format = self._output_format.currentText()

        # Save provider configs
        for provider in ["anthropic", "openai", "gemini", "ollama"]:
            api_key = self._api_keys[provider].text()
            if api_key:
                self._settings.store_api_key(provider, api_key)

            config = AIProviderConfig(
                provider_name=provider,
                api_key=None,  # Stored separately in keyring
                model_name=self._model_names[provider].text(),
                base_url=self._base_urls.get(provider, None) and self._base_urls[provider].text(),
                max_tokens=self._max_tokens[provider].value(),
                temperature=self._temperatures[provider].value(),
            )
            s.ai_providers[provider] = config

        self._settings.save(s)
        self.accept()

    def _change_pin(self):
        from ui.dialogs.pin_dialog import PinDialog
        from core.services.auth_service import AuthService

        auth = AuthService(self._settings)
        dialog = PinDialog(is_setup=True, parent=self)
        if dialog.exec():
            pin = dialog.get_pin()
            if len(pin) >= 4:
                auth.set_pin(pin)
                QMessageBox.information(self, "PIN Changed", "PIN updated successfully.")
            else:
                QMessageBox.warning(self, "Invalid PIN", "PIN must be at least 4 digits.")

    def _remove_pin(self):
        from core.services.auth_service import AuthService

        auth = AuthService(self._settings)
        if auth.is_pin_set():
            auth.remove_pin()
            QMessageBox.information(self, "PIN Removed", "PIN protection has been removed.")
