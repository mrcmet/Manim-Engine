"""Prompt input widget for submitting AI generation requests."""

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QComboBox,
    QCheckBox,
    QTextEdit,
    QPushButton,
    QLabel,
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QKeySequence, QShortcut


class PromptInputWidget(QWidget):
    """Widget for entering prompts and configuring AI generation options."""

    prompt_submitted = Signal(str, bool)  # (prompt_text, include_code)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._setup_connections()

    def _setup_ui(self):
        """Initialize UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # Options row
        options_layout = QHBoxLayout()
        options_layout.setSpacing(12)

        # AI provider selector
        self.provider_combo = QComboBox()
        self.provider_combo.setMinimumWidth(150)
        options_layout.addWidget(self.provider_combo)

        # Include code checkbox
        self.include_code_checkbox = QCheckBox("Include current code")
        self.include_code_checkbox.setChecked(True)
        options_layout.addWidget(self.include_code_checkbox)

        options_layout.addStretch()
        layout.addLayout(options_layout)

        # Selection indicator label
        self._selection_label = QLabel()
        self._selection_label.setStyleSheet(
            "color: #a6e3a1; font-size: 11px;"
        )
        self._selection_label.setVisible(False)
        layout.addWidget(self._selection_label)

        # Prompt text input
        self.prompt_text = QTextEdit()
        self.prompt_text.setPlaceholderText("Enter your prompt here...")
        self.prompt_text.setMaximumHeight(120)
        self.prompt_text.setAcceptRichText(False)
        layout.addWidget(self.prompt_text)

        # Generate button
        self.generate_button = QPushButton("Generate")
        self.generate_button.setMaximumWidth(120)
        layout.addWidget(self.generate_button, alignment=Qt.AlignRight)

        # Keyboard shortcut for generate
        self.generate_shortcut = QShortcut(QKeySequence("Ctrl+Return"), self)

    def _setup_connections(self):
        """Connect signals and slots."""
        self.generate_button.clicked.connect(self._submit_prompt)
        self.generate_shortcut.activated.connect(self._submit_prompt)

    def _submit_prompt(self):
        """Emit prompt_submitted signal with current values."""
        prompt_text = self.prompt_text.toPlainText().strip()
        if not prompt_text:
            return

        include_code = self.include_code_checkbox.isChecked()
        self.prompt_submitted.emit(prompt_text, include_code)

    def set_providers(self, providers: list[str], active_provider: str = None):
        """Set available AI providers.

        Args:
            providers: List of provider names
            active_provider: Name of the currently active provider (optional)
        """
        self.provider_combo.clear()
        self.provider_combo.addItems(providers)

        if active_provider and active_provider in providers:
            index = providers.index(active_provider)
            self.provider_combo.setCurrentIndex(index)

    def get_selected_provider(self) -> str:
        """Get the currently selected AI provider.

        Returns:
            Name of the selected provider
        """
        return self.provider_combo.currentText()

    def set_loading(self, loading: bool):
        """Enable or disable input controls during generation.

        Args:
            loading: True to disable controls, False to enable
        """
        self.prompt_text.setEnabled(not loading)
        self.provider_combo.setEnabled(not loading)
        self.include_code_checkbox.setEnabled(not loading)
        self.generate_button.setEnabled(not loading)

        if loading:
            self.generate_button.setText("Generating...")
        else:
            self.generate_button.setText("Generate")

    def clear_input(self):
        """Clear the prompt input field."""
        self.prompt_text.clear()

    def is_include_code_enabled(self) -> bool:
        """Check if 'Include current code' is enabled.

        Returns:
            True if checkbox is checked
        """
        return self.include_code_checkbox.isChecked()

    def set_selection_active(self, text: str) -> None:
        """Show or hide the selection indicator label.

        Args:
            text: Indicator text (e.g. "Selection active (5 lines)").
                  Pass empty string to hide the label.
        """
        if text:
            self._selection_label.setText(text)
            self._selection_label.setVisible(True)
        else:
            self._selection_label.setVisible(False)
