"""Dialog for creating or editing a code snippet."""

from typing import Optional

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QMessageBox,
)
from PySide6.QtGui import QFont

from core.models.snippet import Snippet


class SnippetEditorDialog(QDialog):
    """Modal dialog for creating or editing a :class:`~core.models.snippet.Snippet`.

    When *snippet* is provided the fields are pre-populated for editing.
    Accepting the dialog with an empty name or code shows a validation
    message and keeps the dialog open.

    Args:
        snippet: Existing snippet to edit, or ``None`` to create a new one.
        parent: Parent widget.
    """

    def __init__(
        self, snippet: Optional[Snippet] = None, parent=None
    ) -> None:
        super().__init__(parent)
        self._snippet = snippet
        self.setWindowTitle("Edit Snippet" if snippet else "New Snippet")
        self.setMinimumSize(520, 400)
        self._build_ui()
        if snippet:
            self._populate(snippet)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_values(self) -> tuple[str, str, str]:
        """Return the current form values.

        Returns:
            A 3-tuple of ``(name, code, description)``.
        """
        return (
            self._name_edit.text().strip(),
            self._code_edit.toPlainText(),
            self._desc_edit.text().strip(),
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        form = QFormLayout()
        form.setSpacing(6)

        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText("E.g. Circle Animation")
        form.addRow("Name *", self._name_edit)

        self._desc_edit = QLineEdit()
        self._desc_edit.setPlaceholderText("Optional short description")
        form.addRow("Description", self._desc_edit)

        layout.addLayout(form)

        code_label = QLabel("Code *")
        layout.addWidget(code_label)

        self._code_edit = QPlainTextEdit()
        self._code_edit.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        mono_font = QFont("Menlo")
        if not mono_font.exactMatch():
            mono_font = QFont("Courier New")
        mono_font.setPointSize(12)
        self._code_edit.setFont(mono_font)
        layout.addWidget(self._code_edit)

        # Button row
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)

        self._save_btn = QPushButton("Save")
        self._save_btn.setDefault(True)
        self._save_btn.clicked.connect(self._on_accept)
        btn_row.addWidget(self._save_btn)

        layout.addLayout(btn_row)

    def _populate(self, snippet: Snippet) -> None:
        self._name_edit.setText(snippet.name)
        self._desc_edit.setText(snippet.description or "")
        self._code_edit.setPlainText(snippet.code)

    def _on_accept(self) -> None:
        name, code, _ = self.get_values()
        if not name:
            QMessageBox.warning(self, "Validation", "Name is required.")
            self._name_edit.setFocus()
            return
        if not code.strip():
            QMessageBox.warning(self, "Validation", "Code is required.")
            self._code_edit.setFocus()
            return
        self.accept()
