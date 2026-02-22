from PySide6.QtWidgets import (
    QDialog, QFormLayout, QLineEdit, QTextEdit, QDialogButtonBox,
)


class NewProjectDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("New Project")
        self.setMinimumWidth(350)

        layout = QFormLayout(self)

        self._name = QLineEdit()
        self._name.setPlaceholderText("My Animation")

        self._desc = QTextEdit()
        self._desc.setMaximumHeight(80)
        self._desc.setPlaceholderText("Optional description...")

        layout.addRow("Project Name:", self._name)
        layout.addRow("Description:", self._desc)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def get_values(self) -> tuple[str, str]:
        return self._name.text(), self._desc.toPlainText()
