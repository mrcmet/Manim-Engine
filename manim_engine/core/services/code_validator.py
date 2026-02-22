import ast


class CodeValidator:
    @staticmethod
    def validate_syntax(code: str) -> tuple[bool, str | None]:
        try:
            ast.parse(code)
            return True, None
        except SyntaxError as e:
            return False, f"Line {e.lineno}: {e.msg}"

    @staticmethod
    def has_scene_class(code: str) -> tuple[bool, str | None]:
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return False, None

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                for base in node.bases:
                    base_name = getattr(base, "id", getattr(base, "attr", ""))
                    if "Scene" in base_name:
                        return True, node.name
        return False, None
