"""Project list widget with context menu support."""

from PySide6.QtWidgets import QListWidget, QListWidgetItem, QMenu
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QAction, QCursor


class ProjectListWidget(QListWidget):
    """List widget displaying projects with context menu actions."""

    project_selected = Signal(str)
    project_delete_requested = Signal(str)
    project_rename_requested = Signal(str, str)

    def __init__(self, parent=None):
        """Initialize the project list widget.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
        self.itemDoubleClicked.connect(self._on_item_double_clicked)

        # Store project data
        self._project_data = {}

    def set_projects(self, projects: list):
        """Set the list of projects to display.

        Args:
            projects: List of project objects with .id, .name, .updated_at attributes
        """
        self.clear()
        self._project_data.clear()

        if not projects:
            return

        # Sort projects by updated_at descending (most recent first)
        sorted_projects = sorted(
            projects, key=lambda p: p.updated_at, reverse=True
        )

        for project in sorted_projects:
            item = QListWidgetItem(project.name)
            item.setData(Qt.UserRole, project.id)
            self.addItem(item)
            self._project_data[project.id] = project

    def _on_item_double_clicked(self, item: QListWidgetItem):
        """Handle double-click to open project.

        Args:
            item: The clicked list item
        """
        project_id = item.data(Qt.UserRole)
        if project_id:
            self.project_selected.emit(project_id)

    def _show_context_menu(self, position):
        """Show context menu for project actions.

        Args:
            position: Position where the menu was requested
        """
        item = self.itemAt(position)
        if not item:
            return

        project_id = item.data(Qt.UserRole)
        if not project_id:
            return

        menu = QMenu(self)

        open_action = QAction("Open", self)
        open_action.triggered.connect(lambda: self.project_selected.emit(project_id))
        menu.addAction(open_action)

        rename_action = QAction("Rename", self)
        rename_action.triggered.connect(lambda: self._request_rename(project_id, item))
        menu.addAction(rename_action)

        menu.addSeparator()

        delete_action = QAction("Delete", self)
        delete_action.triggered.connect(lambda: self.project_delete_requested.emit(project_id))
        menu.addAction(delete_action)

        menu.exec_(QCursor.pos())

    def _request_rename(self, project_id: str, item: QListWidgetItem):
        """Request rename for a project.

        Args:
            project_id: ID of the project to rename
            item: The list item to edit
        """
        old_name = item.text()
        self.editItem(item)

        # Connect to itemChanged to capture the new name
        def on_item_changed(changed_item):
            if changed_item == item:
                new_name = changed_item.text().strip()
                if new_name and new_name != old_name:
                    self.project_rename_requested.emit(project_id, new_name)
                else:
                    # Revert if empty or unchanged
                    changed_item.setText(old_name)
                self.itemChanged.disconnect(on_item_changed)

        self.itemChanged.connect(on_item_changed)

    def get_selected_project_id(self) -> str | None:
        """Get the currently selected project ID.

        Returns:
            Project ID or None if no selection
        """
        current_item = self.currentItem()
        if current_item:
            return current_item.data(Qt.UserRole)
        return None
