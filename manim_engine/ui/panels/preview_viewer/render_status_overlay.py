"""Overlay widget for displaying render status and errors."""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QProgressBar
from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QColor


class RenderStatusOverlay(QWidget):
    """Semi-transparent overlay for showing render status and progress."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self.hide()

    def _setup_ui(self):
        """Initialize UI components."""
        self.setAttribute(Qt.WA_TranslucentBackground)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)

        # Status label
        self.status_label = QLabel()
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 14px;
                font-weight: bold;
                padding: 8px;
                background-color: rgba(30, 30, 46, 200);
                border-radius: 4px;
            }
        """)
        layout.addWidget(self.status_label)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimumWidth(300)
        self.progress_bar.setMaximumWidth(400)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid rgba(137, 180, 250, 180);
                border-radius: 4px;
                background-color: rgba(30, 30, 46, 200);
                height: 20px;
            }
            QProgressBar::chunk {
                background-color: rgba(137, 180, 250, 220);
                border-radius: 2px;
            }
        """)
        layout.addWidget(self.progress_bar)

    def paintEvent(self, event):
        """Paint semi-transparent background.

        Args:
            event: QPaintEvent
        """
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 180))

    def show_loading(self, message: str = "Rendering..."):
        """Show loading state with indeterminate progress.

        Args:
            message: Status message to display
        """
        self.status_label.setText(message)
        self.progress_bar.setRange(0, 0)  # Indeterminate mode
        self.show()
        self.raise_()

    def show_error(self, message: str):
        """Show error state.

        Args:
            message: Error message to display
        """
        self.status_label.setText(f"Error: {message}")
        self.status_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 14px;
                font-weight: bold;
                padding: 8px;
                background-color: rgba(243, 139, 168, 200);
                border-radius: 4px;
            }
        """)
        self.progress_bar.hide()
        self.show()
        self.raise_()

    def hide_overlay(self):
        """Hide the overlay and reset to default state."""
        self.hide()
        self.progress_bar.show()
        self.status_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 14px;
                font-weight: bold;
                padding: 8px;
                background-color: rgba(30, 30, 46, 200);
                border-radius: 4px;
            }
        """)
