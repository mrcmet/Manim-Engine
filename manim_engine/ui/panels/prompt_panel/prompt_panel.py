"""Prompt panel for AI-assisted code generation."""

from PySide6.QtWidgets import QDockWidget, QWidget, QVBoxLayout, QSplitter
from PySide6.QtCore import Qt

from .prompt_input_widget import PromptInputWidget
from .prompt_history_widget import PromptHistoryWidget


class PromptPanel(QDockWidget):
    """Dock widget for AI prompt input and history."""

    def __init__(self, parent=None):
        super().__init__("AI Prompts", parent)
        self._setup_ui()

    def _setup_ui(self):
        """Initialize UI components."""
        self.setAllowedAreas(Qt.RightDockWidgetArea | Qt.BottomDockWidgetArea)

        # Container widget
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Splitter to allow resizing between history and input
        splitter = QSplitter(Qt.Vertical)

        # History widget (top section)
        self.history_widget = PromptHistoryWidget()
        splitter.addWidget(self.history_widget)

        # Input widget (bottom section)
        self.input_widget = PromptInputWidget()
        splitter.addWidget(self.input_widget)

        # Set initial sizes (2:1 ratio for history:input)
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 1)

        layout.addWidget(splitter)
        self.setWidget(container)

    @property
    def prompt_submitted(self):
        """Signal emitted when a prompt is submitted.

        Returns:
            Signal(str, bool) - (prompt_text, include_code)
        """
        return self.input_widget.prompt_submitted

    def set_providers(self, providers: list[str], active_provider: str = None):
        """Set available AI providers.

        Args:
            providers: List of provider names
            active_provider: Name of the currently active provider (optional)
        """
        self.input_widget.set_providers(providers, active_provider)

    def get_selected_provider(self) -> str:
        """Get the currently selected AI provider.

        Returns:
            Name of the selected provider
        """
        return self.input_widget.get_selected_provider()

    def set_loading(self, loading: bool):
        """Enable or disable input during generation.

        Args:
            loading: True to disable input, False to enable
        """
        self.input_widget.set_loading(loading)

    def add_history_entry(self, prompt_text: str, status: str = "pending"):
        """Add a new entry to the prompt history.

        Args:
            prompt_text: The prompt text
            status: Initial status ("pending", "success", or "error")
        """
        self.history_widget.add_entry(prompt_text, status)

    def update_last_history(self, status: str, response_summary: str = None):
        """Update the status of the most recent history entry.

        Args:
            status: New status ("pending", "success", or "error")
            response_summary: Optional response summary (unused for now)
        """
        self.history_widget.update_last_entry(status, response_summary)

    def is_include_code_enabled(self) -> bool:
        """Check if 'Include current code' is enabled.

        Returns:
            True if checkbox is checked
        """
        return self.input_widget.is_include_code_enabled()

    def set_selection_active(self, text: str) -> None:
        """Show or hide the code selection indicator.

        Args:
            text: Indicator text or empty string to hide.
        """
        self.input_widget.set_selection_active(text)
