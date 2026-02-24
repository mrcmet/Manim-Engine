"""Status bar widget showing lint results below the code editor."""
from __future__ import annotations
from typing import Optional

from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel
from PySide6.QtCore import Qt

from core.services.linter import LintIssue


class LintStatusBar(QWidget):
    """Single-row bar showing lint state: clean / N warnings / syntax error."""

    _BG           = "#181825"  # matches line-number gutter
    _COLOR_CLEAN  = "#a6e3a1"  # Catppuccin Mocha: green
    _COLOR_WARN   = "#f9e2af"  # Catppuccin Mocha: yellow
    _COLOR_ERROR  = "#f38ba8"  # Catppuccin Mocha: red
    _COLOR_MUTED  = "#6c7086"  # Catppuccin Mocha: overlay0

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setFixedHeight(22)
        self.setStyleSheet(f"background-color: {self._BG};")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 0, 8, 0)
        layout.setSpacing(6)

        self._dot = QLabel("●")
        self._dot.setFixedWidth(14)
        self._dot.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        self._text = QLabel()
        self._text.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        layout.addWidget(self._dot)
        layout.addWidget(self._text)
        layout.addStretch()

        self.set_pending()

    def set_clean(self) -> None:
        """Show green dot — no issues."""
        self._dot.setStyleSheet(f"color: {self._COLOR_CLEAN}; font-size: 11px;")
        self._text.setText("No issues")
        self._text.setStyleSheet(f"color: {self._COLOR_MUTED}; font-size: 11px;")

    def set_warnings(self, issues: list[LintIssue]) -> None:
        """Show yellow dot — style issues only, render will proceed.

        Args:
            issues: Non-empty list of LintIssue from the linter.
        """
        self._dot.setStyleSheet(f"color: {self._COLOR_WARN}; font-size: 11px;")
        count = len(issues)
        noun = "warning" if count == 1 else "warnings"
        first = f"  {issues[0]}" if issues else ""
        self._text.setText(f"{count} {noun}{first}")
        self._text.setStyleSheet(f"color: {self._COLOR_WARN}; font-size: 11px;")

    def set_error(self, message: str) -> None:
        """Show red dot — syntax error, render is blocked.

        Args:
            message: Short error description e.g. "Line 5: invalid syntax".
        """
        self._dot.setStyleSheet(f"color: {self._COLOR_ERROR}; font-size: 11px;")
        self._text.setText(f"Syntax error: {message}")
        self._text.setStyleSheet(f"color: {self._COLOR_ERROR}; font-size: 11px;")

    def set_pending(self) -> None:
        """Show neutral state while debounce timer is counting down."""
        self._dot.setStyleSheet(f"color: {self._COLOR_MUTED}; font-size: 11px;")
        self._text.setText("...")
        self._text.setStyleSheet(f"color: {self._COLOR_MUTED}; font-size: 11px;")
