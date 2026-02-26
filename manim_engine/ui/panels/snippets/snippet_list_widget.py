"""QListWidget subclass for displaying and interacting with code snippets."""

from PySide6.QtWidgets import QListWidget, QListWidgetItem, QMenu
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QAction

from core.models.snippet import Snippet


class SnippetListWidget(QListWidget):
    """List widget that shows snippets and exposes CRUD signals.

    Each list item stores the snippet ``id`` in
    ``Qt.ItemDataRole.UserRole``.

    Signals:
        snippet_insert_requested(str): Emitted (with snippet id) when the
            user double-clicks an item or chooses "Insert" from the context
            menu.
        snippet_edit_requested(str): Emitted (with snippet id) when the
            user chooses "Edit" from the context menu.
        snippet_delete_requested(str): Emitted (with snippet id) when the
            user chooses "Delete" from the context menu.
    """

    snippet_insert_requested = Signal(str)
    snippet_edit_requested = Signal(str)
    snippet_delete_requested = Signal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setMouseTracking(True)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
        self.itemDoubleClicked.connect(self._on_double_click)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_snippets(self, snippets: list[Snippet]) -> None:
        """Repopulate the list with the given snippets.

        Args:
            snippets: Snippets to display, in the order provided.
        """
        self.clear()
        for snippet in snippets:
            item = QListWidgetItem(snippet.name)
            item.setData(Qt.ItemDataRole.UserRole, snippet.id)
            self.addItem(item)

    def current_snippet_id(self) -> str | None:
        """Return the id of the currently selected snippet, or ``None``."""
        item = self.currentItem()
        if item is None:
            return None
        return item.data(Qt.ItemDataRole.UserRole)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _on_double_click(self, item: QListWidgetItem) -> None:
        snippet_id = item.data(Qt.ItemDataRole.UserRole)
        if snippet_id:
            self.snippet_insert_requested.emit(snippet_id)

    def _show_context_menu(self, position) -> None:
        item = self.itemAt(position)
        if item is None:
            return
        snippet_id = item.data(Qt.ItemDataRole.UserRole)
        if not snippet_id:
            return

        menu = QMenu(self)

        insert_action = QAction("Insert", self)
        insert_action.triggered.connect(
            lambda: self.snippet_insert_requested.emit(snippet_id)
        )
        menu.addAction(insert_action)

        edit_action = QAction("Edit", self)
        edit_action.triggered.connect(
            lambda: self.snippet_edit_requested.emit(snippet_id)
        )
        menu.addAction(edit_action)

        menu.addSeparator()

        delete_action = QAction("Delete", self)
        delete_action.triggered.connect(
            lambda: self.snippet_delete_requested.emit(snippet_id)
        )
        menu.addAction(delete_action)

        menu.exec(self.mapToGlobal(position))
