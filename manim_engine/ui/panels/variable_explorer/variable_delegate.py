"""Custom delegate for variable table editing."""

from PySide6.QtWidgets import (
    QStyledItemDelegate,
    QSpinBox,
    QDoubleSpinBox,
    QColorDialog,
    QWidget,
)
from PySide6.QtCore import Qt, QModelIndex
from PySide6.QtGui import QColor


class VariableDelegate(QStyledItemDelegate):
    """Custom delegate for editing variables with type-specific editors."""

    def createEditor(
        self, parent: QWidget, option, index: QModelIndex
    ) -> QWidget | None:
        """Create an appropriate editor based on variable type.

        Args:
            parent: Parent widget
            option: Style option
            index: Model index

        Returns:
            Editor widget or None for default handling
        """
        # Only create custom editors for the value column (column 1)
        if index.column() != 1:
            return super().createEditor(parent, option, index)

        # Get the variable type from column 2
        type_index = index.siblingAtColumn(2)
        var_type = index.model().data(type_index, Qt.DisplayRole)

        # Get variable name to check for special cases
        name_index = index.siblingAtColumn(0)
        var_name = index.model().data(name_index, Qt.DisplayRole)

        # Color variables get a color dialog
        if var_name and "color" in var_name.lower():
            # Note: QColorDialog is not suitable as an inline editor
            # We'll use the standard delegate and handle color in setModelData
            return super().createEditor(parent, option, index)

        # Type-specific editors
        if var_type == "int":
            editor = QSpinBox(parent)
            editor.setMinimum(-2147483648)
            editor.setMaximum(2147483647)
            editor.setFrame(False)
            return editor

        elif var_type == "float":
            editor = QDoubleSpinBox(parent)
            editor.setMinimum(-1e308)
            editor.setMaximum(1e308)
            editor.setDecimals(6)
            editor.setFrame(False)
            return editor

        # Default editor for strings, tuples, etc.
        return super().createEditor(parent, option, index)

    def setEditorData(self, editor: QWidget, index: QModelIndex):
        """Set the editor's initial value from the model.

        Args:
            editor: Editor widget
            index: Model index
        """
        if isinstance(editor, QSpinBox):
            value = index.data(Qt.EditRole)
            try:
                editor.setValue(int(value))
            except (ValueError, TypeError):
                editor.setValue(0)

        elif isinstance(editor, QDoubleSpinBox):
            value = index.data(Qt.EditRole)
            try:
                editor.setValue(float(value))
            except (ValueError, TypeError):
                editor.setValue(0.0)

        else:
            super().setEditorData(editor, index)

    def setModelData(self, editor: QWidget, model, index: QModelIndex):
        """Write the editor's value back to the model.

        Args:
            editor: Editor widget
            model: Data model
            index: Model index
        """
        if isinstance(editor, QSpinBox):
            value = editor.value()
            model.setData(index, str(value), Qt.EditRole)

        elif isinstance(editor, QDoubleSpinBox):
            value = editor.value()
            model.setData(index, str(value), Qt.EditRole)

        else:
            super().setModelData(editor, model, index)

    def updateEditorGeometry(self, editor: QWidget, option, index: QModelIndex):
        """Update the editor's geometry.

        Args:
            editor: Editor widget
            option: Style option
            index: Model index
        """
        editor.setGeometry(option.rect)
