"""Tests for the PromptBuilder class."""

import pytest
from ai.prompt_builder import PromptBuilder, SYSTEM_PROMPT


class TestPromptBuilder:
    """Test suite for PromptBuilder."""

    def test_build_without_current_code(self):
        """Test building a prompt without existing code."""
        builder = PromptBuilder()
        user_prompt = "Create a circle that grows and changes color"

        messages = builder.build(user_prompt)

        assert len(messages) == 1
        assert messages[0]["role"] == "user"
        assert user_prompt in messages[0]["content"]
        assert "current code" not in messages[0]["content"].lower()

    def test_build_with_current_code(self):
        """Test building a prompt with existing code."""
        builder = PromptBuilder()
        user_prompt = "Make the circle blue instead of red"
        current_code = "from manim import *\n\nclass MyScene(Scene):\n    pass"

        messages = builder.build(user_prompt, current_code)

        assert len(messages) == 1
        assert messages[0]["role"] == "user"
        assert user_prompt in messages[0]["content"]
        assert current_code in messages[0]["content"]
        assert "current code" in messages[0]["content"].lower()

    def test_build_raises_on_empty_prompt(self):
        """Test that build raises ValueError for empty prompts."""
        builder = PromptBuilder()

        with pytest.raises(ValueError, match="non-empty string"):
            builder.build("")

        with pytest.raises(ValueError, match="non-empty string"):
            builder.build("   ")

    def test_build_raises_on_invalid_prompt(self):
        """Test that build raises ValueError for invalid prompt types."""
        builder = PromptBuilder()

        with pytest.raises(ValueError, match="non-empty string"):
            builder.build(None)

        with pytest.raises(ValueError, match="non-empty string"):
            builder.build(123)

    def test_get_system_prompt(self):
        """Test getting the system prompt."""
        builder = PromptBuilder()

        system_prompt = builder.get_system_prompt()

        assert system_prompt == SYSTEM_PROMPT
        assert "Manim" in system_prompt
        assert "Scene" in system_prompt

    def test_custom_system_prompt(self):
        """Test initializing with a custom system prompt."""
        custom_prompt = "You are a custom AI assistant."
        builder = PromptBuilder(system_prompt=custom_prompt)

        assert builder.get_system_prompt() == custom_prompt

    def test_set_system_prompt(self):
        """Test setting a custom system prompt."""
        builder = PromptBuilder()
        custom_prompt = "New system prompt for testing."

        builder.set_system_prompt(custom_prompt)

        assert builder.get_system_prompt() == custom_prompt

    def test_set_system_prompt_raises_on_empty(self):
        """Test that set_system_prompt raises ValueError for empty prompts."""
        builder = PromptBuilder()

        with pytest.raises(ValueError, match="non-empty string"):
            builder.set_system_prompt("")

        with pytest.raises(ValueError, match="non-empty string"):
            builder.set_system_prompt("   ")

    def test_set_system_prompt_raises_on_invalid_type(self):
        """Test that set_system_prompt raises ValueError for invalid types."""
        builder = PromptBuilder()

        with pytest.raises(ValueError, match="non-empty string"):
            builder.set_system_prompt(None)

        with pytest.raises(ValueError, match="non-empty string"):
            builder.set_system_prompt(123)

    def test_build_preserves_whitespace_in_code(self):
        """Test that code blocks preserve whitespace and formatting."""
        builder = PromptBuilder()
        current_code = "def foo():\n    return 42"

        messages = builder.build("Update this", current_code)

        assert current_code in messages[0]["content"]

    def test_build_with_selected_code(self):
        """Test building a prompt with a highlighted code selection."""
        builder = PromptBuilder()
        user_prompt = "Refactor this function"
        current_code = "from manim import *\n\nclass MyScene(Scene):\n    def construct(self):\n        c = Circle()\n        self.add(c)"
        selected_code = "c = Circle()\n        self.add(c)"

        messages = builder.build(user_prompt, current_code, selected_code)

        assert len(messages) == 1
        content = messages[0]["content"]
        assert "I have selected the following code" in content
        assert selected_code in content
        assert current_code in content
        assert user_prompt in content

    def test_build_selected_code_without_full_file(self):
        """Test that selected_code works even when current_code is None."""
        builder = PromptBuilder()
        selected_code = "x = 42"

        messages = builder.build("Explain this", selected_code=selected_code)

        content = messages[0]["content"]
        assert "I have selected the following code" in content
        assert selected_code in content

    def test_build_selected_code_overrides_current_code_header(self):
        """Selected code path should not use the 'Here is the current code' header."""
        builder = PromptBuilder()
        current_code = "from manim import *"
        selected_code = "x = 1"

        messages = builder.build("Fix it", current_code, selected_code)

        content = messages[0]["content"]
        assert "Here is the current code" not in content
        assert "I have selected the following code" in content

    def test_build_empty_selected_code_falls_back_to_current_code(self):
        """Empty/whitespace selected_code should behave like no selection."""
        builder = PromptBuilder()
        current_code = "from manim import *"

        messages = builder.build("Improve this", current_code, selected_code="   ")

        content = messages[0]["content"]
        assert "Here is the current code" in content
        assert "I have selected the following code" not in content
