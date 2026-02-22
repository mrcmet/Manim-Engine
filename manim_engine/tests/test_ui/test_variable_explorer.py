"""Tests for Variable Explorer panel."""

import pytest
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from ui.panels.variable_explorer.variable_table_widget import (
    VariableTableWidget,
    VariableInfo,
)
from ui.panels.variable_explorer.variable_explorer_panel import (
    VariableExplorerPanel,
)


@pytest.fixture
def qapp():
    """Create QApplication instance."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture
def sample_variables():
    """Create sample variables for testing."""
    return [
        VariableInfo(name="radius", value=2.0, type="float", editable=True),
        VariableInfo(name="count", value=5, type="int", editable=True),
        VariableInfo(name="enabled", value=True, type="bool", editable=True),
        VariableInfo(name="label", value="Test", type="str", editable=True),
        VariableInfo(
            name="position", value=(1.0, 2.0, 0.0), type="tuple", editable=True
        ),
        VariableInfo(name="readonly_var", value=42, type="int", editable=False),
    ]


def test_parse_value_int(qapp):
    """Test parsing integer values."""
    widget = VariableTableWidget()

    assert widget._parse_value("42", "int") == 42
    assert widget._parse_value("-10", "int") == -10
    assert widget._parse_value("0", "int") == 0

    with pytest.raises(ValueError):
        widget._parse_value("not_a_number", "int")


def test_parse_value_float(qapp):
    """Test parsing float values."""
    widget = VariableTableWidget()

    assert widget._parse_value("3.14", "float") == 3.14
    assert widget._parse_value("-2.5", "float") == -2.5
    assert widget._parse_value("0.0", "float") == 0.0

    with pytest.raises(ValueError):
        widget._parse_value("invalid", "float")


def test_parse_value_bool(qapp):
    """Test parsing boolean values."""
    widget = VariableTableWidget()

    # True values
    assert widget._parse_value("true", "bool") is True
    assert widget._parse_value("True", "bool") is True
    assert widget._parse_value("1", "bool") is True
    assert widget._parse_value("yes", "bool") is True

    # False values
    assert widget._parse_value("false", "bool") is False
    assert widget._parse_value("False", "bool") is False
    assert widget._parse_value("0", "bool") is False
    assert widget._parse_value("no", "bool") is False

    # Invalid
    with pytest.raises(ValueError):
        widget._parse_value("maybe", "bool")


def test_parse_value_str(qapp):
    """Test parsing string values."""
    widget = VariableTableWidget()

    assert widget._parse_value("hello", "str") == "hello"
    assert widget._parse_value("", "str") == ""
    assert widget._parse_value("  spaces  ", "str") == "spaces"


def test_parse_value_tuple(qapp):
    """Test parsing tuple values."""
    widget = VariableTableWidget()

    assert widget._parse_value("(1, 2, 3)", "tuple") == (1, 2, 3)
    assert widget._parse_value("1, 2, 3", "tuple") == (1, 2, 3)
    assert widget._parse_value("(1.0, 2.0)", "tuple") == (1.0, 2.0)

    # Single value without comma becomes single-element tuple
    assert widget._parse_value("5", "tuple") == (5,)

    with pytest.raises(ValueError):
        widget._parse_value("invalid tuple", "tuple")


def test_parse_value_list(qapp):
    """Test parsing list values."""
    widget = VariableTableWidget()

    assert widget._parse_value("[1, 2, 3]", "list") == [1, 2, 3]
    assert widget._parse_value("1, 2, 3", "list") == [1, 2, 3]
    assert widget._parse_value("[1.0, 2.0]", "list") == [1.0, 2.0]

    with pytest.raises(ValueError):
        widget._parse_value("invalid list", "list")


def test_variable_table_population(qapp, sample_variables):
    """Test that variable table populates correctly."""
    widget = VariableTableWidget()
    widget.set_variables(sample_variables)

    # Should have 6 rows
    assert widget.rowCount() == 6

    # Check first row (radius)
    assert widget.item(0, 0).text() == "radius"
    assert widget.item(0, 1).text() == "2.0"
    assert widget.item(0, 2).text() == "float"

    # Check readonly variable
    readonly_row = 5
    assert widget.item(readonly_row, 0).text() == "readonly_var"
    # Value column should not be editable
    assert not (widget.item(readonly_row, 1).flags() & Qt.ItemFlag.ItemIsEditable)


def test_variable_table_empty(qapp):
    """Test that variable table handles empty list."""
    widget = VariableTableWidget()
    widget.set_variables([])

    assert widget.rowCount() == 0


def test_variable_table_format_value(qapp):
    """Test value formatting."""
    widget = VariableTableWidget()

    assert widget._format_value(42) == "42"
    assert widget._format_value(3.14) == "3.14"
    assert widget._format_value(True) == "True"
    assert widget._format_value("text") == "text"
    assert widget._format_value((1, 2, 3)) == "(1, 2, 3)"
    assert widget._format_value([1, 2, 3]) == "[1, 2, 3]"


def test_variable_explorer_panel_creation(qapp):
    """Test that variable explorer panel is created correctly."""
    panel = VariableExplorerPanel()

    assert panel.windowTitle() == "Variables"
    assert panel._refresh_btn.text() == "Refresh"


def test_variable_explorer_panel_set_variables(qapp, sample_variables):
    """Test setting variables in explorer panel."""
    panel = VariableExplorerPanel()
    panel.set_variables(sample_variables)

    # Should populate the table widget
    assert panel._variable_table.rowCount() == 6


def test_variable_explorer_panel_refresh_signal(qapp):
    """Test refresh button signal."""
    panel = VariableExplorerPanel()

    signal_emitted = False

    def on_refresh():
        nonlocal signal_emitted
        signal_emitted = True

    panel.refresh_requested.connect(on_refresh)

    # Click refresh button
    panel._refresh_btn.click()

    assert signal_emitted is True


def test_variable_table_edit_signal(qapp):
    """Test variable edited signal."""
    widget = VariableTableWidget()

    variables = [
        VariableInfo(name="test_var", value=10, type="int", editable=True),
    ]
    widget.set_variables(variables)

    edited_name = None
    edited_value = None

    def on_edited(name, value):
        nonlocal edited_name, edited_value
        edited_name = name
        edited_value = value

    widget.variable_edited.connect(on_edited)

    # Simulate editing the value
    value_item = widget.item(0, 1)
    value_item.setText("20")

    # Trigger itemChanged signal
    widget.itemChanged.emit(value_item)

    assert edited_name == "test_var"
    assert edited_value == 20
