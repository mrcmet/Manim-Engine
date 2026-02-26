"""AST-based code parser that extracts class/method/field structure."""

import ast

from core.models.code_structure import ClassNode, MethodNode, FieldNode


class CodeParser:
    @staticmethod
    def parse(code: str) -> list[ClassNode]:
        """Parse Python source and return a list of ClassNode objects.

        Only top-level classes are walked. Methods yield direct assignments
        (non-recursive — no descent into if/for/with blocks).

        Args:
            code: Python source code string.

        Returns:
            List of ClassNode, empty on syntax error or empty input.
        """
        if not code.strip():
            return []
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return []

        classes = []
        for node in tree.body:
            if not isinstance(node, ast.ClassDef):
                continue
            bases = [ast.unparse(b) for b in node.bases]
            cls = ClassNode(
                name=node.name,
                base_names=bases,
                line_number=node.lineno,
            )
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    method = MethodNode(name=item.name, line_number=item.lineno)
                    for stmt in item.body:
                        CodeParser._collect_fields(stmt, method.fields)
                    cls.methods.append(method)
            classes.append(cls)
        return classes

    @staticmethod
    def _collect_fields(stmt, fields: list[FieldNode]) -> None:
        """Extract direct assignments from a single statement (non-recursive).

        Args:
            stmt: An AST statement node.
            fields: List to append discovered FieldNode objects to.
        """
        if isinstance(stmt, ast.Assign):
            for target in stmt.targets:
                name = CodeParser._target_name(target)
                if name:
                    value_str = ast.unparse(stmt.value)[:60]
                    fields.append(
                        FieldNode(
                            name=name,
                            value_str=value_str,
                            line_number=stmt.lineno,
                        )
                    )
        elif isinstance(stmt, ast.AnnAssign) and stmt.value is not None:
            name = CodeParser._target_name(stmt.target)
            if name:
                value_str = ast.unparse(stmt.value)[:60]
                fields.append(
                    FieldNode(
                        name=name,
                        value_str=value_str,
                        line_number=stmt.lineno,
                    )
                )

    @staticmethod
    def _target_name(target) -> str | None:
        """Return a string name for an assignment target, or None.

        Args:
            target: An AST target node.

        Returns:
            Variable name string or None if not representable.
        """
        if isinstance(target, ast.Name):
            return target.id
        if isinstance(target, ast.Attribute):
            return ast.unparse(target)   # "self.radius"
        return None
