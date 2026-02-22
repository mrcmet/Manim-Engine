"""Prompt history display widget."""

from PySide6.QtWidgets import (
    QScrollArea,
    QWidget,
    QVBoxLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QColor


class PromptHistoryEntry(QFrame):
    """Single entry in the prompt history showing status and text."""

    STATUS_COLORS = {
        "pending": "#fab387",  # Peach
        "success": "#a6e3a1",  # Green
        "error": "#f38ba8",    # Red
    }

    def __init__(self, prompt_text: str, status: str = "pending", parent=None):
        super().__init__(parent)
        self._status = status
        self._setup_ui(prompt_text)

    def _setup_ui(self, prompt_text: str):
        """Initialize UI components.

        Args:
            prompt_text: The prompt text to display
        """
        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet("""
            PromptHistoryEntry {
                background-color: #313244;
                border-radius: 4px;
                padding: 8px;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # Status indicator dot
        self.status_dot = StatusDot(self._status)
        self.status_dot.setFixedSize(12, 12)
        layout.addWidget(self.status_dot, alignment=Qt.AlignTop)

        # Prompt text label
        self.prompt_label = QLabel(prompt_text)
        self.prompt_label.setWordWrap(True)
        self.prompt_label.setStyleSheet("color: #cdd6f4; font-size: 12px;")
        layout.addWidget(self.prompt_label, stretch=1)

    def set_status(self, status: str):
        """Update the entry status.

        Args:
            status: New status ("pending", "success", or "error")
        """
        self._status = status
        self.status_dot.set_status(status)


class StatusDot(QWidget):
    """Colored status indicator dot."""

    def __init__(self, status: str = "pending", parent=None):
        super().__init__(parent)
        self._status = status

    def set_status(self, status: str):
        """Update the dot color.

        Args:
            status: Status type ("pending", "success", or "error")
        """
        self._status = status
        self.update()

    def paintEvent(self, event):
        """Paint the status dot.

        Args:
            event: QPaintEvent
        """
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        color_hex = PromptHistoryEntry.STATUS_COLORS.get(
            self._status, PromptHistoryEntry.STATUS_COLORS["pending"]
        )
        color = QColor(color_hex)

        painter.setBrush(color)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(0, 0, self.width(), self.height())


class PromptHistoryWidget(QScrollArea):
    """Scrollable list of prompt history entries."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        """Initialize UI components."""
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setStyleSheet("QScrollArea { border: none; }")

        # Container widget for history entries
        self.container = QWidget()
        self.layout = QVBoxLayout(self.container)
        self.layout.setContentsMargins(8, 8, 8, 8)
        self.layout.setSpacing(8)
        self.layout.addStretch()

        self.setWidget(self.container)

        # Track history entries
        self._entries = []

    def add_entry(self, prompt_text: str, status: str = "pending"):
        """Add a new history entry.

        Args:
            prompt_text: The prompt text
            status: Initial status ("pending", "success", or "error")
        """
        entry = PromptHistoryEntry(prompt_text, status)
        self._entries.append(entry)

        # Insert before the stretch item
        self.layout.insertWidget(self.layout.count() - 1, entry)

        # Scroll to bottom to show new entry
        self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())

    def update_last_entry(self, status: str, response_summary: str = None):
        """Update the status of the most recent entry.

        Args:
            status: New status ("pending", "success", or "error")
            response_summary: Optional response text to append (unused for now)
        """
        if self._entries:
            self._entries[-1].set_status(status)
