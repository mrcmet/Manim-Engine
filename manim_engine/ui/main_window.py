from pathlib import Path

from PySide6.QtWidgets import (
    QMainWindow, QSplitter, QMessageBox,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence

from app.signals import SignalBus
from core.services.project_service import ProjectService
from core.services.version_service import VersionService
from core.services.settings_service import SettingsService
from core.services.variable_parser import VariableParser
from ai.ai_service import AIService
from renderer.render_service import RenderService
from renderer.render_config import RenderConfig
from ui.theme import ThemeManager
from ui.panels.variable_explorer.variable_explorer_panel import VariableExplorerPanel
from ui.panels.prompt_panel.prompt_panel import PromptPanel
from ui.panels.preview_viewer.preview_panel import PreviewPanel
from ui.panels.code_editor.code_editor_panel import CodeEditorPanel
from ui.panels.project_explorer.project_explorer_panel import ProjectExplorerPanel
from ui.panels.version_timeline.timeline_panel import TimelinePanel
from ui.dialogs.new_project_dialog import NewProjectDialog
from ui.dialogs.settings_dialog import SettingsDialog
from ui.dialogs.export_dialog import ExportDialog


class MainWindow(QMainWindow):
    def __init__(self, signal_bus: SignalBus, project_service: ProjectService,
                 version_service: VersionService, ai_service: AIService,
                 render_service: RenderService, settings_service: SettingsService,
                 theme_manager: ThemeManager):
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

    def _setup_layout(self):
        # Left docks: Variable Explorer (top) + Prompt Panel (bottom)
        self.addDockWidget(Qt.LeftDockWidgetArea, self._variable_explorer)
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
        view_menu.addAction(self._version_timeline.toggleViewAction())

        # Render menu
        render_menu = menu_bar.addMenu("Render")
        render_menu.addAction("Run (Low Quality)", self._run_low, QKeySequence("Ctrl+Return"))
        render_menu.addAction("Run (High Quality)", self._run_high, QKeySequence("Ctrl+Shift+Return"))
        render_menu.addAction("Cancel Render", self._cancel_render)

    def _wire_signals(self):
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
        if self._current_project:
            version = self._version_service.create_version(
                self._current_project.id, code,
                source="ai", parent_version_id=self._current_version_id
            )
            self._current_version_id = version.id
            self._refresh_timeline()
        self._render_service.render(code)

    def _on_ai_failed(self, error: str):
        self._prompt_panel.set_loading(False)
        self._prompt_panel.update_last_history("error", error)
        QMessageBox.warning(self, "AI Generation Failed", error)

    def _on_run_requested(self):
        code = self._code_editor.get_code()
        if not code.strip():
            return
        if self._current_project:
            version = self._version_service.create_version(
                self._current_project.id, code,
                source="manual_edit", parent_version_id=self._current_version_id
            )
            self._current_version_id = version.id
            self._refresh_timeline()
        self._render_service.render(code)

    def _on_code_changed(self, code: str):
        variables = VariableParser.extract_variables(code)
        self._variable_explorer.set_variables(variables)

    def _on_render_finished(self, video_path: str):
        self._preview_viewer.load_video(Path(video_path))
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
        if version.video_path and Path(str(version.video_path)).exists():
            self._preview_viewer.load_video(Path(str(version.video_path)))
        else:
            self._preview_viewer.clear()
        self._version_timeline.select_version(version_id)

    def _on_variable_edited(self, var_name: str, new_value):
        current_code = self._code_editor.get_code()
        modified_code = VariableParser.replace_variable(current_code, var_name, new_value)
        self._code_editor.set_code(modified_code)
        if self._current_project:
            version = self._version_service.create_version(
                self._current_project.id, modified_code,
                source="variable_tweak", parent_version_id=self._current_version_id
            )
            self._current_version_id = version.id
            self._refresh_timeline()
        self._render_service.render(modified_code)

    def _on_project_selected(self, project_id: str):
        project = self._project_service.open_project(project_id)
        self._current_project = project
        self._settings_service.set("last_project_id", project_id)
        versions = self._version_service.list_versions(project_id)
        self._version_timeline.set_versions(versions)
        if versions:
            latest = versions[-1]
            self._current_version_id = latest.id
            self._code_editor.set_code(latest.code)
            self._version_timeline.select_version(latest.id)
            if latest.video_path and Path(str(latest.video_path)).exists():
                self._preview_viewer.load_video(Path(str(latest.video_path)))
        else:
            self._code_editor.set_code("")
            self._preview_viewer.clear()
        self._refresh_project_list()

    # --- Dialogs ---

    def _new_project(self):
        dialog = NewProjectDialog(self)
        if dialog.exec():
            name, desc = dialog.get_values()
            if name.strip():
                project = self._project_service.create_project(name, desc)
                self._on_project_selected(project.id)

    def _open_settings(self):
        dialog = SettingsDialog(self._settings_service, self._theme_manager, self)
        if dialog.exec():
            self._apply_theme()
            self._bus.settings_changed.emit()

    def _export_dialog(self):
        dialog = ExportDialog(self)
        if dialog.exec():
            quality, fmt = dialog.get_values()
            config = RenderConfig(quality=quality, format=fmt)
            code = self._code_editor.get_code()
            self._render_service.render(code, config=config)

    # --- Render shortcuts ---

    def _run_low(self):
        code = self._code_editor.get_code()
        if code.strip():
            self._render_service.render(code, config=RenderConfig(quality="l"))

    def _run_high(self):
        code = self._code_editor.get_code()
        if code.strip():
            self._render_service.render(code, config=RenderConfig(quality="h"))

    def _cancel_render(self):
        self._render_service.cancel_render()

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
        active = settings.active_provider
        if providers:
            self._prompt_panel.set_providers(providers, active)
        # Refresh project list
        self._refresh_project_list()

    def _load_sample_if_empty(self):
        """Load sample code if editor is empty (no project loaded)."""
        if not self._code_editor.get_code().strip():
            sample = Path(__file__).parent.parent / "samples" / "circle_animation.py"
            if sample.exists():
                self._code_editor.set_code(sample.read_text())

    def _refresh_project_list(self):
        projects = self._project_service.list_projects()
        self._project_explorer.refresh_projects(projects)

    def _refresh_timeline(self):
        if self._current_project:
            versions = self._version_service.list_versions(self._current_project.id)
            self._version_timeline.set_versions(versions)
            if self._current_version_id:
                self._version_timeline.select_version(self._current_version_id)

    def closeEvent(self, event):
        settings = self._settings_service.load()
        settings.window_geometry = self.saveGeometry()
        settings.window_state = self.saveState()
        self._settings_service.save(settings)
        self._render_service.cleanup()
        super().closeEvent(event)
