from pathlib import Path

from PySide6.QtWidgets import (
    QMainWindow, QSplitter, QMessageBox,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence

from app.controller import AppController
from app.signals import SignalBus
from core.services.code_parser import CodeParser
from core.services.snippets_service import SnippetsService
from renderer.render_config import RenderConfig
from ui.qt_bridge import QtBridge
from ui.theme import ThemeManager
from ui.panels.variable_explorer.variable_explorer_panel import VariableExplorerPanel
from ui.panels.prompt_panel.prompt_panel import PromptPanel
from ui.panels.preview_viewer.preview_panel import PreviewPanel
from ui.panels.code_editor.code_editor_panel import CodeEditorPanel
from ui.panels.project_explorer.project_explorer_panel import ProjectExplorerPanel
from ui.panels.version_timeline.timeline_panel import TimelinePanel
from ui.panels.snippets.snippets_panel import SnippetsPanel
from ui.dialogs.new_project_dialog import NewProjectDialog
from ui.dialogs.settings_dialog import SettingsDialog
from ui.dialogs.export_dialog import ExportDialog


class MainWindow(QMainWindow):
    def __init__(self, controller: AppController, bridge: QtBridge,
                 signal_bus: SignalBus, theme_manager: ThemeManager,
                 snippets_service: SnippetsService | None = None):
        super().__init__()
        self.setWindowTitle("Manim Engine")
        self.setMinimumSize(1200, 800)

        self._controller = controller
        self._bridge = bridge
        self._bus = signal_bus
        self._theme_manager = theme_manager
        self._snippets_service = snippets_service or SnippetsService()

        self._create_panels()
        self._create_menus()
        self._setup_layout()
        self._wire_signals()
        self._apply_theme()
        self._restore_state()
        self._load_sample_if_empty()

    def _create_panels(self):
        self._variable_explorer = VariableExplorerPanel()
        self._variable_explorer.setObjectName("VariableExplorer")
        self._prompt_panel = PromptPanel()
        self._prompt_panel.setObjectName("PromptPanel")
        self._preview_viewer = PreviewPanel()
        self._code_editor = CodeEditorPanel()
        self._project_explorer = ProjectExplorerPanel()
        self._project_explorer.setObjectName("ProjectExplorer")
        self._version_timeline = TimelinePanel()
        self._version_timeline.setObjectName("VersionTimeline")
        self._snippets_panel = SnippetsPanel(self._snippets_service)
        self._snippets_panel.setObjectName("SnippetsPanel")

    def _setup_layout(self):
        # Left docks: Variable Explorer (tabbed with Snippets) + Prompt Panel (below)
        self.addDockWidget(Qt.LeftDockWidgetArea, self._variable_explorer)
        self.addDockWidget(Qt.LeftDockWidgetArea, self._snippets_panel)
        self.tabifyDockWidget(self._variable_explorer, self._snippets_panel)
        self.addDockWidget(Qt.LeftDockWidgetArea, self._prompt_panel)
        self.splitDockWidget(self._variable_explorer, self._prompt_panel, Qt.Vertical)

        # Center: Preview (top) + Code Editor (bottom) as central widget
        central_splitter = QSplitter(Qt.Vertical)
        central_splitter.addWidget(self._preview_viewer)
        central_splitter.addWidget(self._code_editor)
        central_splitter.setSizes([400, 400])
        self.setCentralWidget(central_splitter)

        # Right dock: Project Explorer
        self.addDockWidget(Qt.RightDockWidgetArea, self._project_explorer)

        # Bottom dock: Version Timeline
        self.addDockWidget(Qt.BottomDockWidgetArea, self._version_timeline)

    def _create_menus(self):
        menu_bar = self.menuBar()

        # File menu
        file_menu = menu_bar.addMenu("File")
        file_menu.addAction("New Project", self._new_project, QKeySequence("Ctrl+N"))
        file_menu.addSeparator()
        file_menu.addAction("Export Video...", self._export_dialog, QKeySequence("Ctrl+E"))
        file_menu.addSeparator()
        file_menu.addAction("Settings...", self._open_settings, QKeySequence("Ctrl+,"))
        file_menu.addSeparator()
        file_menu.addAction("Quit", self.close, QKeySequence("Ctrl+Q"))

        # View menu
        view_menu = menu_bar.addMenu("View")
        view_menu.addAction(self._project_explorer.toggleViewAction())
        view_menu.addAction(self._variable_explorer.toggleViewAction())
        view_menu.addAction(self._snippets_panel.toggleViewAction())
        view_menu.addAction(self._version_timeline.toggleViewAction())

        # Render menu
        render_menu = menu_bar.addMenu("Render")
        render_menu.addAction("Run (Low Quality)", self._run_low, QKeySequence("Ctrl+Return"))
        render_menu.addAction("Run (High Quality)", self._run_high, QKeySequence("Ctrl+Shift+Return"))
        render_menu.addAction("Cancel Render", self._cancel_render)

    def _wire_signals(self):
        # Render
        self._bridge.render_started.connect(lambda: self._preview_viewer.show_loading())
        self._bridge.render_finished.connect(self._on_render_finished)
        self._bridge.render_image_finished.connect(self._on_render_image_finished)
        self._bridge.render_failed.connect(self._on_render_failed)
        self._bridge.render_failed_detail.connect(self._on_render_failed_detail)

        # AI
        self._bridge.ai_started.connect(lambda: self._prompt_panel.set_loading(True))
        self._bridge.ai_finished.connect(self._on_ai_finished)
        self._bridge.ai_failed.connect(self._on_ai_failed)

        # Version / project
        self._bridge.version_created.connect(lambda _: self._refresh_timeline())
        self._bridge.project_opened.connect(self._on_project_opened)
        self._bridge.code_changed_external.connect(self._code_editor.set_code)

        # UI-local
        self._prompt_panel.prompt_submitted.connect(self._on_prompt_submitted)
        self._code_editor.run_requested.connect(self._on_run_requested)
        self._code_editor.code_changed.connect(self._on_code_changed)
        self._version_timeline.version_selected.connect(self._on_version_selected)
        self._snippets_panel.snippet_insert_requested.connect(self._on_snippet_insert)
        self._project_explorer.project_selected.connect(self._controller.open_project)
        self._project_explorer.new_project_requested.connect(self._new_project)

        # Code Explorer — navigate to line on tree-node click
        self._variable_explorer.navigate_to_line.connect(self._code_editor.navigate_to_line)

        # Selection indicator
        self._code_editor.get_editor_widget().selectionChanged.connect(
            self._on_editor_selection_changed
        )

    # --- Handlers ---

    def _on_prompt_submitted(self, prompt: str, include_code: bool):
        self._prompt_panel.add_history_entry(prompt, "pending")
        settings = self._controller.get_settings()
        custom_context = getattr(settings, "custom_prompt_context", "") or None
        self._controller.submit_prompt(
            prompt,
            self._code_editor.get_code() if include_code else None,
            self._code_editor.get_selected_text() or None,
            custom_context,
            self._prompt_panel.get_selected_provider(),
        )

    def _on_ai_finished(self, code: str):
        self._prompt_panel.set_loading(False)
        self._prompt_panel.update_last_history("success", "Code generated")
        self._code_editor.set_code(code)

    def _on_ai_failed(self, error: str):
        self._prompt_panel.set_loading(False)
        self._prompt_panel.update_last_history("error", error)
        QMessageBox.warning(self, "AI Generation Failed", error)

    def _on_run_requested(self):
        self._controller.run_code(self._code_editor.get_code())

    def _on_code_changed(self, code: str):
        structure = CodeParser.parse(code)
        self._variable_explorer.set_code_structure(structure)

    def _on_render_finished(self, video_path: str):
        self._preview_viewer.load_video(Path(video_path))
        self._code_editor.clear_render_error()

    def _on_render_image_finished(self, image_path: str):
        self._preview_viewer.load_image(Path(image_path))
        self._code_editor.clear_render_error()

    def _on_render_failed(self, error: str):
        self._preview_viewer.show_error(error)

    def _on_render_failed_detail(self, parsed_error, stdout: str, stderr: str):
        self._code_editor.show_render_error(parsed_error, stdout, stderr)

    def _on_version_selected(self, version_id: str):
        self._controller.load_version(version_id)
        project = self._controller.get_active_project()
        if project:
            version = self._controller.get_version(project.id, version_id)
            if version.video_path and Path(str(version.video_path)).exists():
                self._preview_viewer.load_video(Path(str(version.video_path)))
            else:
                self._preview_viewer.clear()
        self._version_timeline.select_version(version_id)

    def _on_project_opened(self, project_id: str, project_name: str):
        versions = self._controller.get_versions(project_id)
        self._version_timeline.set_versions(versions)
        if versions:
            latest = versions[-1]
            self._controller.load_version(latest.id)
            self._version_timeline.select_version(latest.id)
            if latest.video_path and Path(str(latest.video_path)).exists():
                self._preview_viewer.load_video(Path(str(latest.video_path)))
        else:
            self._code_editor.set_code("")
            self._preview_viewer.clear()
        self._refresh_project_list()

    def _on_editor_selection_changed(self) -> None:
        text = self._code_editor.get_selected_text()
        if text.strip():
            lines = text.count('\n') + 1
            self._prompt_panel.set_selection_active(f"Selection active ({lines} lines)")
        else:
            self._prompt_panel.set_selection_active("")

    def _on_snippet_insert(self, code: str) -> None:
        editor = self._code_editor.get_editor_widget()
        cursor = editor.textCursor()
        cursor.insertText(code)
        editor.setTextCursor(cursor)
        editor.setFocus()
        self._controller.mark_snippet_used()

    # --- Dialogs ---

    def _new_project(self):
        dialog = NewProjectDialog(self)
        if dialog.exec():
            name, desc = dialog.get_values()
            if name.strip():
                self._controller.create_project(name, desc)

    def _open_settings(self):
        dialog = SettingsDialog(self._controller.get_settings_service(), self._theme_manager, self)
        if dialog.exec():
            self._apply_theme()
            self._reload_ai_providers()
            self._bus.settings_changed.emit()

    def _reload_ai_providers(self):
        settings = self._controller.get_settings()
        for name, config in settings.ai_providers.items():
            self._controller.reload_ai_provider(name, config)

    def _export_dialog(self):
        dialog = ExportDialog(self)
        if dialog.exec():
            quality, fmt = dialog.get_values()
            config = RenderConfig(quality=quality, format=fmt)
            code = self._code_editor.get_code()
            self._controller.run_code(code, config=config)

    # --- Render shortcuts ---

    def _run_low(self):
        code = self._code_editor.get_code()
        if code.strip():
            self._controller.run_code(code, config=RenderConfig(quality="l"))

    def _run_high(self):
        code = self._code_editor.get_code()
        if code.strip():
            self._controller.run_code(code, config=RenderConfig(quality="h"))

    def _cancel_render(self):
        self._controller.cancel_render()

    # --- State ---

    def _apply_theme(self):
        theme = self._theme_manager.get_theme()
        self.setStyleSheet(self._theme_manager.get_app_stylesheet(theme))
        self._code_editor.set_theme(theme)
        self._snippets_panel.apply_theme(theme)
        self._bus.theme_changed.emit(theme)

    def _restore_state(self):
        settings = self._controller.get_settings()
        if settings.window_geometry:
            self.restoreGeometry(settings.window_geometry)
        if settings.window_state:
            self.restoreState(settings.window_state)
        # Load last project
        if settings.last_project_id:
            try:
                self._controller.open_project(settings.last_project_id)
            except Exception:
                pass
        # Set providers in prompt panel
        providers = self._controller.get_active_providers()
        active = settings.active_provider
        if providers:
            self._prompt_panel.set_providers(providers, active)
        # Refresh project list
        self._refresh_project_list()

    def _load_sample_if_empty(self):
        if not self._code_editor.get_code().strip():
            sample = Path(__file__).parent.parent / "samples" / "circle_animation.py"
            if sample.exists():
                self._code_editor.set_code(sample.read_text())

    def _refresh_project_list(self):
        projects = self._controller.get_projects()
        self._project_explorer.refresh_projects(projects)

    def _refresh_timeline(self):
        project = self._controller.get_active_project()
        if project:
            versions = self._controller.get_versions(project.id)
            self._version_timeline.set_versions(versions)
            active_version = self._controller.get_current_version_id()
            if active_version:
                self._version_timeline.select_version(active_version)

    def closeEvent(self, event):
        self._controller.save_window_state(
            bytes(self.saveGeometry()),
            bytes(self.saveState()),
        )
        self._controller.cleanup()
        super().closeEvent(event)
