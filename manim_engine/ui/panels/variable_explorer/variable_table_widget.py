"""Variable table widget for displaying and editing animation variables."""

from dataclasses import dataclass
from typing import Any

from PySide6.QtWidgets import QTableWidget, QTableWidgetItem, QMessageBox
from PySide6.QtCore import Signal, Qt


@dataclass
class VariableInfo:
    """Information about a variable."""

    name: str
    value: Any
    type: str
    editable: bool = True


class VariableTableWidget(QTableWidget):
    """Table widget for displaying and editing variables."""

    variable_edited = Signal(str, object)

    def __init__(self, parent=None):
        """Initialize the variable table widget.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)

        # Configure table
        self.setColumnCount(3)
        self.setHorizontalHeaderLabels(["Variable", "Value", "Type"])
        self.horizontalHeader().setStretchLastSection(True)
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QTableWidget.SelectRows)

        # Set column widths
        self.setColumnWidth(0, 150)
        self.setColumnWidth(1, 200)

        # Connect signals
        self.itemChanged.connect(self._on_cell_changed)

        # Track whether we're programmatically updating
        self._updating = False

    def set_variables(self, variables: list[VariableInfo]):
        """Set the variables to display.

        Args:
            variables: List of VariableInfo objects
        """
        self._updating = True
        try:
            self.setRowCount(0)

            for var_info in variables:
                row = self.rowCount()
                self.insertRow(row)

                # Variable name (read-only)
                name_item = QTableWidgetItem(var_info.name)
                name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
                self.setItem(row, 0, name_item)

                # Value (editable if var.editable)
                value_str = self._format_value(var_info.value)
                value_item = QTableWidgetItem(value_str)
                if not var_info.editable:
                    value_item.setFlags(value_item.flags() & ~Qt.ItemIsEditable)
                value_item.setData(Qt.UserRole, var_info.value)
                var_type = getattr(var_info, "var_type", getattr(var_info, "type", "str"))
                value_item.setData(Qt.UserRole + 1, var_type)
                self.setItem(row, 1, value_item)

                # Type (read-only)
                type_item = QTableWidgetItem(var_type)
                type_item.setFlags(type_item.flags() & ~Qt.ItemIsEditable)
                self.setItem(row, 2, type_item)

        finally:
            self._updating = False

    def _format_value(self, value: Any) -> str:
        """Format a value for display.

        Args:
            value: The value to format

        Returns:
            Formatted string representation
        """
        if isinstance(value, (list, tuple)):
            return str(value)
        elif isinstance(value, bool):
            return str(value)
        elif isinstance(value, (int, float)):
            return str(value)
        elif isinstance(value, str):
            return value
        else:
            return str(value)

    def _on_cell_changed(self, item: QTableWidgetItem):
        """Handle cell value changes.

        Args:
            item: The changed table item
        """
        if self._updating:
            return

        # Only handle value column changes
        if item.column() != 1:
            return

        var_name_item = self.item(item.row(), 0)
        if not var_name_item:
            return

        var_name = var_name_item.text()
        var_type = item.data(Qt.UserRole + 1)
        old_value = item.data(Qt.UserRole)
        new_text = item.text()

        try:
            # Parse the new value
            new_value = self._parse_value(new_text, var_type)

            # Validate that it's actually different
            if new_value == old_value:
                return

            # Update stored value
            item.setData(Qt.UserRole, new_value)

            # Emit signal
            self.variable_edited.emit(var_name, new_value)

        except (ValueError, SyntaxError) as e:
            # Revert to old value on error
            self._updating = True
            try:
                item.setText(self._format_value(old_value))
                QMessageBox.warning(
                    self,
                    "Invalid Value",
                    f"Could not parse value as {var_type}: {e}",
                )
            finally:
                self._updating = False

    def _parse_value(self, text: str, var_type: str) -> Any:
        """Parse a text value according to its type.

        Args:
            text: Text to parse
            var_type: Expected type

        Returns:
            Parsed value

        Raises:
            ValueError: If parsing fails
        """
        text = text.strip()

        if var_type == "int":
            return int(text)

        elif var_type == "float":
            return float(text)

        elif var_type == "bool":
            lower = text.lower()
            if lower in ("true", "1", "yes"):
                return True
            elif lower in ("false", "0", "no"):
                return False
            else:
                raise ValueError(f"Invalid boolean value: {text}")

        elif var_type == "str":
            return text

        elif var_type == "tuple":
            # Parse as Python tuple literal
            if not text.startswith("("):
                text = f"({text})"
            try:
                # Safe eval for simple literals
                result = eval(text, {"__builtins__": {}}, {})
                if not isinstance(result, tuple):
                    # Handle single values without trailing comma
                    if "," not in text:
                        result = (result,)
                return result
            except Exception as e:
                raise ValueError(f"Invalid tuple: {e}")

        elif var_type == "list":
            # Parse as Python list literal
            if not text.startswith("["):
                text = f"[{text}]"
            try:
                result = eval(text, {"__builtins__": {}}, {})
                if not isinstance(result, list):
                    result = [result]
                return result
            except Exception as e:
                raise ValueError(f"Invalid list: {e}")

        else:
            # For unknown types, return as string
            return text
