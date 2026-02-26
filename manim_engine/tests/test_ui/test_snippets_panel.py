"""Tests for the Snippets panel UI widgets."""

import pytest
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from core.models.snippet import Snippet
from core.services.snippets_service import SnippetsService
from ui.panels.snippets.snippet_list_widget import SnippetListWidget
from ui.panels.snippets.snippets_panel import SnippetsPanel


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def qapp():
    """QApplication singleton for the test session."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture
def sample_snippets():
    return [
        Snippet(id="id-1", name="Circle", code="class C(Scene): pass", description="Circle"),
        Snippet(id="id-2", name="Square", code="class S(Scene): pass"),
        Snippet(id="id-3", name="Triangle", code="class T(Scene): pass", description="Tri"),
    ]


@pytest.fixture
def service(tmp_path):
    """SnippetsService backed by a temp file."""
    return SnippetsService(snippets_file=tmp_path / "snippets.json")


@pytest.fixture
def service_with_snippets(tmp_path):
    """Service pre-populated with two snippets."""
    svc = SnippetsService(snippets_file=tmp_path / "snippets.json")
    svc.add("Alpha", "alpha_code()", "first")
    svc.add("Beta", "beta_code()")
    return svc


# ---------------------------------------------------------------------------
# SnippetListWidget
# ---------------------------------------------------------------------------

def test_snippet_list_widget_population(qapp, sample_snippets):
    widget = SnippetListWidget()
    widget.set_snippets(sample_snippets)

    assert widget.count() == 3
    assert widget.item(0).text() == "Circle"
    assert widget.item(1).text() == "Square"
    assert widget.item(2).text() == "Triangle"


def test_snippet_list_widget_empty(qapp):
    widget = SnippetListWidget()
    widget.set_snippets([])
    assert widget.count() == 0


def test_snippet_list_stores_id(qapp, sample_snippets):
    widget = SnippetListWidget()
    widget.set_snippets(sample_snippets)

    for i, snippet in enumerate(sample_snippets):
        stored_id = widget.item(i).data(Qt.ItemDataRole.UserRole)
        assert stored_id == snippet.id


def test_double_click_emits_insert(qapp, sample_snippets):
    widget = SnippetListWidget()
    widget.set_snippets(sample_snippets)

    emitted_ids = []
    widget.snippet_insert_requested.connect(emitted_ids.append)

    item = widget.item(0)
    widget.itemDoubleClicked.emit(item)

    assert emitted_ids == ["id-1"]


def test_snippet_list_current_id_none_when_empty(qapp):
    widget = SnippetListWidget()
    widget.set_snippets([])
    assert widget.current_snippet_id() is None


def test_snippet_list_current_id_after_selection(qapp, sample_snippets):
    widget = SnippetListWidget()
    widget.set_snippets(sample_snippets)
    widget.setCurrentRow(1)
    assert widget.current_snippet_id() == "id-2"


# ---------------------------------------------------------------------------
# SnippetsPanel
# ---------------------------------------------------------------------------

def test_snippets_panel_creation(qapp, service):
    panel = SnippetsPanel(service)
    assert panel.windowTitle() == "Snippets"
    assert panel._new_btn.text() == "New Snippet"
    assert panel._insert_btn.text() == "Insert"


def test_snippets_panel_loads_snippets(qapp, service_with_snippets):
    panel = SnippetsPanel(service_with_snippets)
    # Two snippets should be in the list
    assert panel._list.count() == 2
    names = [panel._list.item(i).text() for i in range(panel._list.count())]
    assert "Alpha" in names
    assert "Beta" in names


def test_snippets_panel_insert_signal(qapp, service_with_snippets):
    """Selecting a snippet and clicking Insert emits snippet_insert_requested
    with the full code text."""
    panel = SnippetsPanel(service_with_snippets)

    received_codes = []
    panel.snippet_insert_requested.connect(received_codes.append)

    # Select the first item
    panel._list.setCurrentRow(0)
    # Simulate Insert button click
    panel._insert_btn.click()

    assert len(received_codes) == 1
    # The emitted value is the code text, not the id
    assert received_codes[0] in {"alpha_code()", "beta_code()"}


def test_snippets_panel_insert_btn_enabled_on_selection(qapp, service_with_snippets):
    panel = SnippetsPanel(service_with_snippets)

    # Initially no selection — button disabled
    panel._list.clearSelection()
    panel._list.setCurrentItem(None)
    # Trigger update manually
    panel._update_insert_btn()
    assert not panel._insert_btn.isEnabled()

    # Select an item
    panel._list.setCurrentRow(0)
    panel._update_insert_btn()
    assert panel._insert_btn.isEnabled()


def test_snippets_panel_insert_btn_disabled_on_empty(qapp, service):
    """Insert button stays disabled when there are no snippets."""
    panel = SnippetsPanel(service)
    assert not panel._insert_btn.isEnabled()


def test_snippets_panel_apply_theme_no_crash(qapp, service):
    """apply_theme should not raise for any theme dict."""
    panel = SnippetsPanel(service)
    theme = {
        "panel_bg": "#1e1e1e",
        "text_color": "#ffffff",
        "border_color": "#444",
        "editor_bg": "#111",
    }
    # Should not raise
    panel.apply_theme(theme)
