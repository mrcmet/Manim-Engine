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
        name = name or self._settings.get("editor_theme", "dark")
        if name in self.BUILTIN_THEMES:
            return self.BUILTIN_THEMES[name]
        return self.BUILTIN_THEMES["dark"]

    def get_app_stylesheet(self, theme: dict) -> str:
        return f"""
        QMainWindow {{
            background-color: {theme['panel_bg']};
        }}
        QDockWidget {{
            color: {theme['text']};
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
        QTreeWidget, QTreeView {{
            background-color: {theme['background']};
            color: {theme['text']};
            border: 1px solid {theme['panel_border']};
            outline: 0;
        }}
        QTreeWidget::item, QTreeView::item {{
            padding: 3px 4px;
            border: none;
        }}
        QTreeWidget::item:selected, QTreeView::item:selected {{
            background-color: {theme['button_bg']};
            color: {theme['text']};
        }}
        QTreeWidget::item:hover, QTreeView::item:hover {{
            background-color: {theme['current_line']};
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
        QComboBox, QLineEdit, QSpinBox, QDoubleSpinBox, QFontComboBox {{
            background-color: {theme['background']};
            color: {theme['text']};
            border: 1px solid {theme['panel_border']};
            padding: 4px 6px;
            border-radius: 3px;
        }}
        QGroupBox {{
            color: {theme['text']};
            border: 1px solid {theme['panel_border']};
            border-radius: 4px;
            margin-top: 8px;
            padding-top: 16px;
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            subcontrol-position: top left;
            padding: 4px 8px;
            color: {theme['accent']};
        }}
        QDialog {{
            background-color: {theme['panel_bg']};
            color: {theme['text']};
        }}
        QTabWidget::pane {{
            border: 1px solid {theme['panel_border']};
            background-color: {theme['panel_bg']};
        }}
        QTabBar::tab {{
            background-color: {theme['button_bg']};
            color: {theme['text']};
            padding: 6px 16px;
            border: 1px solid {theme['panel_border']};
            border-bottom: none;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
        }}
        QTabBar::tab:selected {{
            background-color: {theme['panel_bg']};
            color: {theme['accent']};
        }}
        QDialogButtonBox QPushButton {{
            min-width: 80px;
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
        QMenuBar {{
            background-color: {theme['panel_bg']};
            color: {theme['text']};
        }}
        QMenuBar::item:selected {{
            background-color: {theme['button_bg']};
        }}
        QMenu {{
            background-color: {theme['panel_bg']};
            color: {theme['text']};
            border: 1px solid {theme['panel_border']};
        }}
        QMenu::item:selected {{
            background-color: {theme['accent']};
        }}
        QToolBar {{
            background-color: {theme['panel_bg']};
            border: none;
            spacing: 4px;
        }}
        QProgressBar {{
            background-color: {theme['panel_border']};
            border-radius: 4px;
            text-align: center;
            color: {theme['text']};
        }}
        QProgressBar::chunk {{
            background-color: {theme['accent']};
            border-radius: 4px;
        }}
        """

    def list_themes(self) -> list[str]:
        return list(self.BUILTIN_THEMES.keys())
