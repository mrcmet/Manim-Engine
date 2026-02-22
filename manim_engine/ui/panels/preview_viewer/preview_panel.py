"""Preview panel for displaying rendered videos."""

from pathlib import Path
from PySide6.QtWidgets import QDockWidget, QWidget, QVBoxLayout
from PySide6.QtCore import Qt

from .video_player_widget import VideoPlayerWidget
from .render_status_overlay import RenderStatusOverlay


class PreviewPanel(QDockWidget):
    """Dock widget containing video player and render status overlay."""

    def __init__(self, parent=None):
        super().__init__("Preview", parent)
        self._setup_ui()

    def _setup_ui(self):
        """Initialize UI components."""
        self.setAllowedAreas(Qt.RightDockWidgetArea | Qt.BottomDockWidgetArea)

        # Container widget
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Video player
        self.video_player = VideoPlayerWidget()
        layout.addWidget(self.video_player)

        # Overlay (positioned on top via stacking)
        self.overlay = RenderStatusOverlay(container)

        self.setWidget(container)

    def resizeEvent(self, event):
        """Resize overlay to match container.

        Args:
            event: QResizeEvent
        """
        super().resizeEvent(event)
        if hasattr(self, 'overlay'):
            self.overlay.resize(self.widget().size())

    def load_video(self, path: Path):
        """Load and play a video file.

        Args:
            path: Path to the video file
        """
        self.overlay.hide_overlay()
        self.video_player.load_video(path)

    def show_loading(self, message: str = "Rendering..."):
        """Show loading overlay.

        Args:
            message: Status message to display
        """
        self.overlay.show_loading(message)

    def show_error(self, message: str):
        """Show error overlay.

        Args:
            message: Error message to display
        """
        self.overlay.show_error(message)

    def clear(self):
        """Clear the video player and hide overlay."""
        self.video_player.clear()
        self.overlay.hide_overlay()
