"""Main code editor panel combining toolbar and editor widget."""

from typing import Optional

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QDockWidget, QWidget, QVBoxLayout

from .editor_toolbar import EditorToolbar
from .editor_widget import CodeEditorWidget


class CodeEditorPanel(QDockWidget):
    """Code editor panel with toolbar and syntax-highlighted editor."""

    # Signals (expose from child widgets)
    code_changed = Signal(str)
    run_requested = Signal()

    def __init__(self, parent: Optional[QWidget] = None):
        """Initialize the code editor panel.

        Args:
            parent: Parent widget.
        """
        super().__init__("Code Editor", parent)

        self.setObjectName("CodeEditorPanel")

        # Create main widget and layout
        main_widget = QWidget()
        layout = QVBoxLayout(main_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Create toolbar
        self._toolbar = EditorToolbar()
        layout.addWidget(self._toolbar)

        # Create editor widget
        self._editor = CodeEditorWidget()
        layout.addWidget(self._editor)

        self.setWidget(main_widget)

        # Connect signals
        self._toolbar.run_clicked.connect(self._on_run_clicked)
        self._toolbar.font_size_changed.connect(self._on_font_size_changed)
        self._editor.code_changed.connect(self._on_code_changed)
        self._editor.run_requested.connect(self._on_run_requested)

    def _on_run_clicked(self) -> None:
        """Handle run button click from toolbar."""
        self.run_requested.emit()

    def _on_font_size_changed(self, size: int) -> None:
        """Handle font size change from toolbar.

        Args:
            size: New font size in points.
        """
        self._editor.set_font_size(size)

    def _on_code_changed(self, code: str) -> None:
        """Handle code changes from editor.

        Args:
            code: The updated code.
        """
        self.code_changed.emit(code)

    def _on_run_requested(self) -> None:
        """Handle run request from editor (Ctrl+Return)."""
        self.run_requested.emit()

    # Public API

    def set_code(self, code: str) -> None:
        """Set the editor content.

        Args:
            code: The code to display in the editor.
        """
        self._editor.set_code(code)

    def get_code(self) -> str:
        """Get the current editor content.

        Returns:
            The code currently in the editor.
        """
        return self._editor.get_code()

    def set_read_only(self, read_only: bool) -> None:
        """Set whether the editor is read-only.

        Args:
            read_only: True to make editor read-only, False for editable.
        """
        self._editor.setReadOnly(read_only)
        self._toolbar.set_run_enabled(not read_only)

    def set_font(self, family: str, size: int) -> None:
        """Set the editor font.

        Args:
            family: Font family name.
            size: Font size in points.
        """
        self._editor.set_font_family(family)
        self._editor.set_font_size(size)
        self._toolbar.set_font_size(size)

    def set_theme(self, theme_dict: dict) -> None:
        """Set the syntax highlighting theme.

        Args:
            theme_dict: Dictionary mapping style names to hex color strings.
        """
        self._editor.set_theme(theme_dict)

    def get_editor_widget(self) -> CodeEditorWidget:
        """Get the underlying editor widget.

        Returns:
            The CodeEditorWidget instance.
        """
        return self._editor

    def get_toolbar(self) -> EditorToolbar:
        """Get the toolbar widget.

        Returns:
            The EditorToolbar instance.
        """
        return self._toolbar
