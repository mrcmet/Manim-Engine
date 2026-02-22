"""Project Explorer panel for managing projects."""

from PySide6.QtWidgets import (
    QDockWidget,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLineEdit,
)
from PySide6.QtCore import Signal, Qt

from .project_list_widget import ProjectListWidget


class ProjectExplorerPanel(QDockWidget):
    """Dock widget for exploring and managing projects."""

    new_project_requested = Signal()

    def __init__(self, parent=None):
        """Initialize the project explorer panel.

        Args:
            parent: Parent widget
        """
        super().__init__("Projects", parent)
        self.setFeatures(
            QDockWidget.DockWidgetMovable
            | QDockWidget.DockWidgetFloatable
            | QDockWidget.DockWidgetClosable
        )

        # Main widget
        main_widget = QWidget()
        layout = QVBoxLayout(main_widget)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # Top toolbar
        toolbar_layout = QHBoxLayout()
        toolbar_layout.setSpacing(4)

        self._new_project_btn = QPushButton("New Project")
        self._new_project_btn.clicked.connect(self.new_project_requested.emit)
        toolbar_layout.addWidget(self._new_project_btn)

        toolbar_layout.addStretch()

        layout.addLayout(toolbar_layout)

        # Search bar
        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("Search projects...")
        self._search_input.textChanged.connect(self._filter_projects)
        self._search_input.setClearButtonEnabled(True)
        layout.addWidget(self._search_input)

        # Project list
        self._project_list = ProjectListWidget()
        layout.addWidget(self._project_list)

        self.setWidget(main_widget)

        # Store all projects for filtering
        self._all_projects = []

    def refresh_projects(self, projects: list):
        """Refresh the project list with new data.

        Args:
            projects: List of project objects with .id, .name, .updated_at
        """
        self._all_projects = projects
        self._apply_filter()

    def _filter_projects(self, search_text: str):
        """Filter projects based on search text.

        Args:
            search_text: Text to filter by
        """
        self._apply_filter()

    def _apply_filter(self):
        """Apply the current search filter to the project list."""
        search_text = self._search_input.text().strip().lower()

        if not search_text:
            # Show all projects
            self._project_list.set_projects(self._all_projects)
            return

        # Filter projects by name
        filtered_projects = [
            project
            for project in self._all_projects
            if search_text in project.name.lower()
        ]

        self._project_list.set_projects(filtered_projects)

    @property
    def project_selected(self) -> Signal:
        """Signal emitted when a project is selected.

        Returns:
            Signal(str) with project ID
        """
        return self._project_list.project_selected

    @property
    def project_delete_requested(self) -> Signal:
        """Signal emitted when project deletion is requested.

        Returns:
            Signal(str) with project ID
        """
        return self._project_list.project_delete_requested

    @property
    def project_rename_requested(self) -> Signal:
        """Signal emitted when project rename is requested.

        Returns:
            Signal(str, str) with project ID and new name
        """
        return self._project_list.project_rename_requested

    def get_selected_project_id(self) -> str | None:
        """Get the currently selected project ID.

        Returns:
            Project ID or None if no selection
        """
        return self._project_list.get_selected_project_id()
