"""Dataclasses representing parsed code structure (classes, methods, fields)."""

from dataclasses import dataclass, field as dc_field


@dataclass
class FieldNode:
    name: str        # "circle", "self.radius"
    value_str: str   # ast.unparse of RHS, truncated to 60 chars
    line_number: int


@dataclass
class MethodNode:
    name: str
    line_number: int
    fields: list["FieldNode"] = dc_field(default_factory=list)


@dataclass
class ClassNode:
    name: str
    base_names: list[str]   # ["Scene"], ["MovingCameraScene"], etc.
    line_number: int
    methods: list["MethodNode"] = dc_field(default_factory=list)
