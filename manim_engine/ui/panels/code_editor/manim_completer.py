"""Auto-completion widget for Manim and Python keywords."""

import json
from pathlib import Path
from typing import List, Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QStandardItemModel, QStandardItem
from PySide6.QtWidgets import QCompleter, QPlainTextEdit


class ManimCompleter(QCompleter):
    """Auto-completion widget for Python and Manim keywords."""

    def __init__(self, parent: Optional[QPlainTextEdit] = None):
        """Initialize the completer with Manim keywords.

        Args:
            parent: Parent widget, typically the code editor.
        """
        super().__init__(parent)

        # Load all keywords
        self._keywords = self._load_all_keywords()

        # Set up the model
        self._model = QStandardItemModel(self)
        self._populate_model()
        self.setModel(self._model)

        # Configure completer behavior
        self.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.setFilterMode(Qt.MatchFlag.MatchContains)
        self.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self.setMaxVisibleItems(10)

        # Current prefix for completion
        self._current_prefix = ""

    def _load_all_keywords(self) -> List[str]:
        """Load all keywords from the JSON resource file.

        Returns:
            Sorted list of all unique keywords.
        """
        keywords_path = (
            Path(__file__).parent.parent.parent.parent / "resources" / "manim_keywords.json"
        )

        all_keywords = []

        try:
            with open(keywords_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Combine all keyword categories
            for category in [
                "python_keywords",
                "manim_classes",
                "manim_animations",
                "manim_methods",
                "manim_constants",
            ]:
                all_keywords.extend(data.get(category, []))

            # Add common Python builtins
            builtins = [
                "print", "len", "range", "str", "int", "float", "list", "dict", "tuple",
                "set", "bool", "type", "isinstance", "super", "property", "staticmethod",
                "classmethod", "enumerate", "zip", "map", "filter", "abs", "min", "max",
                "sum", "sorted", "reversed", "any", "all", "open", "round", "pow"
            ]
            all_keywords.extend(builtins)

        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Warning: Could not load manim_keywords.json: {e}")

        # Remove duplicates and sort
        return sorted(set(all_keywords))

    def _populate_model(self) -> None:
        """Populate the model with all keywords."""
        for keyword in self._keywords:
            item = QStandardItem(keyword)
            self._model.appendRow(item)

    def update_prefix(self, prefix: str) -> None:
        """Update the completion prefix.

        Args:
            prefix: The current word prefix being typed.
        """
        self._current_prefix = prefix
        self.setCompletionPrefix(prefix)

    def _insert_completion(self, editor: QPlainTextEdit, completion: str) -> None:
        """Insert the selected completion into the editor.

        Args:
            editor: The code editor widget.
            completion: The completion text to insert.
        """
        cursor = editor.textCursor()

        # Remove the current prefix
        for _ in range(len(self._current_prefix)):
            cursor.deletePreviousChar()

        # Insert the completion
        cursor.insertText(completion)
        editor.setTextCursor(cursor)

    def get_keywords(self) -> List[str]:
        """Get the list of all keywords.

        Returns:
            List of all keywords loaded by the completer.
        """
        return self._keywords.copy()
