import ast
import re
from typing import Any

from core.models.scene_code import VariableInfo


class VariableParser:
    @staticmethod
    def extract_variables(code: str) -> list[VariableInfo]:
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return []

        variables = []
        for node in tree.body:
            # Only top-level assignments (before class/function defs)
            if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                break

            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        var_info = VariableParser._extract_from_assign(
                            target.id, node.value, node.lineno
                        )
                        if var_info:
                            variables.append(var_info)

            elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                if node.value is not None:
                    var_info = VariableParser._extract_from_assign(
                        node.target.id, node.value, node.lineno
                    )
                    if var_info:
                        variables.append(var_info)

        return variables

    @staticmethod
    def _extract_from_assign(
        name: str, value_node: ast.expr, lineno: int
    ) -> VariableInfo | None:
        try:
            value = ast.literal_eval(value_node)
        except (ValueError, TypeError):
            # Not a literal — could be a Manim constant reference
            if isinstance(value_node, ast.Name):
                return VariableInfo(
                    name=name,
                    value=value_node.id,
                    var_type="constant",
                    line_number=lineno,
                    editable=False,
                )
            return None

        var_type = VariableParser._detect_type(name, value)
        editable = var_type in ("int", "float", "str", "bool", "color", "tuple")

        return VariableInfo(
            name=name,
            value=value,
            var_type=var_type,
            line_number=lineno,
            editable=editable,
        )

    @staticmethod
    def _detect_type(name: str, value: Any) -> str:
        if "color" in name.lower():
            return "color"
        if isinstance(value, bool):
            return "bool"
        if isinstance(value, int):
            return "int"
        if isinstance(value, float):
            return "float"
        if isinstance(value, str):
            if re.match(r"^#[0-9a-fA-F]{6}$", value):
                return "color"
            return "str"
        if isinstance(value, tuple):
            return "tuple"
        if isinstance(value, list):
            return "list"
        return "unknown"

    @staticmethod
    def replace_variable(code: str, var_name: str, new_value: Any) -> str:
        lines = code.split("\n")
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return code

        for node in tree.body:
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == var_name:
                        line_idx = node.lineno - 1
                        line = lines[line_idx]
                        # Find the '=' and replace everything after it
                        eq_pos = line.index("=")
                        prefix = line[: eq_pos + 1]
                        lines[line_idx] = f"{prefix} {repr(new_value)}"
                        return "\n".join(lines)

            elif isinstance(node, ast.AnnAssign) and isinstance(
                node.target, ast.Name
            ):
                if node.target.id == var_name:
                    line_idx = node.lineno - 1
                    line = lines[line_idx]
                    eq_pos = line.index("=")
                    prefix = line[: eq_pos + 1]
                    lines[line_idx] = f"{prefix} {repr(new_value)}"
                    return "\n".join(lines)

        return code
