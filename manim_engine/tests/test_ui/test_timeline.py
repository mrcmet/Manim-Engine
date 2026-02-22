"""Tests for Version Timeline panel."""

import pytest
from datetime import datetime
from dataclasses import dataclass

from PySide6.QtWidgets import QApplication

from ui.panels.version_timeline.timeline_model import (
    TimelineModel,
    TimelineNode,
)
from ui.panels.version_timeline.timeline_widget import TimelineWidget
from ui.panels.version_timeline.timeline_panel import TimelinePanel


@dataclass
class MockVersion:
    """Mock version for testing."""

    id: str
    created_at: datetime
    source: str
    prompt: str | None = None
    has_video: bool = False


@pytest.fixture
def qapp():
    """Create QApplication instance."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture
def sample_versions():
    """Create sample versions for testing."""
    return [
        MockVersion(
            id="v1",
            created_at=datetime(2026, 1, 1, 12, 0, 0),
            source="ai",
            prompt="Create a circle animation",
            has_video=True,
        ),
        MockVersion(
            id="v2",
            created_at=datetime(2026, 1, 2, 12, 0, 0),
            source="manual_edit",
            has_video=False,
        ),
        MockVersion(
            id="v3",
            created_at=datetime(2026, 1, 3, 12, 0, 0),
            source="variable_tweak",
            has_video=True,
        ),
    ]


def test_timeline_model_set_versions(sample_versions):
    """Test setting versions in timeline model."""
    model = TimelineModel()
    nodes = model.set_versions(sample_versions)

    assert len(nodes) == 3

    # Check first node
    assert nodes[0].version_id == "v1"
    assert nodes[0].label == "v1"
    assert nodes[0].source == "ai"
    assert nodes[0].prompt_snippet == "Create a circle animation"
    assert nodes[0].has_video is True
    assert nodes[0].is_current is False

    # Check second node
    assert nodes[1].version_id == "v2"
    assert nodes[1].label == "v2"
    assert nodes[1].source == "manual_edit"
    assert nodes[1].prompt_snippet is None
    assert nodes[1].has_video is False

    # Check third node
    assert nodes[2].version_id == "v3"
    assert nodes[2].label == "v3"
    assert nodes[2].source == "variable_tweak"


def test_timeline_model_set_current(sample_versions):
    """Test setting current version."""
    model = TimelineModel()
    model.set_versions(sample_versions)

    # Set v2 as current
    model.set_current("v2")

    nodes = model.nodes

    assert nodes[0].is_current is False
    assert nodes[1].is_current is True
    assert nodes[2].is_current is False


def test_timeline_model_get_node_by_id(sample_versions):
    """Test getting node by ID."""
    model = TimelineModel()
    model.set_versions(sample_versions)

    node = model.get_node_by_id("v2")
    assert node is not None
    assert node.version_id == "v2"
    assert node.source == "manual_edit"

    # Non-existent ID
    node = model.get_node_by_id("nonexistent")
    assert node is None


def test_timeline_model_add_node():
    """Test adding a node to timeline model."""
    model = TimelineModel()

    node = TimelineNode(
        version_id="v1",
        label="v1",
        source="ai",
        timestamp=datetime(2026, 1, 1, 12, 0, 0),
        prompt_snippet="Test prompt",
        has_video=False,
        is_current=False,
    )

    model.add_node(node)

    assert len(model.nodes) == 1
    assert model.nodes[0].version_id == "v1"


def test_timeline_model_add_node_as_current():
    """Test adding a node marked as current."""
    model = TimelineModel()

    node = TimelineNode(
        version_id="v1",
        label="v1",
        source="ai",
        timestamp=datetime(2026, 1, 1, 12, 0, 0),
        is_current=True,
    )

    model.add_node(node)

    assert model._current_version_id == "v1"
    assert model.nodes[0].is_current is True


def test_timeline_model_prompt_snippet_truncation(qapp):
    """Test that long prompts are truncated."""
    model = TimelineModel()

    long_prompt = "a" * 100
    version = MockVersion(
        id="v1",
        created_at=datetime(2026, 1, 1, 12, 0, 0),
        source="ai",
        prompt=long_prompt,
    )

    nodes = model.set_versions([version])

    # Should be truncated to 50 chars + "..."
    assert len(nodes[0].prompt_snippet) == 53
    assert nodes[0].prompt_snippet.endswith("...")


def test_timeline_widget_creation(qapp):
    """Test timeline widget creation."""
    widget = TimelineWidget()

    assert widget.minimumHeight() == 70
    assert widget._nodes == []
    assert widget._hovered_index is None


def test_timeline_widget_set_nodes(qapp, sample_versions):
    """Test setting nodes in timeline widget."""
    widget = TimelineWidget()
    model = TimelineModel()
    nodes = model.set_versions(sample_versions)

    widget.set_nodes(nodes)

    assert len(widget._nodes) == 3
    # Minimum width should be calculated based on nodes
    assert widget.minimumWidth() > 100


def test_timeline_widget_add_node(qapp):
    """Test adding a node to timeline widget."""
    widget = TimelineWidget()

    node = TimelineNode(
        version_id="v1",
        label="v1",
        source="ai",
        timestamp=datetime(2026, 1, 1, 12, 0, 0),
    )

    widget.add_node(node)

    assert len(widget._nodes) == 1


def test_timeline_widget_set_current_version(qapp, sample_versions):
    """Test setting current version in widget."""
    widget = TimelineWidget()
    model = TimelineModel()
    nodes = model.set_versions(sample_versions)
    widget.set_nodes(nodes)

    widget.set_current_version("v2")

    assert widget._nodes[0].is_current is False
    assert widget._nodes[1].is_current is True
    assert widget._nodes[2].is_current is False


def test_timeline_panel_creation(qapp):
    """Test timeline panel creation."""
    panel = TimelinePanel()

    assert panel.windowTitle() == "Version History"
    assert panel.maximumHeight() == 100


def test_timeline_panel_set_versions(qapp, sample_versions):
    """Test setting versions in timeline panel."""
    panel = TimelinePanel()
    panel.set_versions(sample_versions)

    # Should populate the model and widget
    assert len(panel._model.nodes) == 3
    assert len(panel._timeline_widget._nodes) == 3


def test_timeline_panel_add_version(qapp):
    """Test adding a version to timeline panel."""
    panel = TimelinePanel()

    version = MockVersion(
        id="v1",
        created_at=datetime(2026, 1, 1, 12, 0, 0),
        source="ai",
        prompt="Test prompt",
        has_video=True,
    )

    panel.add_version(version)

    assert len(panel._model.nodes) == 1
    assert len(panel._timeline_widget._nodes) == 1


def test_timeline_panel_select_version(qapp, sample_versions):
    """Test selecting a version in timeline panel."""
    panel = TimelinePanel()
    panel.set_versions(sample_versions)

    panel.select_version("v2")

    nodes = panel._model.nodes
    assert nodes[0].is_current is False
    assert nodes[1].is_current is True
    assert nodes[2].is_current is False


def test_timeline_panel_version_selected_signal(qapp, sample_versions):
    """Test version selected signal."""
    panel = TimelinePanel()
    panel.set_versions(sample_versions)

    selected_id = None

    def on_selected(version_id):
        nonlocal selected_id
        selected_id = version_id

    panel.version_selected.connect(on_selected)

    # Emit signal from widget
    panel._timeline_widget.version_selected.emit("v2")

    assert selected_id == "v2"
