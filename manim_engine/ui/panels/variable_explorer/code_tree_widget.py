"""Tree widget displaying parsed code structure for the Code Explorer panel."""

from PySide6.QtWidgets import QTreeWidget, QTreeWidgetItem, QAbstractItemView
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QFont, QColor, QBrush

from core.models.code_structure import ClassNode


# Catppuccin Mocha palette colours
_COLOR_CLASS = "#b4befe"    # lavender
_COLOR_METHOD = "#89b4fa"   # blue
_COLOR_FIELD = "#a6adc8"    # subtext0

# Max chars of value_str shown inline; full value lives in the tooltip
_MAX_VALUE_DISPLAY = 30


class CodeTreeWidget(QTreeWidget):
    """QTreeWidget showing class → method → field hierarchy.

    Emits navigate_to_line(int) when an item is clicked.
    Line numbers are shown in item tooltips rather than a second column so the
    label column gets the full available width.
    """

    navigate_to_line = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setColumnCount(1)
        self.setHeaderHidden(True)
        self.header().setStretchLastSection(True)

        self.setIndentation(12)
        self.setAnimated(True)
        self.setWordWrap(False)
        self.setUniformRowHeights(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)

        self.itemClicked.connect(self._on_item_clicked)

        self._bold_font = QFont()
        self._bold_font.setBold(True)

        self._normal_font = QFont()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_code_structure(self, classes: list[ClassNode]) -> None:
        """Rebuild the tree from a list of ClassNode objects.

        Args:
            classes: Parsed class nodes from CodeParser.
        """
        self.clear()

        for cls in classes:
            # ---- Class row ----
            base_str = f"({', '.join(cls.base_names)})" if cls.base_names else ""
            cls_label = f"{cls.name} {base_str}" if base_str else cls.name
            cls_item = QTreeWidgetItem([cls_label])
            cls_item.setData(0, Qt.ItemDataRole.UserRole, cls.line_number)
            cls_item.setFont(0, self._bold_font)
            cls_item.setForeground(0, QBrush(QColor(_COLOR_CLASS)))
            cls_item.setToolTip(
                0,
                f"Line {cls.line_number} — class {cls.name}"
                + (f"({', '.join(cls.base_names)})" if cls.base_names else ""),
            )
            self.addTopLevelItem(cls_item)

            for method in cls.methods:
                # ---- Method row ----
                m_item = QTreeWidgetItem([f"def {method.name}(…)"])
                m_item.setData(0, Qt.ItemDataRole.UserRole, method.line_number)
                m_item.setFont(0, self._normal_font)
                m_item.setForeground(0, QBrush(QColor(_COLOR_METHOD)))
                m_item.setToolTip(0, f"Line {method.line_number} — def {method.name}(…)")
                cls_item.addChild(m_item)

                for field in method.fields:
                    # ---- Field row ----
                    display_val = (
                        field.value_str[:_MAX_VALUE_DISPLAY] + "…"
                        if len(field.value_str) > _MAX_VALUE_DISPLAY
                        else field.value_str
                    )
                    label = f"{field.name} = {display_val}"
                    f_item = QTreeWidgetItem([label])
                    f_item.setData(0, Qt.ItemDataRole.UserRole, field.line_number)
                    f_item.setFont(0, self._normal_font)
                    f_item.setForeground(0, QBrush(QColor(_COLOR_FIELD)))
                    f_item.setToolTip(
                        0, f"Line {field.line_number} — {field.name} = {field.value_str}"
                    )
                    m_item.addChild(f_item)

                m_item.setExpanded(True)

            cls_item.setExpanded(True)

    # ------------------------------------------------------------------
    # Private slots
    # ------------------------------------------------------------------

    def _on_item_clicked(self, item: QTreeWidgetItem, column: int) -> None:
        line = item.data(0, Qt.ItemDataRole.UserRole)
        if line is not None:
            self.navigate_to_line.emit(int(line))
