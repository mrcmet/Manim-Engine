"""Parser for AI-generated responses.

This module extracts and validates Manim code from AI model responses,
handling various response formats and ensuring code quality.
"""

import ast
import re


class ResponseParser:
    """Parser for extracting and validating code from AI responses.

    This class handles the parsing of AI-generated text to extract
    Python code blocks, validate syntax, and extract scene class names.
    """

    # Pattern to match code blocks with python language tag
    CODE_BLOCK_PATTERN = re.compile(
        r'```python\s*\n(.*?)```',
        re.DOTALL | re.IGNORECASE
    )

    # Fallback pattern for code blocks without language tag
    GENERIC_CODE_BLOCK_PATTERN = re.compile(
        r'```\s*\n(.*?)```',
        re.DOTALL
    )

    def extract_code(self, response: str) -> str:
        """Extract Python code from an AI response.

        This method looks for code blocks in markdown format,
        validates the syntax, and returns the code.

        Args:
            response: The AI-generated response text.

        Returns:
            The extracted and validated Python code.

        Raises:
            ValueError: If no valid code is found or if the code has syntax errors.
        """
        if not response or not isinstance(response, str):
            raise ValueError("Response must be a non-empty string")

        response = response.strip()
        if not response:
            raise ValueError("Response must be a non-empty string")

        # Try to find python code blocks
        python_blocks = self.CODE_BLOCK_PATTERN.findall(response)

        # If no python blocks found, try generic code blocks
        if not python_blocks:
            python_blocks = self.GENERIC_CODE_BLOCK_PATTERN.findall(response)

        if not python_blocks:
            raise ValueError(
                "No code blocks found in response. "
                "Please ensure the AI response contains code wrapped in ```python blocks."
            )

        # If multiple blocks found, use the longest one (most likely to be complete)
        if len(python_blocks) > 1:
            code = max(python_blocks, key=len)
        else:
            code = python_blocks[0]

        code = code.strip()

        if not code:
            raise ValueError("Extracted code block is empty")

        # Validate the Python syntax
        try:
            ast.parse(code)
        except SyntaxError as e:
            raise ValueError(
                f"Code has syntax errors at line {e.lineno}: {e.msg}"
            ) from e
        except Exception as e:
            raise ValueError(
                f"Code validation failed: {str(e)}"
            ) from e

        return code

    def find_scene_class_name(self, code: str) -> str | None:
        """Find the name of the Scene subclass in the code.

        This is useful for identifying which class to run for rendering.

        Args:
            code: The Python code to analyze.

        Returns:
            The name of the Scene subclass if found, None otherwise.
        """
        if not code or not isinstance(code, str):
            return None

        try:
            tree = ast.parse(code)
        except Exception:
            return None

        # Look for class definitions
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # Check if it inherits from Scene or any Scene subclass
                for base in node.bases:
                    base_name = None

                    # Handle direct name reference (e.g., Scene)
                    if isinstance(base, ast.Name):
                        base_name = base.id
                    # Handle attribute reference (e.g., manim.Scene)
                    elif isinstance(base, ast.Attribute):
                        base_name = base.attr

                    # Check if it's Scene or contains "Scene" in the name
                    if base_name and ('Scene' in base_name or base_name == 'Scene'):
                        return node.name

        return None

    def validate_manim_imports(self, code: str) -> tuple[bool, str | None]:
        """Validate that the code has proper Manim imports.

        Args:
            code: The Python code to validate.

        Returns:
            Tuple of (is_valid, error_message).
        """
        if not code:
            return False, "Code is empty"

        try:
            tree = ast.parse(code)
        except Exception as e:
            return False, f"Code has syntax errors: {str(e)}"

        # Check for Manim imports
        has_manim_import = False

        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                if isinstance(node, ast.Import):
                    # Check for: import manim
                    for alias in node.names:
                        if 'manim' in alias.name.lower():
                            has_manim_import = True
                            break
                elif isinstance(node, ast.ImportFrom):
                    # Check for: from manim import *
                    if node.module and 'manim' in node.module.lower():
                        has_manim_import = True
                        break

            if has_manim_import:
                break

        if not has_manim_import:
            return False, "Code does not import Manim. Add 'from manim import *' at the top."

        return True, None

    def validate_scene_class(self, code: str) -> tuple[bool, str | None]:
        """Validate that the code contains a Scene subclass.

        Args:
            code: The Python code to validate.

        Returns:
            Tuple of (is_valid, error_message).
        """
        scene_class_name = self.find_scene_class_name(code)

        if scene_class_name is None:
            return False, "Code does not contain a Scene subclass. Create a class that inherits from Scene."

        return True, None
