"""Version Timeline panel for visualizing animation history."""

from PySide6.QtWidgets import QDockWidget, QWidget, QVBoxLayout, QScrollArea
from PySide6.QtCore import Signal, Qt

from .timeline_model import TimelineModel, TimelineNode
from .timeline_widget import TimelineWidget


class TimelinePanel(QDockWidget):
    """Dock widget for displaying version timeline."""

    def __init__(self, parent=None):
        """Initialize the timeline panel.

        Args:
            parent: Parent widget
        """
        super().__init__("Version History", parent)
        self.setFeatures(
            QDockWidget.DockWidgetMovable
            | QDockWidget.DockWidgetFloatable
            | QDockWidget.DockWidgetClosable
        )

        # Set maximum height for compact display
        self.setMaximumHeight(100)

        # Main widget with scroll area
        main_widget = QWidget()
        layout = QVBoxLayout(main_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Scroll area for horizontal scrolling
        self._scroll_area = QScrollArea()
        self._scroll_area.setWidgetResizable(True)
        self._scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self._scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._scroll_area.setFrameShape(QScrollArea.NoFrame)

        # Timeline widget
        self._timeline_widget = TimelineWidget()
        self._scroll_area.setWidget(self._timeline_widget)

        layout.addWidget(self._scroll_area)

        self.setWidget(main_widget)

        # Timeline model
        self._model = TimelineModel()

    def set_versions(self, versions: list):
        """Set the versions to display.

        Args:
            versions: List of version objects with attributes:
                - id: Version ID
                - created_at: Timestamp
                - source: Source type
                - prompt: Optional prompt
                - has_video: Whether video exists
        """
        nodes = self._model.set_versions(versions)
        self._timeline_widget.set_nodes(nodes)

    def add_version(self, version):
        """Add a new version to the timeline.

        Args:
            version: Version object with required attributes
        """
        # Create a temporary list with the new version
        all_versions = self._model.nodes
        idx = len(all_versions) + 1

        label = f"v{idx}"
        prompt_snippet = None
        if hasattr(version, "prompt") and version.prompt:
            prompt_snippet = (
                version.prompt[:50] + "..."
                if len(version.prompt) > 50
                else version.prompt
            )

        node = TimelineNode(
            version_id=version.id,
            label=label,
            source=getattr(version, "source", "manual_edit"),
            timestamp=version.created_at,
            prompt_snippet=prompt_snippet,
            has_video=getattr(version, "has_video", False),
            is_current=False,
        )

        self._model.add_node(node)
        self._timeline_widget.add_node(node)

    def select_version(self, version_id: str):
        """Select a version as current.

        Args:
            version_id: ID of the version to select
        """
        self._model.set_current(version_id)
        self._timeline_widget.set_current_version(version_id)

    @property
    def version_selected(self) -> Signal:
        """Signal emitted when a version is selected.

        Returns:
            Signal(str) with version ID
        """
        return self._timeline_widget.version_selected
