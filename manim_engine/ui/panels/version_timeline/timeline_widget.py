"""Custom widget for rendering version timeline."""

from PySide6.QtWidgets import QWidget, QToolTip
from PySide6.QtCore import Signal, Qt, QPoint, QRect
from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QPainterPath

from .timeline_model import TimelineNode


class TimelineWidget(QWidget):
    """Custom painted widget for version timeline visualization."""

    version_selected = Signal(str)

    # Visual constants
    NODE_RADIUS = 14
    NODE_SPACING = 60
    LINE_Y = 35
    MARGIN_LEFT = 30
    MARGIN_RIGHT = 30

    # Source colors (Catppuccin palette)
    SOURCE_COLORS = {
        "ai": QColor("#89b4fa"),  # Blue
        "manual_edit": QColor("#a6e3a1"),  # Green
        "variable_tweak": QColor("#fab387"),  # Orange
    }

    def __init__(self, parent=None):
        """Initialize the timeline widget.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)

        self._nodes: list[TimelineNode] = []
        self._hovered_index: int | None = None

        # Enable mouse tracking for hover effects
        self.setMouseTracking(True)

        # Set minimum height
        self.setMinimumHeight(70)

    def set_nodes(self, nodes: list[TimelineNode]):
        """Set the timeline nodes to display.

        Args:
            nodes: List of TimelineNode objects
        """
        self._nodes = nodes
        self._update_size()
        self.update()

    def add_node(self, node: TimelineNode):
        """Add a new node to the timeline.

        Args:
            node: TimelineNode to add
        """
        self._nodes.append(node)
        self._update_size()
        self.update()

    def set_current_version(self, version_id: str):
        """Set the current version.

        Args:
            version_id: ID of the current version
        """
        for node in self._nodes:
            node.is_current = node.version_id == version_id
        self.update()

    def _update_size(self):
        """Update widget size based on number of nodes."""
        if not self._nodes:
            self.setMinimumWidth(100)
            return

        required_width = (
            self.MARGIN_LEFT
            + (len(self._nodes) - 1) * self.NODE_SPACING
            + self.MARGIN_RIGHT
        )
        self.setMinimumWidth(required_width)

    def paintEvent(self, event):
        """Paint the timeline.

        Args:
            event: Paint event
        """
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        if not self._nodes:
            return

        # Draw horizontal line
        line_start_x = self.MARGIN_LEFT
        line_end_x = self.MARGIN_LEFT + (len(self._nodes) - 1) * self.NODE_SPACING

        pen = QPen(QColor("#6c7086"), 2)  # Catppuccin overlay0
        painter.setPen(pen)
        painter.drawLine(line_start_x, self.LINE_Y, line_end_x, self.LINE_Y)

        # Draw nodes
        for idx, node in enumerate(self._nodes):
            x = self.MARGIN_LEFT + idx * self.NODE_SPACING
            self._draw_node(painter, x, self.LINE_Y, node, idx)

    def _draw_node(
        self, painter: QPainter, x: int, y: int, node: TimelineNode, index: int
    ):
        """Draw a single timeline node.

        Args:
            painter: QPainter instance
            x: X coordinate of node center
            y: Y coordinate of node center
            node: TimelineNode to draw
            index: Node index
        """
        # Get color based on source
        color = self.SOURCE_COLORS.get(node.source, QColor("#cdd6f4"))

        # Draw current version highlight ring
        if node.is_current:
            painter.setPen(QPen(QColor("#ffffff"), 3))
            painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(
                QPoint(x, y), self.NODE_RADIUS + 4, self.NODE_RADIUS + 4
            )

        # Draw node circle
        painter.setPen(QPen(color.darker(120), 2))
        painter.setBrush(QBrush(color))
        painter.drawEllipse(QPoint(x, y), self.NODE_RADIUS, self.NODE_RADIUS)

        # Draw hover effect
        if self._hovered_index == index:
            painter.setPen(QPen(QColor("#f5e0dc"), 2))  # Catppuccin rosewater
            painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(
                QPoint(x, y), self.NODE_RADIUS + 2, self.NODE_RADIUS + 2
            )

        # Draw label below node
        painter.setPen(QPen(QColor("#cdd6f4")))  # Catppuccin text
        label_rect = QRect(x - 30, y + self.NODE_RADIUS + 5, 60, 20)
        painter.drawText(label_rect, Qt.AlignCenter, node.label)

    def mouseMoveEvent(self, event):
        """Handle mouse move for hover effects.

        Args:
            event: Mouse event
        """
        pos = event.pos()
        old_hovered = self._hovered_index
        self._hovered_index = self._get_node_at_position(pos)

        if old_hovered != self._hovered_index:
            self.update()

            # Show tooltip
            if self._hovered_index is not None:
                node = self._nodes[self._hovered_index]
                tooltip = self._build_tooltip(node)
                QToolTip.showText(event.globalPosition().toPoint(), tooltip, self)
            else:
                QToolTip.hideText()

        super().mouseMoveEvent(event)

    def mousePressEvent(self, event):
        """Handle mouse click to select version.

        Args:
            event: Mouse event
        """
        if event.button() == Qt.LeftButton:
            index = self._get_node_at_position(event.pos())
            if index is not None:
                node = self._nodes[index]
                self.version_selected.emit(node.version_id)

        super().mousePressEvent(event)

    def leaveEvent(self, event):
        """Handle mouse leave to clear hover state.

        Args:
            event: Leave event
        """
        if self._hovered_index is not None:
            self._hovered_index = None
            self.update()
            QToolTip.hideText()

        super().leaveEvent(event)

    def _get_node_at_position(self, pos: QPoint) -> int | None:
        """Get the node index at a given position.

        Args:
            pos: Position to check

        Returns:
            Node index or None if no node at position
        """
        for idx, node in enumerate(self._nodes):
            x = self.MARGIN_LEFT + idx * self.NODE_SPACING
            y = self.LINE_Y

            # Hit test with node radius
            dx = pos.x() - x
            dy = pos.y() - y
            distance_sq = dx * dx + dy * dy

            if distance_sq <= (self.NODE_RADIUS + 2) ** 2:
                return idx

        return None

    def _build_tooltip(self, node: TimelineNode) -> str:
        """Build tooltip text for a node.

        Args:
            node: TimelineNode

        Returns:
            Tooltip HTML string
        """
        lines = [f"<b>{node.label}</b>"]

        # Source
        source_display = {
            "ai": "AI Generated",
            "manual_edit": "Manual Edit",
            "variable_tweak": "Variable Tweak",
        }.get(node.source, node.source.replace("_", " ").title())
        lines.append(f"Source: {source_display}")

        # Timestamp
        timestamp_str = node.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        lines.append(f"Created: {timestamp_str}")

        # Prompt snippet
        if node.prompt_snippet:
            lines.append(f"Prompt: {node.prompt_snippet}")

        # Video status
        if node.has_video:
            lines.append("Video: Available")

        return "<br>".join(lines)
