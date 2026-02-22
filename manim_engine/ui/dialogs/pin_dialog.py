from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit, QDialogButtonBox,
)
from PySide6.QtCore import Qt


class PinDialog(QDialog):
    def __init__(self, is_setup: bool = False, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Set PIN" if is_setup else "Enter PIN")
        self.setFixedSize(300, 150)

        layout = QVBoxLayout(self)
        self._label = QLabel(
            "Choose a 4-6 digit PIN:" if is_setup else "Enter your PIN:"
        )
        self._pin_input = QLineEdit()
        self._pin_input.setEchoMode(QLineEdit.Password)
        self._pin_input.setMaxLength(6)
        self._pin_input.setAlignment(Qt.AlignCenter)
        self._pin_input.setPlaceholderText("****")

        self._error_label = QLabel()
        self._error_label.setStyleSheet("color: red;")

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout.addWidget(self._label)
        layout.addWidget(self._pin_input)
        layout.addWidget(self._error_label)
        layout.addWidget(buttons)

    def get_pin(self) -> str:
        return self._pin_input.text()

    def show_error(self, msg: str):
        self._error_label.setText(msg)
