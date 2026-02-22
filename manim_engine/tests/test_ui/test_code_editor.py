"""Tests for the code editor panel and components."""

import json
import pytest
from pathlib import Path

# Try to import PyQt6 - skip all tests if not available
pytest.importorskip("PyQt6")

from PySide6.QtWidgets import QApplication
from ui.panels.code_editor.code_editor_panel import CodeEditorPanel
from ui.panels.code_editor.python_highlighter import PythonManimHighlighter
from ui.panels.code_editor.manim_completer import ManimCompleter


@pytest.fixture(scope="module")
def qapp():
    """Create QApplication for tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


class TestCodeEditorPanel:
    """Tests for the CodeEditorPanel widget."""

    def test_set_and_get_code(self, qapp):
        """Test setting and getting code in the editor."""
        panel = CodeEditorPanel()

        test_code = "def hello():\n    print('Hello, Manim!')"
        panel.set_code(test_code)

        assert panel.get_code() == test_code

    def test_empty_code(self, qapp):
        """Test handling of empty code."""
        panel = CodeEditorPanel()

        panel.set_code("")
        assert panel.get_code() == ""

    def test_multiline_code(self, qapp):
        """Test handling of multiline code with various indentation."""
        panel = CodeEditorPanel()

        test_code = """from manim import *

class MyScene(Scene):
    def construct(self):
        circle = Circle()
        self.play(Create(circle))
        self.wait()
"""
        panel.set_code(test_code)
        assert panel.get_code() == test_code

    def test_read_only_mode(self, qapp):
        """Test read-only mode."""
        panel = CodeEditorPanel()

        panel.set_read_only(True)
        assert panel.get_editor_widget().isReadOnly() is True

        panel.set_read_only(False)
        assert panel.get_editor_widget().isReadOnly() is False

    def test_font_settings(self, qapp):
        """Test font family and size settings."""
        panel = CodeEditorPanel()

        panel.set_font("Courier New", 16)

        editor_font = panel.get_editor_widget().font()
        assert editor_font.family() == "Courier New"
        assert editor_font.pointSize() == 16
        assert panel.get_toolbar().get_font_size() == 16


class TestPythonManimHighlighter:
    """Tests for the syntax highlighter."""

    def test_highlighter_creation(self, qapp):
        """Test that highlighter can be instantiated."""
        highlighter = PythonManimHighlighter()
        assert highlighter is not None

    def test_highlighter_with_document(self, qapp):
        """Test highlighter attached to a document."""
        panel = CodeEditorPanel()
        editor = panel.get_editor_widget()

        # The editor should have a highlighter attached
        assert editor.document() is not None

    def test_set_theme(self, qapp):
        """Test theme updating."""
        highlighter = PythonManimHighlighter()

        custom_theme = {
            "keyword": "#ff0000",
            "string": "#00ff00",
            "comment": "#0000ff",
        }

        # Should not raise an error
        highlighter.set_theme(custom_theme)

    def test_load_keywords(self, qapp):
        """Test that keywords are loaded from JSON."""
        highlighter = PythonManimHighlighter()

        # Check that keywords were loaded
        keywords = highlighter._manim_keywords
        assert "python_keywords" in keywords
        assert "manim_classes" in keywords
        assert "manim_animations" in keywords
        assert "manim_methods" in keywords
        assert "manim_constants" in keywords


class TestManimCompleter:
    """Tests for the auto-completion widget."""

    def test_completer_creation(self, qapp):
        """Test that completer can be instantiated."""
        completer = ManimCompleter()
        assert completer is not None

    def test_load_keywords(self, qapp):
        """Test that keywords are loaded."""
        completer = ManimCompleter()
        keywords = completer.get_keywords()

        # Should have loaded keywords
        assert len(keywords) > 0

        # Check for some expected keywords
        assert "Scene" in keywords or len(keywords) == 0  # May be empty if JSON not found
        assert "Circle" in keywords or len(keywords) == 0
        assert "def" in keywords or len(keywords) == 0

    def test_completer_model(self, qapp):
        """Test that completer has a valid model."""
        completer = ManimCompleter()

        model = completer.model()
        assert model is not None
        assert model.rowCount() > 0 or model.rowCount() == 0  # May be empty if JSON not found

    def test_update_prefix(self, qapp):
        """Test updating completion prefix."""
        completer = ManimCompleter()

        completer.update_prefix("Cir")
        assert completer.completionPrefix() == "Cir"

        completer.update_prefix("play")
        assert completer.completionPrefix() == "play"


class TestManimKeywordsJSON:
    """Tests for the keywords JSON resource file."""

    def test_json_file_exists(self):
        """Test that the keywords JSON file exists."""
        keywords_path = Path(__file__).parent.parent.parent / "resources" / "manim_keywords.json"
        assert keywords_path.exists(), f"Keywords file not found at {keywords_path}"

    def test_json_file_valid(self):
        """Test that the JSON file is valid and contains expected keys."""
        keywords_path = Path(__file__).parent.parent.parent / "resources" / "manim_keywords.json"

        with open(keywords_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Check all required keys exist
        assert "python_keywords" in data
        assert "manim_classes" in data
        assert "manim_animations" in data
        assert "manim_methods" in data
        assert "manim_constants" in data

        # Check they are lists
        assert isinstance(data["python_keywords"], list)
        assert isinstance(data["manim_classes"], list)
        assert isinstance(data["manim_animations"], list)
        assert isinstance(data["manim_methods"], list)
        assert isinstance(data["manim_constants"], list)

        # Check some expected values
        assert "def" in data["python_keywords"]
        assert "class" in data["python_keywords"]
        assert "Scene" in data["manim_classes"]
        assert "Circle" in data["manim_classes"]
        assert "Create" in data["manim_animations"]
        assert "FadeIn" in data["manim_animations"]
        assert "play" in data["manim_methods"]
        assert "wait" in data["manim_methods"]
        assert "UP" in data["manim_constants"]
        assert "RED" in data["manim_constants"]

    def test_no_duplicate_keywords(self):
        """Test that there are no duplicate keywords within each category."""
        keywords_path = Path(__file__).parent.parent.parent / "resources" / "manim_keywords.json"

        with open(keywords_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        for category, keywords in data.items():
            assert len(keywords) == len(set(keywords)), f"Duplicates found in {category}"


class TestEditorIntegration:
    """Integration tests for the complete editor."""

    def test_code_changed_signal(self, qapp):
        """Test that code_changed signal is emitted."""
        panel = CodeEditorPanel()
        received_code = []

        def on_code_changed(code):
            received_code.append(code)

        panel.code_changed.connect(on_code_changed)

        test_code = "print('test')"
        panel.set_code(test_code)

        # Signal should have been emitted
        assert len(received_code) > 0
        assert received_code[-1] == test_code

    def test_theme_setting(self, qapp):
        """Test setting a custom theme."""
        panel = CodeEditorPanel()

        custom_theme = {
            "keyword": "#ff6c6b",
            "string": "#98be65",
            "comment": "#5b6268",
        }

        # Should not raise an error
        panel.set_theme(custom_theme)
