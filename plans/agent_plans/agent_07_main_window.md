# Agent 7: Main Window, Settings Dialog & Integration Wiring

## Scope
Build the main window that composes all 6 panels into the dock layout, the settings dialog (with API key management, editor theming, rendering config), the export dialog, the new project dialog, the theme manager, and all signal-to-service wiring that ties the application together.

**This agent runs LAST** — after Agents 1-6 have built their components.

## Files to Create

```
manim_engine/
├── ui/
│   ├── main_window.py
│   ├── theme.py
│   └── dialogs/
│       ├── __init__.py
│       ├── settings_dialog.py
│       ├── export_dialog.py
│       ├── new_project_dialog.py
│       └── pin_dialog.py
└── resources/
    ├── default_theme.json
    └── icons/          # placeholder .svg files (or use Qt built-in icons)
```

---

## Detailed Specifications

### `ui/theme.py` — Theme Manager

```python
import json
from pathlib import Path

DEFAULT_DARK_THEME = {
    "background": "#1e1e2e",
    "text": "#cdd6f4",
    "current_line": "#2a2a3a",
    "gutter_bg": "#181825",
    "gutter_text": "#6c7086",
    "keyword": "#cba6f7",
    "builtin": "#f38ba8",
    "manim_class": "#89b4fa",
    "manim_method": "#a6e3a1",
    "string": "#a6e3a1",
    "comment": "#6c7086",
    "number": "#fab387",
    "decorator": "#f9e2af",
    "function": "#89dceb",
    "self_keyword": "#f38ba8",
    "panel_bg": "#1e1e2e",
    "panel_border": "#313244",
    "button_bg": "#45475a",
    "button_text": "#cdd6f4",
    "accent": "#89b4fa",
}

DEFAULT_LIGHT_THEME = {
    "background": "#eff1f5",
    "text": "#4c4f69",
    "current_line": "#e6e9ef",
    "gutter_bg": "#dce0e8",
    "gutter_text": "#9ca0b0",
    "keyword": "#8839ef",
    "builtin": "#d20f39",
    "manim_class": "#1e66f5",
    "manim_method": "#40a02b",
    "string": "#40a02b",
    "comment": "#9ca0b0",
    "number": "#fe640b",
    "decorator": "#df8e1d",
    "function": "#04a5e5",
    "self_keyword": "#d20f39",
    "panel_bg": "#eff1f5",
    "panel_border": "#ccd0da",
    "button_bg": "#bcc0cc",
    "button_text": "#4c4f69",
    "accent": "#1e66f5",
}

class ThemeManager:
    BUILTIN_THEMES = {"dark": DEFAULT_DARK_THEME, "light": DEFAULT_LIGHT_THEME}

    def __init__(self, settings_service):
        self._settings = settings_service

    def get_theme(self, name: str | None = None) -> dict:
        """Get theme dict by name. Falls back to dark."""
        name = name or self._settings.get("editor_theme", "dark")
        if name in self.BUILTIN_THEMES:
            return self.BUILTIN_THEMES[name]
        # Try loading custom theme from settings
        custom = self._settings.get(f"custom_theme_{name}")
        return custom or self.BUILTIN_THEMES["dark"]

    def get_app_stylesheet(self, theme: dict) -> str:
        """Generate QSS stylesheet for the entire application from theme dict."""
        return f"""
        QMainWindow {{
            background-color: {theme['panel_bg']};
        }}
        QDockWidget {{
            color: {theme['text']};
            titlebar-close-icon: url(close.svg);
        }}
        QDockWidget::title {{
            background-color: {theme['panel_border']};
            padding: 6px;
        }}
        QPushButton {{
            background-color: {theme['button_bg']};
            color: {theme['button_text']};
            border: 1px solid {theme['panel_border']};
            padding: 6px 12px;
            border-radius: 4px;
        }}
        QPushButton:hover {{
            background-color: {theme['accent']};
        }}
        QTextEdit, QPlainTextEdit {{
            background-color: {theme['background']};
            color: {theme['text']};
            border: 1px solid {theme['panel_border']};
        }}
        QTableWidget {{
            background-color: {theme['background']};
            color: {theme['text']};
            gridline-color: {theme['panel_border']};
        }}
        QHeaderView::section {{
            background-color: {theme['panel_border']};
            color: {theme['text']};
            padding: 4px;
        }}
        QSlider::groove:horizontal {{
            background: {theme['panel_border']};
            height: 6px;
            border-radius: 3px;
        }}
        QSlider::handle:horizontal {{
            background: {theme['accent']};
            width: 14px;
            margin: -4px 0;
            border-radius: 7px;
        }}
        QComboBox, QLineEdit, QSpinBox, QDoubleSpinBox {{
            background-color: {theme['background']};
            color: {theme['text']};
            border: 1px solid {theme['panel_border']};
            padding: 4px;
            border-radius: 3px;
        }}
        QScrollBar:horizontal, QScrollBar:vertical {{
            background: {theme['panel_bg']};
        }}
        QScrollBar::handle {{
            background: {theme['button_bg']};
            border-radius: 4px;
        }}
        QLabel {{
            color: {theme['text']};
        }}
        QCheckBox {{
            color: {theme['text']};
        }}
        QToolTip {{
            background-color: {theme['panel_border']};
            color: {theme['text']};
            border: 1px solid {theme['accent']};
        }}
        """

    def list_themes(self) -> list[str]:
        return list(self.BUILTIN_THEMES.keys())
```

### `ui/main_window.py` — Main Window & Controller

```python
class MainWindow(QMainWindow):
    def __init__(self, signal_bus, project_service, version_service,
                 ai_service, render_service, settings_service, theme_manager):
        super().__init__()
        self.setWindowTitle("Manim Engine")
        self.setMinimumSize(1200, 800)

        self._bus = signal_bus
        self._project_service = project_service
        self._version_service = version_service
        self._ai_service = ai_service
        self._render_service = render_service
        self._settings_service = settings_service
        self._theme_manager = theme_manager
        self._current_project = None
        self._current_version_id = None

        self._create_panels()
        self._create_menus()
        self._setup_layout()
        self._wire_signals()
        self._apply_theme()
        self._restore_state()

    def _create_panels(self):
        self._variable_explorer = VariableExplorerPanel()
        self._prompt_panel = PromptPanel()
        self._preview_viewer = PreviewPanel()
        self._code_editor = CodeEditorPanel()
        self._project_explorer = ProjectExplorerPanel()
        self._version_timeline = TimelinePanel()

    def _setup_layout(self):
        """
        Layout:
        +------------------+-----------------------------+------------------+
        | Variable Explorer|     Preview Viewer          | Project Explorer |
        +------------------+-----------------------------+  (collapsible)   |
        | Prompt Panel     |     Code Editor             |                  |
        +------------------+-----------------------------+------------------+
        |                    Version Timeline                               |
        +------------------------------------------------------------------+
        """
        # Left side: Variable Explorer (top) + Prompt Panel (bottom)
        self.addDockWidget(Qt.LeftDockWidgetArea, self._variable_explorer)
        self.addDockWidget(Qt.LeftDockWidgetArea, self._prompt_panel)
        self.splitDockWidget(self._variable_explorer, self._prompt_panel, Qt.Vertical)

        # Center: Preview (top) + Code Editor (bottom) using QSplitter as central widget
        central_splitter = QSplitter(Qt.Vertical)
        # Extract inner widgets from dock widgets for central area
        preview_widget = QWidget()
        preview_layout = QVBoxLayout(preview_widget)
        preview_layout.setContentsMargins(0, 0, 0, 0)
        preview_layout.addWidget(self._preview_viewer)

        editor_widget = QWidget()
        editor_layout = QVBoxLayout(editor_widget)
        editor_layout.setContentsMargins(0, 0, 0, 0)
        editor_layout.addWidget(self._code_editor)

        central_splitter.addWidget(self._preview_viewer)
        central_splitter.addWidget(self._code_editor)
        central_splitter.setSizes([400, 400])
        self.setCentralWidget(central_splitter)

        # NOTE: Since Preview and Code Editor are in central widget,
        # they should NOT be QDockWidgets. Agent 4 and 5 panels should
        # provide their inner widget directly. Alternative: make them all
        # dock widgets and use tabifyDockWidget / splitDockWidget.

        # Right side: Project Explorer
        self.addDockWidget(Qt.RightDockWidgetArea, self._project_explorer)

        # Bottom: Version Timeline
        self.addDockWidget(Qt.BottomDockWidgetArea, self._version_timeline)

    def _create_menus(self):
        menu_bar = self.menuBar()

        # File menu
        file_menu = menu_bar.addMenu("File")
        file_menu.addAction("New Project", self._new_project, QKeySequence("Ctrl+N"))
        file_menu.addAction("Open Project...", self._open_project_dialog)
        file_menu.addSeparator()
        file_menu.addAction("Export Video...", self._export_dialog, QKeySequence("Ctrl+E"))
        file_menu.addSeparator()
        file_menu.addAction("Settings...", self._open_settings, QKeySequence("Ctrl+,"))
        file_menu.addSeparator()
        file_menu.addAction("Quit", self.close, QKeySequence("Ctrl+Q"))

        # Edit menu
        edit_menu = menu_bar.addMenu("Edit")
        edit_menu.addAction("Undo", lambda: None, QKeySequence("Ctrl+Z"))
        edit_menu.addAction("Redo", lambda: None, QKeySequence("Ctrl+Shift+Z"))

        # View menu
        view_menu = menu_bar.addMenu("View")
        view_menu.addAction(self._project_explorer.toggleViewAction())
        view_menu.addAction(self._variable_explorer.toggleViewAction())
        view_menu.addAction(self._version_timeline.toggleViewAction())

        # Render menu
        render_menu = menu_bar.addMenu("Render")
        render_menu.addAction("Run (Low Quality)", self._run_low, QKeySequence("Ctrl+Return"))
        render_menu.addAction("Run (High Quality)", self._run_high, QKeySequence("Ctrl+Shift+Return"))
        render_menu.addAction("Cancel Render", self._cancel_render)

    def _wire_signals(self):
        """Connect all signal bus signals to handlers."""
        bus = self._bus

        # Prompt → AI generation
        self._prompt_panel.prompt_submitted.connect(self._on_prompt_submitted)

        # AI results → Code editor
        bus.ai_generation_finished.connect(self._on_code_generated)
        bus.ai_generation_failed.connect(self._on_ai_failed)
        bus.ai_generation_started.connect(lambda: self._prompt_panel.set_loading(True))

        # Code editor → Render
        self._code_editor.run_requested.connect(self._on_run_requested)

        # Code changed → Variable extraction
        self._code_editor.code_changed.connect(self._on_code_changed)

        # Render results → Preview
        bus.render_finished.connect(self._on_render_finished)
        bus.render_failed.connect(self._on_render_failed)
        bus.render_started.connect(lambda: self._preview_viewer.show_loading())

        # Version timeline
        self._version_timeline.version_selected.connect(self._on_version_selected)

        # Variable explorer
        self._variable_explorer.variable_edited.connect(self._on_variable_edited)

        # Project explorer
        self._project_explorer.project_selected.connect(self._on_project_selected)
        self._project_explorer.new_project_requested.connect(self._new_project)

    # --- Handlers ---

    def _on_prompt_submitted(self, prompt: str, include_code: bool):
        self._prompt_panel.add_history_entry(prompt, "pending")
        current_code = self._code_editor.get_code() if include_code else None
        provider = self._prompt_panel.get_selected_provider()
        self._ai_service.set_active_provider(provider)
        self._ai_service.generate_code(prompt, current_code)

    def _on_code_generated(self, code: str):
        self._prompt_panel.set_loading(False)
        self._prompt_panel.update_last_history("success", "Code generated")
        self._code_editor.set_code(code)
        # Create version
        if self._current_project:
            version = self._version_service.create_version(
                self._current_project.id, code,
                source="ai", parent_version_id=self._current_version_id
            )
            self._current_version_id = version.id
            self._version_timeline.add_version(version)
            self._version_timeline.select_version(version.id)
        # Auto-render
        self._render_service.render(code)

    def _on_ai_failed(self, error: str):
        self._prompt_panel.set_loading(False)
        self._prompt_panel.update_last_history("error", error)
        QMessageBox.warning(self, "AI Generation Failed", error)

    def _on_run_requested(self, code: str):
        if self._current_project:
            version = self._version_service.create_version(
                self._current_project.id, code,
                source="manual_edit", parent_version_id=self._current_version_id
            )
            self._current_version_id = version.id
            self._version_timeline.add_version(version)
            self._version_timeline.select_version(version.id)
        self._render_service.render(code)

    def _on_code_changed(self, code: str):
        from core.services.variable_parser import VariableParser
        variables = VariableParser.extract_variables(code)
        self._variable_explorer.set_variables(variables)

    def _on_render_finished(self, video_path: str):
        self._preview_viewer.load_video(Path(video_path))
        # Update version with video path
        if self._current_project and self._current_version_id:
            self._version_service.set_video_path(
                self._current_project.id, self._current_version_id, Path(video_path)
            )

    def _on_render_failed(self, error: str):
        self._preview_viewer.show_error(error)

    def _on_version_selected(self, version_id: str):
        if not self._current_project:
            return
        version = self._version_service.get_version(
            self._current_project.id, version_id
        )
        self._current_version_id = version.id
        self._code_editor.set_code(version.code)
        if version.video_path and version.video_path.exists():
            self._preview_viewer.load_video(version.video_path)
        else:
            self._preview_viewer.clear()
        self._version_timeline.select_version(version_id)

    def _on_variable_edited(self, var_name: str, new_value):
        from core.services.variable_parser import VariableParser
        current_code = self._code_editor.get_code()
        modified_code = VariableParser.replace_variable(current_code, var_name, new_value)
        self._code_editor.set_code(modified_code)
        # Create version and render
        if self._current_project:
            version = self._version_service.create_version(
                self._current_project.id, modified_code,
                source="variable_tweak", parent_version_id=self._current_version_id
            )
            self._current_version_id = version.id
            self._version_timeline.add_version(version)
            self._version_timeline.select_version(version.id)
        self._render_service.render(modified_code)

    def _on_project_selected(self, project_id: str):
        project = self._project_service.open_project(project_id)
        self._current_project = project
        self._settings_service.set("last_project_id", project_id)
        # Load versions
        versions = self._version_service.list_versions(project_id)
        self._version_timeline.set_versions(versions)
        if versions:
            latest = versions[-1]
            self._current_version_id = latest.id
            self._code_editor.set_code(latest.code)
            self._version_timeline.select_version(latest.id)
            if latest.video_path and Path(latest.video_path).exists():
                self._preview_viewer.load_video(Path(latest.video_path))
        else:
            self._code_editor.set_code("")
            self._preview_viewer.clear()
        # Refresh project list
        projects = self._project_service.list_projects()
        self._project_explorer.refresh_projects(projects)

    # --- Dialogs ---

    def _new_project(self):
        dialog = NewProjectDialog(self)
        if dialog.exec():
            name, desc = dialog.get_values()
            project = self._project_service.create_project(name, desc)
            self._on_project_selected(project.id)
            self._bus.project_created.emit(project.id)

    def _open_settings(self):
        dialog = SettingsDialog(self._settings_service, self._theme_manager, self)
        if dialog.exec():
            self._apply_theme()
            self._settings_service.save(self._settings_service.load())
            self._bus.settings_changed.emit()

    def _export_dialog(self):
        dialog = ExportDialog(self)
        if dialog.exec():
            quality, fmt = dialog.get_values()
            from renderer.render_config import RenderConfig
            config = RenderConfig(quality=quality, format=fmt)
            code = self._code_editor.get_code()
            self._render_service.render(code, config=config)

    # --- State ---

    def _apply_theme(self):
        theme = self._theme_manager.get_theme()
        self.setStyleSheet(self._theme_manager.get_app_stylesheet(theme))
        self._code_editor.set_theme(theme)
        self._bus.theme_changed.emit(theme)

    def _restore_state(self):
        settings = self._settings_service.load()
        if settings.window_geometry:
            self.restoreGeometry(settings.window_geometry)
        if settings.window_state:
            self.restoreState(settings.window_state)
        # Load last project
        if settings.last_project_id:
            try:
                self._on_project_selected(settings.last_project_id)
            except Exception:
                pass
        # Set providers in prompt panel
        providers = self._ai_service.get_available_providers()
        self._prompt_panel.set_providers(providers, settings.active_provider)

    def closeEvent(self, event):
        settings = self._settings_service.load()
        settings.window_geometry = self.saveGeometry()
        settings.window_state = self.saveState()
        self._settings_service.save(settings)
        self._render_service.cleanup()
        super().closeEvent(event)
```

### `ui/dialogs/settings_dialog.py`

Tabbed dialog with 4 tabs:

**Tab 1: General**
- Default project directory (QFileDialog path picker)
- Auto-render on code change (QCheckBox)

**Tab 2: AI Providers**
- QComboBox to select active provider
- For each provider, a collapsible group box with:
  - API Key field (QLineEdit, password echo mode)
  - Model name (QLineEdit with placeholder showing default)
  - Base URL (for Ollama only)
  - Max tokens (QSpinBox)
  - Temperature (QDoubleSpinBox, 0.0-2.0)
- "Test Connection" button per provider

**Tab 3: Editor**
- Font family (QFontComboBox)
- Font size (QSpinBox, 8-32)
- Theme selector (QComboBox: dark, light)
- Tab width (QSpinBox, 2-8)
- Preview of current theme colors

**Tab 4: Rendering**
- Default quality (QComboBox: Low/Medium/High/4K)
- Render timeout (QSpinBox, 10-120 seconds)
- Output format (QComboBox: mp4/gif/webm)

**Tab 5: Security**
- Change PIN button
- Remove PIN button

### `ui/dialogs/export_dialog.py`

```python
class ExportDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Export Animation")
        layout = QFormLayout(self)

        self._quality = QComboBox()
        self._quality.addItems(["Low (480p)", "Medium (720p)", "High (1080p)", "4K (2160p)"])
        self._quality.setCurrentIndex(2)  # default High

        self._format = QComboBox()
        self._format.addItems(["mp4", "gif", "webm"])

        layout.addRow("Quality:", self._quality)
        layout.addRow("Format:", self._format)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def get_values(self) -> tuple[str, str]:
        quality_map = {0: "l", 1: "m", 2: "h", 3: "k"}
        return quality_map[self._quality.currentIndex()], self._format.currentText()
```

### `ui/dialogs/new_project_dialog.py`

```python
class NewProjectDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("New Project")
        layout = QFormLayout(self)

        self._name = QLineEdit()
        self._name.setPlaceholderText("My Animation")
        self._desc = QTextEdit()
        self._desc.setMaximumHeight(80)
        self._desc.setPlaceholderText("Optional description...")

        layout.addRow("Project Name:", self._name)
        layout.addRow("Description:", self._desc)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def get_values(self) -> tuple[str, str]:
        return self._name.text(), self._desc.toPlainText()
```

### `ui/dialogs/pin_dialog.py`

```python
class PinDialog(QDialog):
    """Simple PIN entry dialog for app startup."""

    def __init__(self, is_setup: bool = False, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Enter PIN" if not is_setup else "Set PIN")
        self.setFixedSize(300, 150)

        layout = QVBoxLayout(self)
        self._label = QLabel("Enter your PIN:" if not is_setup else "Choose a 4-6 digit PIN:")
        self._pin_input = QLineEdit()
        self._pin_input.setEchoMode(QLineEdit.Password)
        self._pin_input.setMaxLength(6)
        self._pin_input.setAlignment(Qt.AlignCenter)
        self._pin_input.setPlaceholderText("****")

        self._error_label = QLabel()
        self._error_label.setStyleSheet("color: red;")

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout.addWidget(self._label)
        layout.addWidget(self._pin_input)
        layout.addWidget(self._error_label)
        layout.addWidget(buttons)

    def get_pin(self) -> str:
        return self._pin_input.text()

    def show_error(self, msg: str):
        self._error_label.setText(msg)
```

### `resources/default_theme.json`

```json
{
    "dark": { ... },
    "light": { ... }
}
```

(Same content as DEFAULT_DARK_THEME and DEFAULT_LIGHT_THEME dicts above, serialized as JSON.)

---

## Integration Wiring Summary

This is the critical flow — every signal connection documented:

| Source | Signal | Handler | Action |
|--------|--------|---------|--------|
| PromptPanel | `prompt_submitted(str, bool)` | `_on_prompt_submitted` | Calls `ai_service.generate_code()` |
| SignalBus | `ai_generation_started` | lambda | `prompt_panel.set_loading(True)` |
| SignalBus | `ai_generation_finished(str)` | `_on_code_generated` | Set code in editor, create version, auto-render |
| SignalBus | `ai_generation_failed(str)` | `_on_ai_failed` | Show error, reset loading |
| CodeEditorPanel | `run_requested(str)` | `_on_run_requested` | Create version, start render |
| CodeEditorPanel | `code_changed(str)` | `_on_code_changed` | Extract variables → variable explorer |
| SignalBus | `render_started` | lambda | `preview_viewer.show_loading()` |
| SignalBus | `render_finished(str)` | `_on_render_finished` | Load video in preview, update version |
| SignalBus | `render_failed(str)` | `_on_render_failed` | Show error in preview |
| TimelinePanel | `version_selected(str)` | `_on_version_selected` | Load version code + video |
| VariableExplorerPanel | `variable_edited(str, obj)` | `_on_variable_edited` | Modify code, create version, re-render |
| ProjectExplorerPanel | `project_selected(str)` | `_on_project_selected` | Open project, load versions |
| ProjectExplorerPanel | `new_project_requested` | `_new_project` | Show new project dialog |

---

## Tests

Integration tests (require all modules):
- Test main window instantiation with mock services
- Test signal wiring: emit prompt_submitted → verify ai_service.generate_code called
- Test version creation flow
- Test theme application

## Verification

```bash
# Full app launch test:
cd manim_engine
python main.py

# Walkthrough:
# 1. PIN dialog appears → enter/set PIN
# 2. Main window loads with all panels
# 3. Create new project
# 4. Enter prompt → AI generates code → code appears in editor
# 5. Video renders → appears in preview
# 6. Edit a variable → code updates → re-renders
# 7. Click version node → restores that version
# 8. Open Settings → change theme → UI updates
# 9. Export → higher quality render
# 10. Close → reopen → last project loads automatically
```

## Dependencies on Other Agents
- **ALL agents (1-6)**: This agent imports and composes everything.
- Agent 1: All services and models
- Agent 2: AIService, ProviderRegistry
- Agent 3: RenderService
- Agent 4: CodeEditorPanel
- Agent 5: PreviewPanel, PromptPanel
- Agent 6: ProjectExplorerPanel, VariableExplorerPanel, TimelinePanel
