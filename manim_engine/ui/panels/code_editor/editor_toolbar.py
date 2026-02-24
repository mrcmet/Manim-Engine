"""Toolbar for the code editor with run button and font controls."""

from typing import Optional

from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QAction, QIcon, QKeySequence
from PySide6.QtWidgets import QToolBar, QWidget, QSpinBox, QLabel


class EditorToolbar(QToolBar):
    """Toolbar for code editor controls."""

    # Signals
    run_clicked = Signal()              # Emitted when run button is clicked
    font_size_changed = Signal(int)     # Emitted when font size changes
    autofix_clicked = Signal()          # Emitted when Auto-fix button is clicked

    def __init__(self, parent: Optional[QWidget] = None):
        """Initialize the toolbar.

        Args:
            parent: Parent widget.
        """
        super().__init__(parent)

        self.setMovable(False)
        self.setIconSize(QSize(20, 20))
        self.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)

        self._setup_actions()

    def _setup_actions(self) -> None:
        """Set up toolbar actions and widgets."""
        # Run button
        self._run_action = QAction("Run", self)
        self._run_action.setToolTip("Run the code (Ctrl+Return)")
        self._run_action.setShortcut(QKeySequence("Ctrl+Return"))
        self._run_action.triggered.connect(self._on_run_clicked)
        self.addAction(self._run_action)

        self.addSeparator()

        # Auto-fix button
        self._autofix_action = QAction("Auto-fix", self)
        self._autofix_action.setToolTip("Apply autopep8 style fixes (PEP 8)")
        self._autofix_action.triggered.connect(lambda: self.autofix_clicked.emit())
        self._autofix_action.setEnabled(False)
        self.addAction(self._autofix_action)

        self.addSeparator()

        # Font size label
        font_size_label = QLabel("Font Size:")
        font_size_label.setStyleSheet("padding-left: 5px; padding-right: 5px;")
        self.addWidget(font_size_label)

        # Font size spinbox
        self._font_size_spinbox = QSpinBox()
        self._font_size_spinbox.setMinimum(8)
        self._font_size_spinbox.setMaximum(32)
        self._font_size_spinbox.setValue(14)
        self._font_size_spinbox.setSuffix(" pt")
        self._font_size_spinbox.setToolTip("Set font size (8-32 points)")
        self._font_size_spinbox.valueChanged.connect(self._on_font_size_changed)
        self.addWidget(self._font_size_spinbox)

    def _on_run_clicked(self) -> None:
        """Handle run button click."""
        self.run_clicked.emit()

    def _on_font_size_changed(self, size: int) -> None:
        """Handle font size change.

        Args:
            size: New font size in points.
        """
        self.font_size_changed.emit(size)

    def set_autofix_enabled(self, enabled: bool) -> None:
        """Enable or disable the Auto-fix button.

        Args:
            enabled: True when there are style warnings to fix.
        """
        self._autofix_action.setEnabled(enabled)

    def set_run_enabled(self, enabled: bool) -> None:
        """Enable or disable the run button.

        Args:
            enabled: Whether the run button should be enabled.
        """
        self._run_action.setEnabled(enabled)

    def get_font_size(self) -> int:
        """Get the current font size.

        Returns:
            Font size in points.
        """
        return self._font_size_spinbox.value()

    def set_font_size(self, size: int) -> None:
        """Set the font size without emitting signals.

        Args:
            size: Font size in points (8-32).
        """
        self._font_size_spinbox.blockSignals(True)
        self._font_size_spinbox.setValue(size)
        self._font_size_spinbox.blockSignals(False)
