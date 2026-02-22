"""Tests for the ResponseParser class."""

import pytest
from ai.response_parser import ResponseParser


class TestResponseParser:
    """Test suite for ResponseParser."""

    def test_extract_code_from_python_block(self):
        """Test extracting code from a python markdown block."""
        parser = ResponseParser()
        response = """
Here's the code you requested:

```python
from manim import *

class MyScene(Scene):
    def construct(self):
        circle = Circle()
        self.play(Create(circle))
```

This creates a simple circle animation.
"""

        code = parser.extract_code(response)

        assert "from manim import *" in code
        assert "class MyScene(Scene):" in code
        assert "def construct(self):" in code

    def test_extract_code_from_generic_block(self):
        """Test extracting code from a generic markdown block."""
        parser = ResponseParser()
        response = """
```
from manim import *

class TestScene(Scene):
    pass
```
"""

        code = parser.extract_code(response)

        assert "from manim import *" in code
        assert "class TestScene(Scene):" in code

    def test_extract_code_multiple_blocks_returns_longest(self):
        """Test that when multiple blocks exist, the longest is returned."""
        parser = ResponseParser()
        response = """
```python
x = 1
```

Here's the full code:

```python
from manim import *

class MyScene(Scene):
    def construct(self):
        self.play(Create(Circle()))
```
"""

        code = parser.extract_code(response)

        assert "from manim import *" in code
        assert "x = 1" not in code  # Should skip the shorter block

    def test_extract_code_raises_on_no_blocks(self):
        """Test that extract_code raises ValueError when no code blocks found."""
        parser = ResponseParser()
        response = "This is just text without any code blocks."

        with pytest.raises(ValueError, match="No code blocks found"):
            parser.extract_code(response)

    def test_extract_code_raises_on_empty_response(self):
        """Test that extract_code raises ValueError for empty response."""
        parser = ResponseParser()

        with pytest.raises(ValueError, match="non-empty string"):
            parser.extract_code("")

        with pytest.raises(ValueError, match="non-empty string"):
            parser.extract_code("   ")

    def test_extract_code_raises_on_syntax_error(self):
        """Test that extract_code raises ValueError for invalid Python syntax."""
        parser = ResponseParser()
        response = """
```python
this is not valid python syntax!!!
def broken
```
"""

        with pytest.raises(ValueError, match="syntax errors"):
            parser.extract_code(response)

    def test_find_scene_class_name_basic(self):
        """Test finding a Scene subclass name."""
        parser = ResponseParser()
        code = """
from manim import *

class MyAnimation(Scene):
    def construct(self):
        pass
"""

        scene_name = parser.find_scene_class_name(code)

        assert scene_name == "MyAnimation"

    def test_find_scene_class_name_with_module_prefix(self):
        """Test finding Scene class when imported with module prefix."""
        parser = ResponseParser()
        code = """
import manim

class TestScene(manim.Scene):
    pass
"""

        scene_name = parser.find_scene_class_name(code)

        assert scene_name == "TestScene"

    def test_find_scene_class_name_multiple_classes(self):
        """Test finding Scene class when multiple classes exist."""
        parser = ResponseParser()
        code = """
from manim import *

class Helper:
    pass

class MainScene(Scene):
    pass
"""

        scene_name = parser.find_scene_class_name(code)

        assert scene_name == "MainScene"

    def test_find_scene_class_name_returns_none_when_not_found(self):
        """Test that None is returned when no Scene subclass is found."""
        parser = ResponseParser()
        code = """
class NotAScene:
    pass
"""

        scene_name = parser.find_scene_class_name(code)

        assert scene_name is None

    def test_find_scene_class_name_handles_invalid_code(self):
        """Test that find_scene_class_name handles invalid code gracefully."""
        parser = ResponseParser()

        scene_name = parser.find_scene_class_name("not valid python!!!")

        assert scene_name is None

    def test_validate_manim_imports_with_star_import(self):
        """Test validating code with 'from manim import *'."""
        parser = ResponseParser()
        code = "from manim import *\n\nclass MyScene(Scene):\n    pass"

        is_valid, error = parser.validate_manim_imports(code)

        assert is_valid is True
        assert error is None

    def test_validate_manim_imports_with_explicit_import(self):
        """Test validating code with explicit manim imports."""
        parser = ResponseParser()
        code = "from manim import Scene, Circle\n\nclass MyScene(Scene):\n    pass"

        is_valid, error = parser.validate_manim_imports(code)

        assert is_valid is True
        assert error is None

    def test_validate_manim_imports_with_module_import(self):
        """Test validating code with module-level import."""
        parser = ResponseParser()
        code = "import manim\n\nclass MyScene(manim.Scene):\n    pass"

        is_valid, error = parser.validate_manim_imports(code)

        assert is_valid is True
        assert error is None

    def test_validate_manim_imports_fails_without_import(self):
        """Test that validation fails when no manim import is present."""
        parser = ResponseParser()
        code = "class MyScene(Scene):\n    pass"

        is_valid, error = parser.validate_manim_imports(code)

        assert is_valid is False
        assert "import" in error.lower()

    def test_validate_scene_class_success(self):
        """Test validating that code contains a Scene subclass."""
        parser = ResponseParser()
        code = "from manim import *\n\nclass MyScene(Scene):\n    def construct(self):\n        pass"

        is_valid, error = parser.validate_scene_class(code)

        assert is_valid is True
        assert error is None

    def test_validate_scene_class_fails_without_scene(self):
        """Test that validation fails when no Scene subclass is present."""
        parser = ResponseParser()
        code = "from manim import *\n\nclass NotAScene:\n    pass"

        is_valid, error = parser.validate_scene_class(code)

        assert is_valid is False
        assert "Scene" in error
