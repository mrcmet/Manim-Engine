"""Frameless tooltip-style popup showing a preview of snippet code."""

from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel, QPlainTextEdit
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

_MAX_LINES = 20


class SnippetCodePopup(QFrame):
    """A frameless floating frame that shows a read-only code preview.

    Positioned to the right of the hovered list row so it never
    obscures the snippet name.

    Usage::

        popup = SnippetCodePopup(parent_widget)
        popup.show_snippet("Circle Animation", code, global_pos)
        popup.hide()
    """

    def __init__(self, parent=None) -> None:
        super().__init__(
            parent,
            Qt.WindowType.ToolTip | Qt.WindowType.FramelessWindowHint,
        )
        self.setFixedWidth(420)
        self._build_ui()
        self.hide()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def show_snippet(self, name: str, code: str, global_pos) -> None:
        """Display the popup near *global_pos*.

        Args:
            name: Snippet display name shown as a header label.
            code: Full source code; truncated to
                :data:`_MAX_LINES` lines with a continuation notice.
            global_pos: A ``QPoint`` in global screen coordinates where
                the popup should appear (typically the right edge of the
                hovered list row).
        """
        self._name_label.setText(name)

        lines = code.splitlines()
        truncated = len(lines) > _MAX_LINES
        display_lines = lines[:_MAX_LINES]
        display_text = "\n".join(display_lines)
        if truncated:
            remaining = len(lines) - _MAX_LINES
            display_text += f"\n… ({remaining} more line{'s' if remaining != 1 else ''})"

        self._code_view.setPlainText(display_text)

        # Resize height to fit content (cap at ~400 px)
        doc_height = self._code_view.document().size().height()
        self._code_view.setFixedHeight(min(int(doc_height) + 8, 400))

        self.adjustSize()
        self.move(global_pos)
        self.show()
        self.raise_()

    def apply_theme(self, theme: dict) -> None:
        """Style the popup to match the application theme.

        Args:
            theme: Theme dictionary from :class:`~ui.theme.ThemeManager`.
        """
        bg = theme.get("panel_bg", "#2b2b2b")
        fg = theme.get("text_color", "#d4d4d4")
        border = theme.get("border_color", "#555555")
        editor_bg = theme.get("editor_bg", "#1e1e1e")

        self.setStyleSheet(
            f"QFrame {{ background: {bg}; border: 1px solid {border}; border-radius: 4px; }}"
        )
        self._name_label.setStyleSheet(
            f"QLabel {{ color: {fg}; font-weight: bold;"
            f" padding: 4px 6px; background: {bg}; }}"
        )
        self._code_view.setStyleSheet(
            f"QPlainTextEdit {{ background: {editor_bg}; color: {fg};"
            f" border: none; padding: 4px; }}"
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._name_label = QLabel()
        self._name_label.setWordWrap(False)
        layout.addWidget(self._name_label)

        self._code_view = QPlainTextEdit()
        self._code_view.setReadOnly(True)
        self._code_view.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)

        mono_font = QFont("Menlo")
        if not mono_font.exactMatch():
            mono_font = QFont("Courier New")
        mono_font.setPointSize(11)
        self._code_view.setFont(mono_font)

        layout.addWidget(self._code_view)
