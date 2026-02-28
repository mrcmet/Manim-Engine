"""Preview panel for displaying rendered videos."""

from pathlib import Path
from PySide6.QtWidgets import QDockWidget, QWidget, QVBoxLayout, QStackedWidget, QLabel
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt

from .video_player_widget import VideoPlayerWidget
from .render_status_overlay import RenderStatusOverlay


class PreviewPanel(QDockWidget):
    """Dock widget containing video player and render status overlay."""

    def __init__(self, parent=None):
        super().__init__("Preview", parent)
        self._current_pixmap: QPixmap | None = None
        self._setup_ui()

    def _setup_ui(self):
        """Initialize UI components."""
        self.setAllowedAreas(Qt.RightDockWidgetArea | Qt.BottomDockWidgetArea)

        # Container widget
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Stacked widget switches between video player and image label
        self._stack = QStackedWidget()

        # Video player (index 0 — default)
        self.video_player = VideoPlayerWidget()
        self._stack.addWidget(self.video_player)

        # Image label (index 1 — for no-animation scenes)
        self._image_label = QLabel()
        self._image_label.setAlignment(Qt.AlignCenter)
        self._image_label.setMinimumHeight(200)
        self._image_label.setStyleSheet("background-color: #1e1e2e;")
        self._stack.addWidget(self._image_label)

        layout.addWidget(self._stack)

        # Overlay (positioned on top via stacking)
        self.overlay = RenderStatusOverlay(container)

        self.setWidget(container)

    def resizeEvent(self, event):
        """Resize overlay and re-scale image if currently visible.

        Args:
            event: QResizeEvent
        """
        super().resizeEvent(event)
        if hasattr(self, 'overlay'):
            self.overlay.resize(self.widget().size())
        # Re-scale stored pixmap to new label size
        if (self._current_pixmap is not None
                and hasattr(self, '_stack')
                and self._stack.currentWidget() is self._image_label):
            scaled = self._current_pixmap.scaled(
                self._image_label.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )
            self._image_label.setPixmap(scaled)

    def load_video(self, path: Path):
        """Load and play a video file.

        Args:
            path: Path to the video file
        """
        self.overlay.hide_overlay()
        self._stack.setCurrentWidget(self.video_player)
        self.video_player.load_video(path)

    def load_image(self, path: Path):
        """Display a static image file (for no-animation scenes).

        Args:
            path: Path to the PNG image file
        """
        self.overlay.hide_overlay()
        pixmap = QPixmap(str(path))
        if pixmap.isNull():
            self.show_error(f"Failed to load image: {path.name}")
            return
        self._current_pixmap = pixmap
        scaled = pixmap.scaled(
            self._image_label.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )
        self._image_label.setPixmap(scaled)
        self._stack.setCurrentWidget(self._image_label)

    def show_loading(self, message: str = "Rendering..."):
        """Show loading overlay and stop any currently playing video.

        Args:
            message: Status message to display
        """
        self.video_player.media_player.stop()
        self.overlay.show_loading(message)

    def show_error(self, message: str):
        """Show error overlay.

        Args:
            message: Error message to display
        """
        self.overlay.show_error(message)

    def clear(self):
        """Clear the video player and hide overlay."""
        self._current_pixmap = None
        self._image_label.setPixmap(QPixmap())
        self._stack.setCurrentWidget(self.video_player)
        self.video_player.clear()
        self.overlay.hide_overlay()
