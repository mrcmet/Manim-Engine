"""Main code editor widget with line numbers and syntax highlighting."""

from typing import Optional

from PySide6.QtCore import Qt, QRect, QSize, Signal
from PySide6.QtGui import (
    QColor,
    QPainter,
    QTextFormat,
    QKeyEvent,
    QFont,
    QTextCursor,
    QPaintEvent,
    QResizeEvent,
    QWheelEvent,
)
from PySide6.QtWidgets import QPlainTextEdit, QWidget, QTextEdit

from .python_highlighter import PythonManimHighlighter
from .manim_completer import ManimCompleter


class LineNumberArea(QWidget):
    """Widget for displaying line numbers in the gutter."""

    def __init__(self, editor: "CodeEditorWidget"):
        """Initialize the line number area.

        Args:
            editor: The parent code editor widget.
        """
        super().__init__(editor)
        self._editor = editor

    def sizeHint(self) -> QSize:
        """Return the recommended size for the widget.

        Returns:
            Size hint based on the editor's line number area width.
        """
        return QSize(self._editor.line_number_area_width(), 0)

    def paintEvent(self, event: QPaintEvent) -> None:
        """Paint the line numbers.

        Args:
            event: The paint event.
        """
        self._editor.line_number_area_paint_event(event)


class CodeEditorWidget(QPlainTextEdit):
    """Code editor widget with syntax highlighting, line numbers, and auto-completion."""

    # Signals
    code_changed = Signal(str)  # Emitted when code changes
    run_requested = Signal()    # Emitted when user requests to run code

    def __init__(self, parent: Optional[QWidget] = None):
        """Initialize the code editor.

        Args:
            parent: Parent widget.
        """
        super().__init__(parent)

        # Set up line number area
        self._line_number_area = LineNumberArea(self)

        # Set up syntax highlighter
        self._highlighter = PythonManimHighlighter(self.document())

        # Set up auto-completer
        self._completer = ManimCompleter(self)
        self._completer.setWidget(self)
        self._completer.activated.connect(self._insert_completion)

        # Configure editor appearance
        self._setup_editor()

        # Extra-selection state
        self._current_line_selections: list = []
        self._error_line_selections: list = []

        # Connect signals
        self.blockCountChanged.connect(self._update_line_number_area_width)
        self.updateRequest.connect(self._update_line_number_area)
        self.cursorPositionChanged.connect(self._highlight_current_line)
        self.textChanged.connect(self._on_text_changed)

        # Initial setup
        self._update_line_number_area_width(0)
        self._highlight_current_line()

    def _setup_editor(self) -> None:
        """Configure initial editor settings."""
        # Font
        font = QFont("Courier New", 14)
        font.setFixedPitch(True)
        self.setFont(font)

        # Tab width (4 spaces)
        tab_stop = 4
        self.setTabStopDistance(tab_stop * self.fontMetrics().horizontalAdvance(' '))

        # Line wrapping
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)

        # Background color (dark theme)
        self.setStyleSheet("""
            QPlainTextEdit {
                background-color: #1e1e2e;
                color: #cdd6f4;
                border: none;
                selection-background-color: #585b70;
            }
        """)

    def line_number_area_width(self) -> int:
        """Calculate the width needed for the line number area.

        Returns:
            Width in pixels.
        """
        digits = len(str(max(1, self.blockCount())))
        space = 10 + self.fontMetrics().horizontalAdvance('9') * digits
        return space

    def _update_line_number_area_width(self, _: int) -> None:
        """Update the viewport margins to accommodate line numbers.

        Args:
            _: Block count (unused, required by signal).
        """
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def _update_line_number_area(self, rect: QRect, dy: int) -> None:
        """Update the line number area when scrolling.

        Args:
            rect: The rectangle that needs updating.
            dy: Vertical scroll offset.
        """
        if dy:
            self._line_number_area.scroll(0, dy)
        else:
            self._line_number_area.update(0, rect.y(), self._line_number_area.width(), rect.height())

        if rect.contains(self.viewport().rect()):
            self._update_line_number_area_width(0)

    def resizeEvent(self, event: QResizeEvent) -> None:
        """Handle widget resize events.

        Args:
            event: The resize event.
        """
        super().resizeEvent(event)
        cr = self.contentsRect()
        self._line_number_area.setGeometry(
            QRect(cr.left(), cr.top(), self.line_number_area_width(), cr.height())
        )

    def line_number_area_paint_event(self, event: QPaintEvent) -> None:
        """Paint line numbers in the gutter.

        Args:
            event: The paint event.
        """
        painter = QPainter(self._line_number_area)
        painter.fillRect(event.rect(), QColor("#181825"))

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = int(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + int(self.blockBoundingRect(block).height())

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                painter.setPen(QColor("#6c7086"))
                painter.drawText(
                    0,
                    top,
                    self._line_number_area.width() - 5,
                    self.fontMetrics().height(),
                    Qt.AlignmentFlag.AlignRight,
                    number,
                )

            block = block.next()
            top = bottom
            bottom = top + int(self.blockBoundingRect(block).height())
            block_number += 1

    def _highlight_current_line(self) -> None:
        """Highlight the line containing the cursor."""
        self._current_line_selections = []

        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()
            selection.format.setBackground(QColor("#313244"))
            selection.format.setProperty(QTextFormat.Property.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            self._current_line_selections = [selection]

        self._apply_extra_selections()

    def _apply_extra_selections(self) -> None:
        """Merge current-line and error-line highlights and apply them."""
        self.setExtraSelections(
            self._current_line_selections + self._error_line_selections
        )

    def set_error_line(self, line: int | None) -> None:
        """Highlight a line with a red tint to mark a render error.

        Args:
            line: 1-based line number to highlight, or None to clear.
        """
        self._error_line_selections = []
        if line is not None:
            block = self.document().findBlockByLineNumber(line - 1)
            if block.isValid():
                sel = QTextEdit.ExtraSelection()
                sel.format.setBackground(QColor("#3d1a1a"))
                sel.format.setProperty(QTextFormat.Property.FullWidthSelection, True)
                sel.cursor = QTextCursor(block)
                self._error_line_selections = [sel]
        self._apply_extra_selections()

    def insertFromMimeData(self, source) -> None:
        """Handle paste operations — normalize indentation from copied text."""
        if source.hasText():
            text = source.text()
            lines = text.split('\n')
            if len(lines) > 1:
                # Find the common extra whitespace on non-empty lines after the first.
                # This fixes text copied from web code blocks that adds a leading space.
                rest_non_empty = [l for l in lines[1:] if l.strip()]
                if rest_non_empty:
                    min_indent = min(len(l) - len(l.lstrip()) for l in rest_non_empty)
                    # Only strip if line 1 (first top-level statement) has less indent,
                    # indicating the extra whitespace is an artifact, not real indentation.
                    first_indent = len(lines[0]) - len(lines[0].lstrip()) if lines[0].strip() else 0
                    strip_amount = min_indent - first_indent
                    if strip_amount > 0:
                        stripped = [lines[0]]
                        for l in lines[1:]:
                            if len(l) >= strip_amount and l[:strip_amount].isspace():
                                stripped.append(l[strip_amount:])
                            else:
                                stripped.append(l)
                        text = '\n'.join(stripped)
            cursor = self.textCursor()
            cursor.insertText(text)
            self.setTextCursor(cursor)
        else:
            super().insertFromMimeData(source)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        """Handle key press events for auto-completion and custom behavior.

        Args:
            event: The key event.
        """
        # Handle Ctrl+Return to run code
        if event.key() == Qt.Key.Key_Return and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            self.run_requested.emit()
            return

        # Handle completer
        if self._completer.popup().isVisible():
            if event.key() in (
                Qt.Key.Key_Enter,
                Qt.Key.Key_Return,
                Qt.Key.Key_Escape,
                Qt.Key.Key_Tab,
                Qt.Key.Key_Backtab,
            ):
                event.ignore()
                return

        # Handle Tab key - insert 4 spaces
        if event.key() == Qt.Key.Key_Tab:
            self.insertPlainText("    ")
            return

        # Handle auto-indent on Enter
        if event.key() == Qt.Key.Key_Return:
            cursor = self.textCursor()
            current_line = cursor.block().text()

            # Calculate current indentation
            indent = len(current_line) - len(current_line.lstrip())

            # Add extra indent if line ends with ':'
            extra_indent = 4 if current_line.rstrip().endswith(':') else 0

            super().keyPressEvent(event)
            self.insertPlainText(' ' * (indent + extra_indent))
            return

        # Default behavior
        super().keyPressEvent(event)

        # Update completer
        cursor = self.textCursor()
        cursor.select(QTextCursor.SelectionType.WordUnderCursor)
        completion_prefix = cursor.selectedText()

        if len(completion_prefix) < 2:
            self._completer.popup().hide()
            return

        self._completer.update_prefix(completion_prefix)

        if self._completer.completionCount() > 0:
            cr = self.cursorRect()
            cr.setWidth(
                self._completer.popup().sizeHintForColumn(0)
                + self._completer.popup().verticalScrollBar().sizeHint().width()
            )
            self._completer.complete(cr)
        else:
            self._completer.popup().hide()

    def _insert_completion(self, completion: str) -> None:
        """Insert the selected completion.

        Args:
            completion: The completion text to insert.
        """
        cursor = self.textCursor()
        cursor.select(QTextCursor.SelectionType.WordUnderCursor)
        cursor.insertText(completion)
        self.setTextCursor(cursor)

    def _on_text_changed(self) -> None:
        """Handle text changes and emit code_changed signal."""
        self.code_changed.emit(self.toPlainText())

    def set_code(self, code: str) -> None:
        """Set the editor content.

        Args:
            code: The code to display in the editor.
        """
        self.setPlainText(code)

    def get_code(self) -> str:
        """Get the current editor content.

        Returns:
            The code currently in the editor.
        """
        return self.toPlainText()

    def set_font_family(self, family: str) -> None:
        """Set the font family.

        Args:
            family: Font family name (e.g., "Courier New").
        """
        font = self.font()
        font.setFamily(family)
        self.setFont(font)

    def set_font_size(self, size: int) -> None:
        """Set the font size.

        Args:
            size: Font size in points.
        """
        font = self.font()
        font.setPointSize(size)
        self.setFont(font)

        # Update tab width
        tab_stop = 4
        self.setTabStopDistance(tab_stop * self.fontMetrics().horizontalAdvance(' '))

    def set_theme(self, theme_dict: dict) -> None:
        """Set the syntax highlighting theme.

        Args:
            theme_dict: Dictionary mapping style names to colors.
        """
        self._highlighter.set_theme(theme_dict)
