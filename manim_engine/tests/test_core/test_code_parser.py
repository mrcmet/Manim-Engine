"""Tests for CodeParser AST walker."""

import pytest

from core.services.code_parser import CodeParser


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

SIMPLE_SCENE = """\
from manim import *

class CircleScene(Scene):
    def construct(self):
        circle = Circle()
        self.radius = 1.5
        self.play(Create(circle))
"""

TWO_CLASSES = """\
class SceneA(Scene):
    def construct(self):
        x = 10

class SceneB(MovingCameraScene):
    def setup(self):
        self.cam = 1
    def construct(self):
        y = 20
"""

ANNOTATED = """\
class MyScene(Scene):
    def construct(self):
        c: Circle = Circle()
        r = 2
"""

LONG_RHS = """\
class MyScene(Scene):
    def construct(self):
        x = some_function_with_a_very_long_name(argument_one, argument_two, argument_three)
"""

SYNTAX_ERROR = "class Broken(\n    def construct(self):\n        pass\n"

NO_CLASSES = """\
def helper():
    x = 1
"""

PASS_ONLY = """\
class EmptyScene(Scene):
    pass
"""


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_parse_empty():
    assert CodeParser.parse("") == []


def test_parse_whitespace_only():
    assert CodeParser.parse("   \n\t\n") == []


def test_parse_syntax_error():
    result = CodeParser.parse(SYNTAX_ERROR)
    assert result == []


def test_no_classes():
    result = CodeParser.parse(NO_CLASSES)
    assert result == []


def test_single_class_no_methods():
    result = CodeParser.parse(PASS_ONLY)
    assert len(result) == 1
    cls = result[0]
    assert cls.name == "EmptyScene"
    assert cls.base_names == ["Scene"]
    assert cls.methods == []


def test_single_class_with_construct():
    result = CodeParser.parse(SIMPLE_SCENE)
    assert len(result) == 1
    cls = result[0]
    assert cls.name == "CircleScene"
    assert cls.base_names == ["Scene"]
    assert cls.line_number >= 1

    assert len(cls.methods) == 1
    method = cls.methods[0]
    assert method.name == "construct"

    # Two assignments: circle and self.radius
    assert len(method.fields) == 2
    names = [f.name for f in method.fields]
    assert "circle" in names
    assert "self.radius" in names


def test_self_attribute_captured():
    result = CodeParser.parse(SIMPLE_SCENE)
    fields = result[0].methods[0].fields
    self_field = next(f for f in fields if f.name == "self.radius")
    assert self_field.value_str == "1.5"
    assert self_field.line_number >= 1


def test_annotated_assignment():
    result = CodeParser.parse(ANNOTATED)
    assert len(result) == 1
    fields = result[0].methods[0].fields
    names = [f.name for f in fields]
    assert "c" in names
    assert "r" in names
    c_field = next(f for f in fields if f.name == "c")
    assert "Circle" in c_field.value_str


def test_multiple_classes():
    result = CodeParser.parse(TWO_CLASSES)
    assert len(result) == 2
    names = [c.name for c in result]
    assert "SceneA" in names
    assert "SceneB" in names

    scene_b = next(c for c in result if c.name == "SceneB")
    assert scene_b.base_names == ["MovingCameraScene"]
    assert len(scene_b.methods) == 2
    method_names = [m.name for m in scene_b.methods]
    assert "setup" in method_names
    assert "construct" in method_names


def test_value_str_truncated():
    result = CodeParser.parse(LONG_RHS)
    fields = result[0].methods[0].fields
    assert len(fields) == 1
    assert len(fields[0].value_str) <= 60


def test_line_numbers_positive():
    result = CodeParser.parse(SIMPLE_SCENE)
    cls = result[0]
    assert cls.line_number > 0
    for method in cls.methods:
        assert method.line_number > 0
        for field in method.fields:
            assert field.line_number > 0
