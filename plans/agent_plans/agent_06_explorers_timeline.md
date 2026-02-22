# Agent 6: Project Explorer, Variable Explorer & Version Timeline

## Scope
Build the three "data navigation" panels: the collapsible project explorer, the editable variable explorer table, and the visual version timeline strip.

## Files to Create

```
manim_engine/
└── ui/
    └── panels/
        ├── project_explorer/
        │   ├── __init__.py
        │   ├── project_explorer_panel.py
        │   └── project_list_widget.py
        ├── variable_explorer/
        │   ├── __init__.py
        │   ├── variable_explorer_panel.py
        │   ├── variable_table_widget.py
        │   └── variable_delegate.py
        └── version_timeline/
            ├── __init__.py
            ├── timeline_panel.py
            ├── timeline_widget.py
            └── timeline_model.py
└── tests/
    └── test_ui/
        ├── test_project_explorer.py
        ├── test_variable_explorer.py
        └── test_timeline.py
```

---

## Detailed Specifications

### Project Explorer

#### `project_list_widget.py`

```python
from PySide6.QtWidgets import QListWidget, QListWidgetItem, QMenu
from PySide6.QtCore import Signal

class ProjectListWidget(QListWidget):
    """List of projects with right-click context menu."""

    project_selected = Signal(str)   # project_id
    project_delete_requested = Signal(str)
    project_rename_requested = Signal(str, str)  # id, new_name

    def __init__(self):
        super().__init__()
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
        self.itemClicked.connect(self._on_item_clicked)

    def set_projects(self, projects: list):
        """Populate list. Each project has .id, .name, .updated_at."""
        self.clear()
        for proj in projects:
            item = QListWidgetItem()
            item.setText(f"{proj.name}\n{proj.updated_at.strftime('%Y-%m-%d %H:%M')}")
            item.setData(Qt.UserRole, proj.id)
            self.addItem(item)

    def _on_item_clicked(self, item):
        self.project_selected.emit(item.data(Qt.UserRole))

    def _show_context_menu(self, pos):
        item = self.itemAt(pos)
        if not item:
            return
        menu = QMenu(self)
        menu.addAction("Open", lambda: self.project_selected.emit(item.data(Qt.UserRole)))
        menu.addAction("Rename", lambda: self._rename_project(item))
        menu.addAction("Delete", lambda: self.project_delete_requested.emit(item.data(Qt.UserRole)))
        menu.exec(self.mapToGlobal(pos))
```

#### `project_explorer_panel.py`

```python
class ProjectExplorerPanel(QDockWidget):
    """Collapsible project explorer on the right side."""

    def __init__(self):
        super().__init__("Projects")
        self.setObjectName("project_explorer_panel")
        self.setFeatures(QDockWidget.DockWidgetClosable |
                         QDockWidget.DockWidgetMovable |
                         QDockWidget.DockWidgetFloatable)

        container = QWidget()
        layout = QVBoxLayout(container)

        # New project button
        self._new_btn = QPushButton("+ New Project")
        self._new_btn.clicked.connect(self.new_project_requested)

        # Search filter
        self._search = QLineEdit()
        self._search.setPlaceholderText("Search projects...")
        self._search.textChanged.connect(self._filter_projects)

        # Project list
        self._list = ProjectListWidget()

        layout.addWidget(self._new_btn)
        layout.addWidget(self._search)
        layout.addWidget(self._list)
        self.setWidget(container)

    new_project_requested = Signal()

    # Public interface:
    def refresh_projects(self, projects: list):
        self._list.set_projects(projects)

    @property
    def project_selected(self): return self._list.project_selected
    @property
    def project_delete_requested(self): return self._list.project_delete_requested

    def _filter_projects(self, text):
        for i in range(self._list.count()):
            item = self._list.item(i)
            item.setHidden(text.lower() not in item.text().lower())
```

---

### Variable Explorer

#### `variable_table_widget.py`

```python
from PySide6.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView
from PySide6.QtCore import Signal

class VariableTableWidget(QTableWidget):
    """Editable table showing variables extracted from Manim code."""

    variable_edited = Signal(str, object)  # (var_name, new_value)

    def __init__(self):
        super().__init__()
        self.setColumnCount(3)
        self.setHorizontalHeaderLabels(["Variable", "Value", "Type"])
        self.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.verticalHeader().setVisible(False)
        self.setSelectionBehavior(QTableWidget.SelectRows)

        self._variables: list = []  # list of VariableInfo
        self.cellChanged.connect(self._on_cell_changed)

    def set_variables(self, variables: list):
        """Populate table from list of VariableInfo objects."""
        self.blockSignals(True)
        self.setRowCount(len(variables))
        self._variables = variables
        for row, var in enumerate(variables):
            # Name column (read-only)
            name_item = QTableWidgetItem(var.name)
            name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
            self.setItem(row, 0, name_item)

            # Value column (editable if var.editable)
            value_item = QTableWidgetItem(str(var.value))
            if not var.editable:
                value_item.setFlags(value_item.flags() & ~Qt.ItemIsEditable)
            self.setItem(row, 1, value_item)

            # Type column (read-only)
            type_item = QTableWidgetItem(var.var_type)
            type_item.setFlags(type_item.flags() & ~Qt.ItemIsEditable)
            self.setItem(row, 2, type_item)

            # Use custom delegate for special types
        self.blockSignals(False)

    def _on_cell_changed(self, row, col):
        if col != 1:  # only value column
            return
        var = self._variables[row]
        new_text = self.item(row, 1).text()
        try:
            new_value = self._parse_value(new_text, var.var_type)
            self.variable_edited.emit(var.name, new_value)
        except ValueError:
            # Revert to original value
            self.blockSignals(True)
            self.item(row, 1).setText(str(var.value))
            self.blockSignals(False)

    def _parse_value(self, text: str, var_type: str):
        """Parse string input to the appropriate Python type."""
        if var_type == "int":
            return int(text)
        elif var_type == "float":
            return float(text)
        elif var_type == "bool":
            return text.lower() in ("true", "1", "yes")
        elif var_type == "str":
            return text
        elif var_type == "tuple":
            return tuple(float(x.strip()) for x in text.strip("()").split(","))
        else:
            return text
```

#### `variable_delegate.py`

```python
from PySide6.QtWidgets import QStyledItemDelegate, QSpinBox, QDoubleSpinBox, QColorDialog

class VariableDelegate(QStyledItemDelegate):
    """Custom editing delegates for specific variable types."""

    def createEditor(self, parent, option, index):
        var_type = index.sibling(index.row(), 2).data()
        var_name = index.sibling(index.row(), 0).data()

        if var_type == "int":
            editor = QSpinBox(parent)
            editor.setRange(-10000, 10000)
            return editor
        elif var_type == "float":
            editor = QDoubleSpinBox(parent)
            editor.setRange(-10000.0, 10000.0)
            editor.setDecimals(3)
            return editor
        elif "color" in var_name.lower():
            # Open color picker dialog
            color = QColorDialog.getColor()
            if color.isValid():
                # Set value directly since dialog is modal
                model = index.model()
                model.setData(index, f'"{color.name()}"')
            return None  # No persistent editor needed
        else:
            return super().createEditor(parent, option, index)
```

#### `variable_explorer_panel.py`

```python
class VariableExplorerPanel(QDockWidget):
    """Dockable variable explorer panel."""

    def __init__(self):
        super().__init__("Variables")
        self.setObjectName("variable_explorer_panel")

        container = QWidget()
        layout = QVBoxLayout(container)

        self._refresh_btn = QPushButton("Refresh Variables")
        self._table = VariableTableWidget()
        self._table.setItemDelegateForColumn(1, VariableDelegate(self._table))

        layout.addWidget(self._refresh_btn)
        layout.addWidget(self._table)
        self.setWidget(container)

    # Public interface:
    def set_variables(self, variables: list):
        self._table.set_variables(variables)

    @property
    def variable_edited(self): return self._table.variable_edited

    @property
    def refresh_requested(self): return self._refresh_btn.clicked
```

---

### Version Timeline

#### `timeline_model.py`

```python
from dataclasses import dataclass

@dataclass
class TimelineNode:
    version_id: str
    label: str          # short label, e.g. "v1", "v2"
    source: str         # "ai", "manual_edit", "variable_tweak"
    timestamp: str      # formatted time
    prompt_snippet: str | None  # first 50 chars of prompt
    has_video: bool
    is_current: bool

class TimelineModel:
    """Data model backing the timeline widget."""

    def __init__(self):
        self._nodes: list[TimelineNode] = []
        self._current_id: str | None = None

    def set_versions(self, versions: list) -> list[TimelineNode]:
        """Convert Version objects to TimelineNodes."""
        self._nodes = []
        for i, v in enumerate(versions):
            node = TimelineNode(
                version_id=v.id,
                label=f"v{i + 1}",
                source=v.source,
                timestamp=v.created_at.strftime("%H:%M:%S"),
                prompt_snippet=(v.prompt[:50] + "...") if v.prompt else None,
                has_video=v.video_path is not None,
                is_current=(v.id == self._current_id),
            )
            self._nodes.append(node)
        return self._nodes

    def set_current(self, version_id: str):
        self._current_id = version_id
        for node in self._nodes:
            node.is_current = (node.version_id == version_id)

    @property
    def nodes(self) -> list[TimelineNode]:
        return self._nodes
```

#### `timeline_widget.py`

```python
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Signal, Qt, QRect, QPoint
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QFontMetrics

class TimelineWidget(QWidget):
    """Custom-painted horizontal timeline with clickable version nodes.

    Visual design:
        [v1]---[v2]---[v3]---[v4*]
                                ^ current (highlighted ring)

    Node colors by source:
        - ai: #89b4fa (blue)
        - manual_edit: #a6e3a1 (green)
        - variable_tweak: #fab387 (orange)

    Current version: extra highlight ring in white
    Hover: tooltip with timestamp + prompt snippet
    Click: emits version_selected signal
    Horizontal scrolling if many nodes
    """

    version_selected = Signal(str)  # version_id

    NODE_RADIUS = 14
    NODE_SPACING = 60
    LINE_Y = 35
    COLORS = {
        "ai": QColor("#89b4fa"),
        "manual_edit": QColor("#a6e3a1"),
        "variable_tweak": QColor("#fab387"),
    }

    def __init__(self):
        super().__init__()
        self._model = TimelineModel()
        self._hovered_index = -1
        self.setMinimumHeight(70)
        self.setMaximumHeight(80)
        self.setMouseTracking(True)

    def set_model(self, model: TimelineModel):
        self._model = model
        self._update_size()
        self.update()

    def set_versions(self, versions: list):
        self._model.set_versions(versions)
        self._update_size()
        self.update()

    def add_version(self, version):
        """Convenience: append a single version and repaint."""
        # Add to model's internal list and repaint
        ...

    def select_version(self, version_id: str):
        self._model.set_current(version_id)
        self.update()

    def _update_size(self):
        width = max(200, len(self._model.nodes) * self.NODE_SPACING + 40)
        self.setMinimumWidth(width)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        nodes = self._model.nodes
        if not nodes:
            painter.setPen(QColor("#6c7086"))
            painter.drawText(self.rect(), Qt.AlignCenter, "No versions yet")
            return

        # Draw connecting line
        x_start = 30
        x_end = x_start + (len(nodes) - 1) * self.NODE_SPACING
        painter.setPen(QPen(QColor("#45475a"), 2))
        painter.drawLine(x_start, self.LINE_Y, x_end, self.LINE_Y)

        # Draw nodes
        for i, node in enumerate(nodes):
            x = x_start + i * self.NODE_SPACING
            color = self.COLORS.get(node.source, QColor("#cdd6f4"))

            # Node circle
            painter.setBrush(QBrush(color))
            painter.setPen(QPen(color.darker(120), 2))
            painter.drawEllipse(QPoint(x, self.LINE_Y), self.NODE_RADIUS, self.NODE_RADIUS)

            # Current version highlight ring
            if node.is_current:
                painter.setBrush(Qt.NoBrush)
                painter.setPen(QPen(QColor("#ffffff"), 3))
                painter.drawEllipse(QPoint(x, self.LINE_Y),
                                    self.NODE_RADIUS + 4, self.NODE_RADIUS + 4)

            # Label
            painter.setPen(QColor("#cdd6f4"))
            painter.setFont(QFont("sans-serif", 9))
            painter.drawText(QRect(x - 20, self.LINE_Y + 18, 40, 20),
                             Qt.AlignCenter, node.label)

            # Hover highlight
            if i == self._hovered_index:
                painter.setBrush(QBrush(QColor(255, 255, 255, 40)))
                painter.setPen(Qt.NoPen)
                painter.drawEllipse(QPoint(x, self.LINE_Y),
                                    self.NODE_RADIUS + 2, self.NODE_RADIUS + 2)

    def mousePressEvent(self, event):
        idx = self._hit_test(event.pos())
        if idx >= 0:
            node = self._model.nodes[idx]
            self.version_selected.emit(node.version_id)

    def mouseMoveEvent(self, event):
        idx = self._hit_test(event.pos())
        if idx != self._hovered_index:
            self._hovered_index = idx
            self.update()
            if idx >= 0:
                node = self._model.nodes[idx]
                tooltip = f"{node.label} ({node.timestamp})\n{node.source}"
                if node.prompt_snippet:
                    tooltip += f"\n{node.prompt_snippet}"
                self.setToolTip(tooltip)
            else:
                self.setToolTip("")

    def _hit_test(self, pos) -> int:
        """Return index of node at pos, or -1."""
        for i, node in enumerate(self._model.nodes):
            x = 30 + i * self.NODE_SPACING
            dx = pos.x() - x
            dy = pos.y() - self.LINE_Y
            if dx * dx + dy * dy <= (self.NODE_RADIUS + 4) ** 2:
                return i
        return -1
```

#### `timeline_panel.py`

```python
class TimelinePanel(QDockWidget):
    """Dockable timeline panel at the bottom of the window."""

    def __init__(self):
        super().__init__("Version History")
        self.setObjectName("timeline_panel")
        self.setMaximumHeight(100)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        self._timeline = TimelineWidget()
        scroll.setWidget(self._timeline)
        self.setWidget(scroll)

    # Public interface:
    def set_versions(self, versions: list):
        self._timeline.set_versions(versions)

    def add_version(self, version):
        self._timeline.add_version(version)

    def select_version(self, version_id: str):
        self._timeline.select_version(version_id)

    @property
    def version_selected(self): return self._timeline.version_selected
```

---

## Tests

**`test_project_explorer.py`**:
- Test ProjectListWidget populates items from project list
- Test project_selected signal emits correct ID on click
- Test search filtering hides non-matching items

**`test_variable_explorer.py`**:
- Test VariableTableWidget populates rows from VariableInfo list
- Test editing a value emits variable_edited signal
- Test invalid value input reverts to original
- Test _parse_value for each type

**`test_timeline.py`**:
- Test TimelineModel converts versions to nodes
- Test set_current marks correct node
- Test TimelineWidget hit_test detects click on node
- Test painting doesn't crash with empty nodes

## Verification

```bash
python -m pytest tests/test_ui/test_project_explorer.py tests/test_ui/test_variable_explorer.py tests/test_ui/test_timeline.py -v

# Visual test - Timeline:
python -c "
import sys
from datetime import datetime
from PySide6.QtWidgets import QApplication
from ui.panels.version_timeline.timeline_panel import TimelinePanel
from ui.panels.version_timeline.timeline_model import TimelineNode

app = QApplication(sys.argv)
panel = TimelinePanel()

# Create mock versions (using simple objects)
class MockVersion:
    def __init__(self, id, source, prompt=None):
        self.id = id
        self.source = source
        self.prompt = prompt
        self.created_at = datetime.now()
        self.video_path = '/tmp/test.mp4'

versions = [
    MockVersion('1', 'ai', 'Create a spinning circle'),
    MockVersion('2', 'manual_edit'),
    MockVersion('3', 'variable_tweak'),
    MockVersion('4', 'ai', 'Add a bouncing square'),
]
panel.set_versions(versions)
panel.select_version('4')
panel.show()
panel.resize(600, 100)
app.exec()
"
```

## Dependencies on Other Agents
- Agent 1: `core.models.scene_code.VariableInfo` and `core.models.version.Version` dataclasses (for type hints)

## What Other Agents Need From You
- Agent 7: `ProjectExplorerPanel` with `refresh_projects()`, `project_selected` signal, `new_project_requested` signal
- Agent 7: `VariableExplorerPanel` with `set_variables()`, `variable_edited` signal
- Agent 7: `TimelinePanel` with `set_versions()`, `add_version()`, `select_version()`, `version_selected` signal
