"""Collapsible error console widget shown below the code editor on render failure."""
from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTextEdit,
)

if TYPE_CHECKING:
    from renderer.error_parser import ParsedError


class ErrorConsoleWidget(QWidget):
    """Collapsible widget that displays render error details below the editor.

    Hidden by default; appears on render failure and disappears on success
    or when the user clicks Dismiss.
    """

    dismissed = Signal()

    _BG = "#181825"
    _BORDER = "#313244"
    _ERROR_COLOR = "#f38ba8"
    _TEXT_COLOR = "#cdd6f4"
    _MUTED_COLOR = "#6c7086"

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header bar
        self._header = QWidget()
        self._header.setFixedHeight(22)
        self._header.setStyleSheet(
            f"background-color: {self._BG}; "
            f"border-top: 1px solid {self._BORDER};"
        )
        header_layout = QHBoxLayout(self._header)
        header_layout.setContentsMargins(8, 0, 8, 0)
        header_layout.setSpacing(6)

        self._dot = QLabel("●")
        self._dot.setStyleSheet(
            f"color: {self._ERROR_COLOR}; font-size: 11px; border: none;"
        )
        self._dot.setFixedWidth(14)

        self._title = QLabel("Render Error")
        self._title.setStyleSheet(
            f"color: {self._ERROR_COLOR}; font-size: 11px; font-weight: bold; border: none;"
        )

        self._dismiss_btn = QPushButton("✕ Dismiss")
        self._dismiss_btn.setFixedHeight(18)
        self._dismiss_btn.setStyleSheet(
            f"QPushButton {{"
            f"  color: {self._MUTED_COLOR}; font-size: 11px;"
            f"  background: transparent; border: none; padding: 0 4px;"
            f"}}"
            f"QPushButton:hover {{ color: {self._TEXT_COLOR}; }}"
        )
        self._dismiss_btn.clicked.connect(self._on_dismiss)

        header_layout.addWidget(self._dot)
        header_layout.addWidget(self._title)
        header_layout.addStretch()
        header_layout.addWidget(self._dismiss_btn)

        layout.addWidget(self._header)

        # Scrollable text area
        self._text_area = QTextEdit()
        self._text_area.setReadOnly(True)
        self._text_area.setMaximumHeight(150)
        self._text_area.setStyleSheet(
            f"QTextEdit {{"
            f"  background-color: {self._BG}; color: {self._TEXT_COLOR};"
            f"  font-family: 'Courier New'; font-size: 11px;"
            f"  border: none; border-top: 1px solid {self._BORDER};"
            f"}}"
        )
        layout.addWidget(self._text_area)

        self.hide()

    # --- Public API ---

    def show_error(self, parsed_error: "ParsedError", stdout: str, stderr: str) -> None:
        """Display the render error details.

        Args:
            parsed_error: Structured error info from ManimErrorParser.
            stdout: Raw stdout from the render subprocess.
            stderr: Raw stderr from the render subprocess.
        """
        text = parsed_error.summary
        if parsed_error.cleaned_stderr.strip():
            text += "\n\n" + parsed_error.cleaned_stderr
        self._text_area.setPlainText(text)
        self._text_area.verticalScrollBar().setValue(0)
        self.show()

    def clear(self) -> None:
        """Clear and hide the console."""
        self._text_area.clear()
        self.hide()

    # --- Private ---

    def _on_dismiss(self) -> None:
        self.clear()
        self.dismissed.emit()
