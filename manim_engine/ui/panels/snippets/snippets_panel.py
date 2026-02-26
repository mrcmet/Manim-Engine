"""Dock widget panel for managing and inserting code snippets."""

from PySide6.QtWidgets import (
    QDockWidget,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QMessageBox,
)
from PySide6.QtCore import Signal, Qt, QPoint

from core.services.snippets_service import SnippetsService
from .snippet_list_widget import SnippetListWidget
from .snippet_code_popup import SnippetCodePopup
from .snippet_editor_dialog import SnippetEditorDialog


class SnippetsPanel(QDockWidget):
    """QDockWidget that lists saved Manim code snippets.

    Users can create, edit, delete, and insert snippets into the code
    editor from this panel.  Hovering over a list item shows a read-only
    popup preview of the snippet code.

    Signals:
        snippet_insert_requested(str): Emitted with the **full code text**
            of the snippet the user wants to insert.

    Args:
        snippets_service: Injected service for snippet persistence.
        parent: Parent widget.
    """

    snippet_insert_requested = Signal(str)

    def __init__(
        self, snippets_service: SnippetsService, parent=None
    ) -> None:
        super().__init__("Snippets", parent)
        self.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetMovable
            | QDockWidget.DockWidgetFeature.DockWidgetFloatable
            | QDockWidget.DockWidgetFeature.DockWidgetClosable
        )
        self._service = snippets_service

        self._build_ui()
        self._wire_signals()
        self._install_hover_popup()
        self._refresh_list()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def apply_theme(self, theme: dict) -> None:
        """Propagate theme to child widgets that support it.

        Args:
            theme: Theme dictionary from :class:`~ui.theme.ThemeManager`.
        """
        self._popup.apply_theme(theme)

    # ------------------------------------------------------------------
    # Private — UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        main_widget = QWidget()
        layout = QVBoxLayout(main_widget)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # Toolbar
        toolbar = QHBoxLayout()
        toolbar.setSpacing(4)

        self._new_btn = QPushButton("New Snippet")
        self._new_btn.clicked.connect(self._on_new)
        toolbar.addWidget(self._new_btn)

        self._insert_btn = QPushButton("Insert")
        self._insert_btn.setEnabled(False)
        self._insert_btn.clicked.connect(self._on_insert)
        toolbar.addWidget(self._insert_btn)

        toolbar.addStretch()
        layout.addLayout(toolbar)

        # Snippet list
        self._list = SnippetListWidget()
        layout.addWidget(self._list)

        self.setWidget(main_widget)

        # Hover popup (child of the main widget so it floats over it)
        self._popup = SnippetCodePopup(main_widget)

    def _wire_signals(self) -> None:
        self._list.currentItemChanged.connect(self._on_selection_changed)
        self._list.snippet_insert_requested.connect(self._on_insert_by_id)
        self._list.snippet_edit_requested.connect(self._on_edit)
        self._list.snippet_delete_requested.connect(self._on_delete)

    # ------------------------------------------------------------------
    # Private — hover popup via monkey-patched events
    # ------------------------------------------------------------------

    def _install_hover_popup(self) -> None:
        """Monkey-patch mouseMoveEvent and leaveEvent on the list widget."""
        _orig_mouse_move = self._list.mouseMoveEvent
        _orig_leave = self._list.leaveEvent

        def _patched_mouse_move(event, _orig=_orig_mouse_move):
            item = self._list.itemAt(event.pos())
            if item is not None:
                snippet_id = item.data(Qt.ItemDataRole.UserRole)
                snippet = self._service.get(snippet_id)
                if snippet is not None:
                    # Position popup to the right of the list widget
                    global_pt = self._list.mapToGlobal(
                        QPoint(self._list.width() + 4, event.pos().y())
                    )
                    self._popup.show_snippet(snippet.name, snippet.code, global_pt)
                else:
                    self._popup.hide()
            else:
                self._popup.hide()
            _orig(event)

        def _patched_leave(event, _orig=_orig_leave):
            self._popup.hide()
            _orig(event)

        self._list.mouseMoveEvent = _patched_mouse_move
        self._list.leaveEvent = _patched_leave

    # ------------------------------------------------------------------
    # Private — list management
    # ------------------------------------------------------------------

    def _refresh_list(self) -> None:
        """Reload snippets from the service and repopulate the list."""
        snippets = self._service.load()
        self._list.set_snippets(snippets)
        self._update_insert_btn()

    def _on_selection_changed(self) -> None:
        self._update_insert_btn()

    def _update_insert_btn(self) -> None:
        self._insert_btn.setEnabled(self._list.current_snippet_id() is not None)

    # ------------------------------------------------------------------
    # Private — CRUD handlers
    # ------------------------------------------------------------------

    def _on_new(self) -> None:
        dialog = SnippetEditorDialog(parent=self)
        if dialog.exec():
            name, code, description = dialog.get_values()
            self._service.add(name, code, description or None)
            self._refresh_list()

    def _on_edit(self, snippet_id: str) -> None:
        snippet = self._service.get(snippet_id)
        if snippet is None:
            return
        dialog = SnippetEditorDialog(snippet=snippet, parent=self)
        if dialog.exec():
            name, code, description = dialog.get_values()
            self._service.update(snippet_id, name, code, description or None)
            self._refresh_list()

    def _on_delete(self, snippet_id: str) -> None:
        snippet = self._service.get(snippet_id)
        if snippet is None:
            return
        reply = QMessageBox.question(
            self,
            "Delete Snippet",
            f"Delete '{snippet.name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._service.delete(snippet_id)
            self._popup.hide()
            self._refresh_list()

    def _on_insert(self) -> None:
        snippet_id = self._list.current_snippet_id()
        if snippet_id:
            self._on_insert_by_id(snippet_id)

    def _on_insert_by_id(self, snippet_id: str) -> None:
        snippet = self._service.get(snippet_id)
        if snippet is not None:
            self.snippet_insert_requested.emit(snippet.code)
