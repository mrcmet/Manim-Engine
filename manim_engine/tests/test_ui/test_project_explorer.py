"""Tests for Project Explorer panel."""

import pytest
from datetime import datetime
from dataclasses import dataclass

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from ui.panels.project_explorer.project_list_widget import (
    ProjectListWidget,
)
from ui.panels.project_explorer.project_explorer_panel import (
    ProjectExplorerPanel,
)


@dataclass
class MockProject:
    """Mock project for testing."""

    id: str
    name: str
    updated_at: datetime


@pytest.fixture
def qapp():
    """Create QApplication instance."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture
def sample_projects():
    """Create sample projects for testing."""
    return [
        MockProject(
            id="proj1",
            name="Animation One",
            updated_at=datetime(2026, 1, 1, 12, 0, 0),
        ),
        MockProject(
            id="proj2",
            name="Animation Two",
            updated_at=datetime(2026, 1, 2, 12, 0, 0),
        ),
        MockProject(
            id="proj3",
            name="Test Animation",
            updated_at=datetime(2026, 1, 3, 12, 0, 0),
        ),
    ]


def test_project_list_widget_population(qapp, sample_projects):
    """Test that project list widget populates correctly."""
    widget = ProjectListWidget()
    widget.set_projects(sample_projects)

    # Should have 3 items
    assert widget.count() == 3

    # Items should be sorted by updated_at descending
    assert widget.item(0).text() == "Test Animation"
    assert widget.item(1).text() == "Animation Two"
    assert widget.item(2).text() == "Animation One"

    # Check that IDs are stored correctly
    assert widget.item(0).data(Qt.ItemDataRole.UserRole) == "proj3"
    assert widget.item(1).data(Qt.ItemDataRole.UserRole) == "proj2"
    assert widget.item(2).data(Qt.ItemDataRole.UserRole) == "proj1"


def test_project_list_widget_empty(qapp):
    """Test that project list widget handles empty list."""
    widget = ProjectListWidget()
    widget.set_projects([])

    assert widget.count() == 0


def test_project_list_widget_selection(qapp, sample_projects):
    """Test project selection signal."""
    widget = ProjectListWidget()
    widget.set_projects(sample_projects)

    selected_id = None

    def on_selected(project_id):
        nonlocal selected_id
        selected_id = project_id

    widget.project_selected.connect(on_selected)

    # Simulate double-click on first item
    item = widget.item(0)
    widget.itemDoubleClicked.emit(item)

    assert selected_id == "proj3"


def test_project_explorer_panel_creation(qapp):
    """Test that project explorer panel is created correctly."""
    panel = ProjectExplorerPanel()

    assert panel.windowTitle() == "Projects"
    assert panel._new_project_btn.text() == "New Project"
    assert panel._search_input.placeholderText() == "Search projects..."


def test_project_explorer_panel_refresh(qapp, sample_projects):
    """Test refreshing projects in explorer panel."""
    panel = ProjectExplorerPanel()
    panel.refresh_projects(sample_projects)

    # Should populate the list widget
    assert panel._project_list.count() == 3


def test_project_explorer_panel_search_filter(qapp, sample_projects):
    """Test search filtering in project explorer."""
    panel = ProjectExplorerPanel()
    panel.refresh_projects(sample_projects)

    # Initially shows all 3 projects
    assert panel._project_list.count() == 3

    # Search for "Test"
    panel._search_input.setText("Test")

    # Should show only 1 project
    assert panel._project_list.count() == 1
    assert panel._project_list.item(0).text() == "Test Animation"

    # Clear search
    panel._search_input.clear()

    # Should show all projects again
    assert panel._project_list.count() == 3


def test_project_explorer_panel_search_case_insensitive(qapp, sample_projects):
    """Test that search is case-insensitive."""
    panel = ProjectExplorerPanel()
    panel.refresh_projects(sample_projects)

    # Search with lowercase
    panel._search_input.setText("animation")

    # Should match all projects
    assert panel._project_list.count() == 3

    # Search with uppercase
    panel._search_input.setText("ANIMATION")

    # Should still match all projects
    assert panel._project_list.count() == 3


def test_project_explorer_panel_new_project_signal(qapp):
    """Test new project button signal."""
    panel = ProjectExplorerPanel()

    signal_emitted = False

    def on_new_project():
        nonlocal signal_emitted
        signal_emitted = True

    panel.new_project_requested.connect(on_new_project)

    # Click new project button
    panel._new_project_btn.click()

    assert signal_emitted is True


def test_project_explorer_panel_get_selected_project_id(qapp, sample_projects):
    """Test getting selected project ID."""
    panel = ProjectExplorerPanel()
    panel.refresh_projects(sample_projects)

    # Initially no selection
    assert panel.get_selected_project_id() is None

    # Select first item
    panel._project_list.setCurrentRow(0)

    # Should return the selected project ID
    assert panel.get_selected_project_id() == "proj3"
