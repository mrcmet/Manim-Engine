"""Tests for prompt panel widgets."""

import pytest
from PySide6.QtWidgets import QApplication
from ui.panels.prompt_panel.prompt_panel import PromptPanel
from ui.panels.prompt_panel.prompt_input_widget import PromptInputWidget
from ui.panels.prompt_panel.prompt_history_widget import PromptHistoryWidget


@pytest.fixture(scope="module")
def qapp():
    """Create QApplication instance for tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


def test_prompt_input_instantiation(qapp):
    """Test that PromptInputWidget can be instantiated."""
    widget = PromptInputWidget()
    assert widget is not None
    assert widget.provider_combo is not None
    assert widget.include_code_checkbox is not None
    assert widget.prompt_text is not None
    assert widget.generate_button is not None


def test_set_loading(qapp):
    """Test set_loading method enables/disables controls."""
    widget = PromptInputWidget()

    # Initially enabled
    assert widget.prompt_text.isEnabled()
    assert widget.provider_combo.isEnabled()
    assert widget.include_code_checkbox.isEnabled()
    assert widget.generate_button.isEnabled()
    assert widget.generate_button.text() == "Generate"

    # Set loading state
    widget.set_loading(True)
    assert not widget.prompt_text.isEnabled()
    assert not widget.provider_combo.isEnabled()
    assert not widget.include_code_checkbox.isEnabled()
    assert not widget.generate_button.isEnabled()
    assert widget.generate_button.text() == "Generating..."

    # Restore enabled state
    widget.set_loading(False)
    assert widget.prompt_text.isEnabled()
    assert widget.provider_combo.isEnabled()
    assert widget.include_code_checkbox.isEnabled()
    assert widget.generate_button.isEnabled()
    assert widget.generate_button.text() == "Generate"


def test_provider_selector(qapp):
    """Test setting and getting AI providers."""
    widget = PromptInputWidget()

    # Set providers
    providers = ["OpenAI", "Anthropic", "Google"]
    widget.set_providers(providers)

    assert widget.provider_combo.count() == 3
    assert widget.provider_combo.itemText(0) == "OpenAI"
    assert widget.provider_combo.itemText(1) == "Anthropic"
    assert widget.provider_combo.itemText(2) == "Google"

    # Test with active provider
    widget.set_providers(providers, "Anthropic")
    assert widget.get_selected_provider() == "Anthropic"


def test_include_code_checkbox(qapp):
    """Test include code checkbox functionality."""
    widget = PromptInputWidget()

    # Default state is checked
    assert widget.include_code_checkbox.isChecked()
    assert widget.is_include_code_enabled()

    # Uncheck
    widget.include_code_checkbox.setChecked(False)
    assert not widget.is_include_code_enabled()


def test_clear_input(qapp):
    """Test clearing prompt input."""
    widget = PromptInputWidget()

    # Set some text
    widget.prompt_text.setPlainText("Test prompt")
    assert widget.prompt_text.toPlainText() == "Test prompt"

    # Clear
    widget.clear_input()
    assert widget.prompt_text.toPlainText() == ""


def test_prompt_history_instantiation(qapp):
    """Test that PromptHistoryWidget can be instantiated."""
    widget = PromptHistoryWidget()
    assert widget is not None
    assert widget.container is not None
    assert widget.layout is not None


def test_add_history_entry(qapp):
    """Test adding entries to prompt history."""
    widget = PromptHistoryWidget()

    # Initially empty
    assert len(widget._entries) == 0

    # Add entry
    widget.add_entry("First prompt", "pending")
    assert len(widget._entries) == 1

    # Add more entries
    widget.add_entry("Second prompt", "success")
    widget.add_entry("Third prompt", "error")
    assert len(widget._entries) == 3


def test_update_last_history_entry(qapp):
    """Test updating the last history entry status."""
    widget = PromptHistoryWidget()

    # Add entry
    widget.add_entry("Test prompt", "pending")
    entry = widget._entries[0]
    assert entry._status == "pending"

    # Update status
    widget.update_last_entry("success")
    assert entry._status == "success"

    # Update to error
    widget.update_last_entry("error")
    assert entry._status == "error"


def test_prompt_panel_instantiation(qapp):
    """Test that PromptPanel can be instantiated."""
    panel = PromptPanel()
    assert panel is not None
    assert panel.history_widget is not None
    assert panel.input_widget is not None


def test_prompt_panel_methods(qapp):
    """Test PromptPanel public methods."""
    panel = PromptPanel()

    # Test set_providers
    providers = ["OpenAI", "Anthropic"]
    panel.set_providers(providers, "Anthropic")
    assert panel.get_selected_provider() == "Anthropic"

    # Test set_loading
    panel.set_loading(True)
    assert not panel.input_widget.generate_button.isEnabled()

    panel.set_loading(False)
    assert panel.input_widget.generate_button.isEnabled()

    # Test add_history_entry
    panel.add_history_entry("Test prompt", "pending")
    assert len(panel.history_widget._entries) == 1

    # Test update_last_history
    panel.update_last_history("success")
    assert panel.history_widget._entries[0]._status == "success"

    # Test is_include_code_enabled
    assert panel.is_include_code_enabled()
