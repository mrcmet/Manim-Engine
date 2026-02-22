"""Data model for version timeline."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass
class TimelineNode:
    """Represents a single node in the version timeline."""

    version_id: str
    label: str
    source: str  # 'ai', 'manual_edit', 'variable_tweak'
    timestamp: datetime
    prompt_snippet: str | None = None
    has_video: bool = False
    is_current: bool = False


class TimelineModel:
    """Model for managing timeline data."""

    def __init__(self):
        """Initialize the timeline model."""
        self._nodes: list[TimelineNode] = []
        self._current_version_id: str | None = None

    def set_versions(self, versions: list[Any]) -> list[TimelineNode]:
        """Set versions from raw version data.

        Args:
            versions: List of version objects with attributes:
                - id: Version ID
                - created_at: Timestamp
                - source: Source type ('ai', 'manual_edit', 'variable_tweak')
                - prompt: Optional prompt text
                - has_video: Whether video exists

        Returns:
            List of TimelineNode objects
        """
        self._nodes.clear()

        for idx, version in enumerate(versions):
            # Generate label
            label = f"v{idx + 1}"

            # Extract prompt snippet if available
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
                is_current=version.id == self._current_version_id,
            )

            self._nodes.append(node)

        return self._nodes

    def set_current(self, version_id: str | None):
        """Set the current version.

        Args:
            version_id: ID of the current version
        """
        self._current_version_id = version_id

        # Update is_current flag on all nodes
        for node in self._nodes:
            node.is_current = node.version_id == version_id

    @property
    def nodes(self) -> list[TimelineNode]:
        """Get all timeline nodes.

        Returns:
            List of TimelineNode objects
        """
        return self._nodes.copy()

    def get_node_by_id(self, version_id: str) -> TimelineNode | None:
        """Get a node by version ID.

        Args:
            version_id: Version ID to find

        Returns:
            TimelineNode or None if not found
        """
        for node in self._nodes:
            if node.version_id == version_id:
                return node
        return None

    def add_node(self, node: TimelineNode):
        """Add a new node to the timeline.

        Args:
            node: TimelineNode to add
        """
        self._nodes.append(node)

        # If this is marked as current, update current version
        if node.is_current:
            self.set_current(node.version_id)
