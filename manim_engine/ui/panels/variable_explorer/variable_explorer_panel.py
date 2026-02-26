"""Code Explorer panel — displays class/method/field tree from parsed source."""

from PySide6.QtWidgets import (
    QDockWidget,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
)
from PySide6.QtCore import Signal

from .code_tree_widget import CodeTreeWidget
from core.models.code_structure import ClassNode


class VariableExplorerPanel(QDockWidget):
    """Dock widget showing a tree of classes, methods, and variable assignments.

    Clicking any tree node emits navigate_to_line so the code editor can
    move its cursor to the corresponding source line.
    """

    # Forwarded from CodeTreeWidget — connected externally via property
    refresh_requested = Signal()

    def __init__(self, parent=None):
        super().__init__("Code Explorer", parent)
        self.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetMovable
            | QDockWidget.DockWidgetFeature.DockWidgetFloatable
            | QDockWidget.DockWidgetFeature.DockWidgetClosable
        )

        main_widget = QWidget()
        layout = QVBoxLayout(main_widget)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # Toolbar
        toolbar_layout = QHBoxLayout()
        toolbar_layout.setSpacing(4)

        self._refresh_btn = QPushButton("Refresh")
        self._refresh_btn.clicked.connect(self.refresh_requested)
        toolbar_layout.addWidget(self._refresh_btn)
        toolbar_layout.addStretch()

        layout.addLayout(toolbar_layout)

        # Code tree
        self._tree = CodeTreeWidget()
        layout.addWidget(self._tree)

        self.setWidget(main_widget)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def navigate_to_line(self) -> Signal:
        """Signal(int) emitted when the user clicks a tree node.

        Returns:
            The navigate_to_line signal from the underlying CodeTreeWidget.
        """
        return self._tree.navigate_to_line

    def set_code_structure(self, classes: list[ClassNode]) -> None:
        """Update the tree to reflect the given parsed class structure.

        Args:
            classes: List of ClassNode objects from CodeParser.
        """
        self._tree.set_code_structure(classes)
