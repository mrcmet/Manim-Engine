"""Main code editor panel combining toolbar and editor widget."""

from typing import Optional

from PySide6.QtCore import Signal, QTimer
from PySide6.QtWidgets import QDockWidget, QWidget, QVBoxLayout

from core.services.code_validator import CodeValidator
from core.services.linter import Linter
from .editor_toolbar import EditorToolbar
from .editor_widget import CodeEditorWidget
from .lint_status_bar import LintStatusBar


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

        # Lint status bar below editor
        self._lint_bar = LintStatusBar()
        layout.addWidget(self._lint_bar)

        self.setWidget(main_widget)

        # Debounce timer — fires 800ms after the last keystroke
        self._lint_timer = QTimer(self)
        self._lint_timer.setSingleShot(True)
        self._lint_timer.setInterval(800)
        self._lint_timer.timeout.connect(self._run_lint)

        # Cached lint state used to gate the render
        self._has_syntax_error = False
        self._syntax_error_msg = ""

        # Connect signals
        self._toolbar.run_clicked.connect(self._on_run_clicked)
        self._toolbar.font_size_changed.connect(self._on_font_size_changed)
        self._toolbar.autofix_clicked.connect(self._on_autofix_clicked)
        self._editor.code_changed.connect(self._on_code_changed)
        self._editor.run_requested.connect(self._on_run_requested)

    # --- Internal handlers ---

    def _on_run_clicked(self) -> None:
        """Handle run button click from toolbar."""
        # Flush pending debounce so lint state is current
        if self._lint_timer.isActive():
            self._lint_timer.stop()
            self._run_lint()
        if self._has_syntax_error:
            return
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
        self._lint_bar.set_pending()
        self._lint_timer.start()  # restarts countdown on each keystroke

    def _on_run_requested(self) -> None:
        """Handle run request from editor (Ctrl+Return)."""
        if self._lint_timer.isActive():
            self._lint_timer.stop()
            self._run_lint()
        if self._has_syntax_error:
            return
        self.run_requested.emit()

    def _on_autofix_clicked(self) -> None:
        """Apply autopep8 fixes and replace editor content."""
        code = self._editor.get_code()
        fixed = Linter.fix(code)
        if fixed != code:
            self._editor.set_code(fixed)

    def _run_lint(self) -> None:
        """Run syntax check then style lint; update status bar and state."""
        code = self._editor.get_code()

        if not code.strip():
            self._has_syntax_error = False
            self._syntax_error_msg = ""
            self._lint_bar.set_clean()
            self._toolbar.set_autofix_enabled(False)
            return

        # Syntax check first (fast, no external dep)
        valid, error_msg = CodeValidator.validate_syntax(code)
        if not valid:
            self._has_syntax_error = True
            self._syntax_error_msg = error_msg or "Syntax error"
            self._lint_bar.set_error(self._syntax_error_msg)
            self._toolbar.set_autofix_enabled(False)
            return

        self._has_syntax_error = False
        self._syntax_error_msg = ""

        # Style lint (no-op if pycodestyle not installed)
        issues = Linter.lint(code)
        if issues:
            self._lint_bar.set_warnings(issues)
            self._toolbar.set_autofix_enabled(True)
        else:
            self._lint_bar.set_clean()
            self._toolbar.set_autofix_enabled(False)

    # --- Public API ---

    def has_syntax_error(self) -> bool:
        """Return True if the current code has a syntax error.

        Returns:
            True if the last lint pass found a syntax error.
        """
        return self._has_syntax_error

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
