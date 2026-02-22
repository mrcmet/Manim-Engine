# Agent 4: Code Editor Panel

## Scope
Build a full-featured code editor panel with Python/Manim syntax highlighting, line numbers, current-line highlight, basic autocomplete, and a toolbar with run/format buttons. Font and color scheme must be customizable.

## Files to Create

```
manim_engine/
├── ui/
│   ├── __init__.py
│   └── panels/
│       ├── __init__.py
│       └── code_editor/
│           ├── __init__.py
│           ├── code_editor_panel.py
│           ├── editor_widget.py
│           ├── python_highlighter.py
│           ├── manim_completer.py
│           └── editor_toolbar.py
├── resources/
│   └── manim_keywords.json
└── tests/
    └── test_ui/
        ├── __init__.py
        └── test_code_editor.py
```

---

## Detailed Specifications

### `editor_widget.py` — Core Editor (QPlainTextEdit subclass)

This is the most complex file. Implements:

**Line Number Gutter:**
```python
class LineNumberArea(QWidget):
    """Painted in the left margin of the editor."""
    def __init__(self, editor):
        super().__init__(editor)
        self._editor = editor

    def paintEvent(self, event):
        self._editor.line_number_area_paint_event(event)

    def sizeHint(self):
        return QSize(self._editor.line_number_area_width(), 0)
```

**Editor Widget:**
```python
class CodeEditorWidget(QPlainTextEdit):
    code_changed = Signal(str)
    run_requested = Signal(str)

    def __init__(self):
        super().__init__()
        self._line_number_area = LineNumberArea(self)
        self._highlighter = PythonManimHighlighter(self.document())
        self._completer = ManimCompleter(self)

        # Setup
        self.setTabStopDistance(self.fontMetrics().horizontalAdvance(' ') * 4)
        self.setLineWrapMode(QPlainTextEdit.NoWrap)

        # Signals
        self.blockCountChanged.connect(self._update_line_number_width)
        self.updateRequest.connect(self._update_line_number_area)
        self.cursorPositionChanged.connect(self._highlight_current_line)
        self.textChanged.connect(lambda: self.code_changed.emit(self.toPlainText()))

    def line_number_area_width(self) -> int:
        digits = len(str(max(1, self.blockCount())))
        return 10 + self.fontMetrics().horizontalAdvance('9') * digits

    def line_number_area_paint_event(self, event):
        """Paint line numbers in the gutter area."""
        # QPainter draws numbers right-aligned for each visible block

    def _highlight_current_line(self):
        """Highlight the line where the cursor is."""
        selections = []
        selection = QTextEdit.ExtraSelection()
        selection.format.setBackground(QColor("#2a2a3a"))  # themed
        selection.format.setProperty(QTextFormat.FullWidthSelection, True)
        selection.cursor = self.textCursor()
        selection.cursor.clearSelection()
        selections.append(selection)
        self.setExtraSelections(selections)

    def keyPressEvent(self, event):
        """Handle Tab (insert spaces), Enter (auto-indent), and completer."""
        # Tab → insert spaces (tab_width)
        # Enter → copy leading whitespace from previous line
        # Ctrl+Space → trigger completer
        # If completer popup visible, delegate navigation keys to it
        ...

    def set_font_family(self, family: str): ...
    def set_font_size(self, size: int): ...
    def set_theme(self, theme: dict):
        """Apply theme dict with keys: background, text, current_line,
        gutter_bg, gutter_text, keyword, string, comment, number,
        manim_class, decorator, function."""
        ...
```

### `python_highlighter.py` — Syntax Highlighting

```python
from PySide6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QFont
import re

class PythonManimHighlighter(QSyntaxHighlighter):
    """Regex-based syntax highlighter for Python + Manim keywords."""

    def __init__(self, document):
        super().__init__(document)
        self._rules: list[tuple[re.Pattern, QTextCharFormat]] = []
        self._theme = {}  # set via set_theme()
        self._build_rules()

    def _build_rules(self):
        """Create highlighting rules for:
        1. Python keywords (def, class, if, else, for, while, return, import, from, etc.)
        2. Python builtins (print, len, range, True, False, None, etc.)
        3. Manim classes (Scene, Mobject, Circle, Square, Text, MathTex,
           Arrow, Line, Dot, VGroup, Animation, etc.)
        4. Manim methods (play, wait, add, remove, Create, FadeIn, FadeOut,
           Transform, MoveToTarget, Write, etc.)
        5. Decorators (@)
        6. Numbers (int, float, hex)
        7. Strings (single/double/triple quoted)
        8. Comments (# to end of line)
        9. self keyword
        10. Function/method names (word before parenthesis)
        """

    def set_theme(self, theme: dict):
        """Update colors and rebuild rules. Theme keys:
        keyword, builtin, manim_class, manim_method, decorator,
        number, string, comment, self_keyword, function."""
        self._theme = theme
        self._build_rules()
        self.rehighlight()

    def highlightBlock(self, text: str):
        """Apply regex rules in order. Handle multi-line strings with
        setCurrentBlockState/previousBlockState for triple-quoted strings."""
```

**Manim-specific keywords to highlight** (load from `resources/manim_keywords.json`):

Classes: Scene, ThreeDScene, MovingCameraScene, Mobject, VMobject, VGroup, Group, Circle, Square, Rectangle, Triangle, Line, Arrow, DoubleArrow, Dot, Arc, Ellipse, Polygon, RegularPolygon, Star, Annulus, Sector, Text, MathTex, Tex, Title, BulletedList, Code, Table, NumberPlane, Axes, ThreeDAxes, NumberLine, BarChart, Graph, SurroundingRectangle, BackgroundRectangle, Brace, BraceBetweenPoints, DecimalNumber, Integer, Variable

Animations: Create, Uncreate, FadeIn, FadeOut, Write, Unwrite, DrawBorderThenFill, ShowPassingFlash, Transform, ReplacementTransform, MoveToTarget, ApplyMethod, AnimationGroup, Succession, LaggedStart, Indicate, Flash, Circumscribe, Wiggle, ShowCreationThenFadeOut, GrowFromCenter, GrowFromEdge, GrowArrow, SpinInFromNothing, ShrinkToCenter, Rotate, ScaleInPlace, Homotopy, ComplexHomotopy

### `manim_completer.py` — Autocomplete

```python
from PySide6.QtWidgets import QCompleter
from PySide6.QtCore import Qt

class ManimCompleter(QCompleter):
    """Basic autocomplete using a static word list loaded from manim_keywords.json.

    Triggered by Ctrl+Space or automatically after typing 3+ characters.
    Popup shows matching completions filtered by prefix."""

    def __init__(self, editor: QPlainTextEdit):
        keywords = self._load_keywords()
        super().__init__(keywords)
        self.setWidget(editor)
        self.setCaseSensitivity(Qt.CaseInsensitive)
        self.setFilterMode(Qt.MatchContains)
        self.setCompletionMode(QCompleter.PopupCompletion)
        self.activated.connect(self._insert_completion)

    def _load_keywords(self) -> list[str]:
        """Load from resources/manim_keywords.json.
        Includes Python keywords + builtins + Manim classes + methods."""

    def _insert_completion(self, completion: str):
        """Insert the completion text, replacing the current word prefix."""

    def update_prefix(self, prefix: str):
        """Update the completion prefix based on current word under cursor."""
```

### `resources/manim_keywords.json`

```json
{
    "python_keywords": ["def", "class", "if", "elif", "else", "for", "while", "return",
                         "import", "from", "as", "with", "try", "except", "finally",
                         "raise", "yield", "lambda", "pass", "break", "continue",
                         "and", "or", "not", "in", "is", "True", "False", "None"],
    "manim_classes": ["Scene", "ThreeDScene", "MovingCameraScene", "Circle", "Square",
                       "Rectangle", "Line", "Arrow", "Dot", "Text", "MathTex", "Tex",
                       "VGroup", "Group", "NumberPlane", "Axes", "Mobject", "VMobject",
                       "Triangle", "Polygon", "RegularPolygon", "Star", "Arc", "Ellipse",
                       "Annulus", "Sector", "Brace", "SurroundingRectangle", "Table",
                       "BarChart", "NumberLine", "DecimalNumber", "Variable", "Code",
                       "Title", "BulletedList", "BackgroundRectangle"],
    "manim_animations": ["Create", "Uncreate", "FadeIn", "FadeOut", "Write", "Unwrite",
                          "Transform", "ReplacementTransform", "MoveToTarget", "Indicate",
                          "Flash", "Circumscribe", "Wiggle", "GrowFromCenter", "GrowArrow",
                          "Rotate", "DrawBorderThenFill", "ShowPassingFlash",
                          "AnimationGroup", "Succession", "LaggedStart", "LaggedStartMap",
                          "ApplyMethod", "ShrinkToCenter", "SpinInFromNothing"],
    "manim_methods": ["play", "wait", "add", "remove", "move_to", "next_to", "shift",
                       "scale", "rotate", "set_color", "set_fill", "set_stroke",
                       "animate", "become", "copy", "get_center", "get_width",
                       "get_height", "arrange", "to_edge", "to_corner"],
    "manim_constants": ["UP", "DOWN", "LEFT", "RIGHT", "ORIGIN", "UL", "UR", "DL", "DR",
                         "PI", "TAU", "DEGREES", "RED", "BLUE", "GREEN", "YELLOW",
                         "WHITE", "BLACK", "GREY", "GRAY", "ORANGE", "PURPLE", "PINK",
                         "TEAL", "GOLD", "MAROON"]
}
```

### `editor_toolbar.py`

```python
class EditorToolbar(QToolBar):
    """Toolbar above the code editor with action buttons."""

    run_clicked = Signal()
    format_clicked = Signal()

    def __init__(self):
        super().__init__()
        self._run_btn = QAction("Run (Ctrl+Enter)", self)
        self._run_btn.setShortcut(QKeySequence("Ctrl+Return"))
        self._run_btn.triggered.connect(self.run_clicked)
        self.addAction(self._run_btn)

        self.addSeparator()

        self._font_size_spin = QSpinBox()
        self._font_size_spin.setRange(8, 32)
        self._font_size_spin.setValue(14)
        self._font_size_spin.setPrefix("Size: ")
        self._font_size_spin.valueChanged.connect(self.font_size_changed)
        self.addWidget(self._font_size_spin)

    font_size_changed = Signal(int)
```

### `code_editor_panel.py` — QDockWidget Wrapper

```python
class CodeEditorPanel(QDockWidget):
    """Wraps the code editor widget and toolbar into a dockable panel."""

    def __init__(self):
        super().__init__("Code Editor")
        self.setObjectName("code_editor_panel")

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)

        self._toolbar = EditorToolbar()
        self._editor = CodeEditorWidget()

        layout.addWidget(self._toolbar)
        layout.addWidget(self._editor)
        self.setWidget(container)

        # Wire toolbar to editor
        self._toolbar.run_clicked.connect(
            lambda: self._editor.run_requested.emit(self._editor.toPlainText())
        )
        self._toolbar.font_size_changed.connect(self._editor.set_font_size)

    # Public interface for Main Window:
    def set_code(self, code: str): self._editor.setPlainText(code)
    def get_code(self) -> str: return self._editor.toPlainText()
    def set_read_only(self, flag: bool): self._editor.setReadOnly(flag)
    def set_font(self, font: QFont): self._editor.setFont(font)
    def set_theme(self, theme: dict): self._editor.set_theme(theme)

    @property
    def code_changed(self): return self._editor.code_changed
    @property
    def run_requested(self): return self._editor.run_requested
```

---

## Theme Dict Format

The editor accepts a theme dict with these keys:

```python
{
    "background": "#1e1e2e",
    "text": "#cdd6f4",
    "current_line": "#2a2a3a",
    "gutter_bg": "#181825",
    "gutter_text": "#6c7086",
    "keyword": "#cba6f7",       # purple
    "builtin": "#f38ba8",       # pink
    "manim_class": "#89b4fa",   # blue
    "manim_method": "#a6e3a1",  # green
    "string": "#a6e3a1",        # green
    "comment": "#6c7086",       # gray
    "number": "#fab387",        # peach
    "decorator": "#f9e2af",     # yellow
    "function": "#89dceb",      # teal
    "self_keyword": "#f38ba8",  # pink
}
```

---

## Tests

**`test_code_editor.py`**:
- Test line number area width calculation
- Test set_code / get_code roundtrip
- Test PythonManimHighlighter formats keywords correctly
- Test completer loads keywords from JSON
- Test theme application changes stylesheet

## Verification

```bash
python -m pytest tests/test_ui/test_code_editor.py -v

# Visual test:
python -c "
import sys
from PySide6.QtWidgets import QApplication
from ui.panels.code_editor.code_editor_panel import CodeEditorPanel
app = QApplication(sys.argv)
panel = CodeEditorPanel()
panel.set_code('from manim import *\n\nRADIUS = 2\nCOLOR = BLUE\n\nclass MyScene(Scene):\n    def construct(self):\n        c = Circle(radius=RADIUS, color=COLOR)\n        self.play(Create(c))\n        self.wait(1)\n')
panel.show()
panel.resize(800, 600)
app.exec()
"
```

## Dependencies on Other Agents
- Agent 1: Only for `app.signals` if wiring signals directly (optional — Agent 7 handles wiring)

## What Other Agents Need From You
- Agent 7: `CodeEditorPanel` with `set_code()`, `get_code()`, `set_theme()`, `set_font()`, `code_changed` signal, `run_requested` signal
