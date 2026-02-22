"""Variable Explorer panel for viewing and editing animation variables."""

from PySide6.QtWidgets import (
    QDockWidget,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
)
from PySide6.QtCore import Signal

from .variable_table_widget import VariableTableWidget, VariableInfo
from .variable_delegate import VariableDelegate


class VariableExplorerPanel(QDockWidget):
    """Dock widget for exploring and editing animation variables."""

    def __init__(self, parent=None):
        """Initialize the variable explorer panel.

        Args:
            parent: Parent widget
        """
        super().__init__("Variables", parent)
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

        # Toolbar
        toolbar_layout = QHBoxLayout()
        toolbar_layout.setSpacing(4)

        self._refresh_btn = QPushButton("Refresh")
        self._refresh_btn.clicked.connect(self._on_refresh_clicked)
        toolbar_layout.addWidget(self._refresh_btn)

        toolbar_layout.addStretch()

        layout.addLayout(toolbar_layout)

        # Variable table
        self._variable_table = VariableTableWidget()

        # Set custom delegate for column 1 (value column)
        self._delegate = VariableDelegate()
        self._variable_table.setItemDelegateForColumn(1, self._delegate)

        layout.addWidget(self._variable_table)

        self.setWidget(main_widget)

        # Track refresh requested signal
        self._refresh_requested_signal = Signal()

    def set_variables(self, variables: list[VariableInfo]):
        """Set the variables to display.

        Args:
            variables: List of VariableInfo objects
        """
        self._variable_table.set_variables(variables)

    @property
    def variable_edited(self) -> Signal:
        """Signal emitted when a variable is edited.

        Returns:
            Signal(str, object) with variable name and new value
        """
        return self._variable_table.variable_edited

    @property
    def refresh_requested(self) -> Signal:
        """Signal emitted when refresh is requested.

        Returns:
            Signal with no arguments
        """
        # Create a proper signal if it doesn't exist
        if not hasattr(self, '_refresh_requested_signal_obj'):
            from PySide6.QtCore import QObject

            class RefreshSignalEmitter(QObject):
                refresh_requested = Signal()

            self._refresh_requested_signal_obj = RefreshSignalEmitter()

        return self._refresh_requested_signal_obj.refresh_requested

    def _on_refresh_clicked(self):
        """Handle refresh button click."""
        if hasattr(self, '_refresh_requested_signal_obj'):
            self._refresh_requested_signal_obj.refresh_requested.emit()
