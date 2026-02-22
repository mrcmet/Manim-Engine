"""Python and Manim syntax highlighter for the code editor."""

import json
import re
from pathlib import Path
from typing import Dict, List, Optional

from PySide6.QtCore import QRegularExpression, Qt
from PySide6.QtGui import QColor, QFont, QSyntaxHighlighter, QTextCharFormat, QTextDocument


class PythonManimHighlighter(QSyntaxHighlighter):
    """Syntax highlighter for Python code with Manim-specific keywords."""

    def __init__(self, document: Optional[QTextDocument] = None):
        """Initialize the highlighter with default dark theme.

        Args:
            document: The text document to highlight. Can be None.
        """
        super().__init__(document)

        # Load Manim keywords from JSON
        self._manim_keywords = self._load_manim_keywords()

        # Default dark theme colors
        self._theme = {
            "keyword": "#cba6f7",
            "builtin": "#f38ba8",
            "manim_class": "#89b4fa",
            "manim_method": "#a6e3a1",
            "string": "#a6e3a1",
            "comment": "#6c7086",
            "number": "#fab387",
            "decorator": "#f9e2af",
            "function": "#89dceb",
            "self": "#f38ba8",
        }

        # Initialize highlighting rules
        self._rules: List[tuple] = []
        self._setup_rules()

        # Multi-line string state tracking
        self._triple_single_quote_start = QRegularExpression("'''")
        self._triple_single_quote_end = QRegularExpression("'''")
        self._triple_double_quote_start = QRegularExpression('"""')
        self._triple_double_quote_end = QRegularExpression('"""')

    def _load_manim_keywords(self) -> Dict[str, List[str]]:
        """Load Manim keywords from JSON resource file.

        Returns:
            Dictionary containing keyword categories.
        """
        keywords_path = (
            Path(__file__).parent.parent.parent.parent / "resources" / "manim_keywords.json"
        )
        try:
            with open(keywords_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            # Return empty dict if file not found or invalid
            print(f"Warning: Could not load manim_keywords.json: {e}")
            return {
                "python_keywords": [],
                "manim_classes": [],
                "manim_animations": [],
                "manim_methods": [],
                "manim_constants": [],
            }

    def _create_format(self, color: str, bold: bool = False, italic: bool = False) -> QTextCharFormat:
        """Create a text format with the given color and style.

        Args:
            color: Hex color string (e.g., "#cba6f7").
            bold: Whether to make the text bold.
            italic: Whether to make the text italic.

        Returns:
            Configured QTextCharFormat.
        """
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(color))
        if bold:
            fmt.setFontWeight(QFont.Weight.Bold)
        if italic:
            fmt.setFontItalic(True)
        return fmt

    def _setup_rules(self) -> None:
        """Set up all syntax highlighting rules."""
        self._rules = []

        # Python keywords
        python_keywords = self._manim_keywords.get("python_keywords", [])
        if python_keywords:
            keyword_pattern = r"\b(" + "|".join(re.escape(kw) for kw in python_keywords) + r")\b"
            self._rules.append((
                QRegularExpression(keyword_pattern),
                self._create_format(self._theme["keyword"], bold=True)
            ))

        # Python builtins
        builtins = [
            "print", "len", "range", "str", "int", "float", "list", "dict", "tuple",
            "set", "bool", "type", "isinstance", "super", "property", "staticmethod",
            "classmethod", "enumerate", "zip", "map", "filter", "abs", "min", "max",
            "sum", "sorted", "reversed", "any", "all", "open", "round", "pow"
        ]
        builtin_pattern = r"\b(" + "|".join(re.escape(b) for b in builtins) + r")\b"
        self._rules.append((
            QRegularExpression(builtin_pattern),
            self._create_format(self._theme["builtin"])
        ))

        # Manim classes
        manim_classes = self._manim_keywords.get("manim_classes", [])
        manim_animations = self._manim_keywords.get("manim_animations", [])
        all_manim_classes = manim_classes + manim_animations
        if all_manim_classes:
            manim_class_pattern = r"\b(" + "|".join(re.escape(c) for c in all_manim_classes) + r")\b"
            self._rules.append((
                QRegularExpression(manim_class_pattern),
                self._create_format(self._theme["manim_class"], bold=True)
            ))

        # Manim methods
        manim_methods = self._manim_keywords.get("manim_methods", [])
        if manim_methods:
            manim_method_pattern = r"\b(" + "|".join(re.escape(m) for m in manim_methods) + r")\b"
            self._rules.append((
                QRegularExpression(manim_method_pattern),
                self._create_format(self._theme["manim_method"])
            ))

        # Manim constants
        manim_constants = self._manim_keywords.get("manim_constants", [])
        if manim_constants:
            manim_const_pattern = r"\b(" + "|".join(re.escape(c) for c in manim_constants) + r")\b"
            self._rules.append((
                QRegularExpression(manim_const_pattern),
                self._create_format(self._theme["manim_class"])
            ))

        # 'self' keyword
        self._rules.append((
            QRegularExpression(r"\bself\b"),
            self._create_format(self._theme["self"], italic=True)
        ))

        # Decorators
        self._rules.append((
            QRegularExpression(r"@\w+"),
            self._create_format(self._theme["decorator"])
        ))

        # Function definitions
        self._rules.append((
            QRegularExpression(r"\bdef\s+(\w+)"),
            self._create_format(self._theme["function"])
        ))

        # Numbers
        self._rules.append((
            QRegularExpression(r"\b\d+\.?\d*\b"),
            self._create_format(self._theme["number"])
        ))

        # Single-line strings (double quotes)
        self._rules.append((
            QRegularExpression(r'"[^"\\]*(\\.[^"\\]*)*"'),
            self._create_format(self._theme["string"])
        ))

        # Single-line strings (single quotes)
        self._rules.append((
            QRegularExpression(r"'[^'\\]*(\\.[^'\\]*)*'"),
            self._create_format(self._theme["string"])
        ))

        # Comments
        self._rules.append((
            QRegularExpression(r"#[^\n]*"),
            self._create_format(self._theme["comment"], italic=True)
        ))

    def set_theme(self, theme_dict: Dict[str, str]) -> None:
        """Update the color theme and refresh highlighting.

        Args:
            theme_dict: Dictionary mapping style names to hex color strings.
                Valid keys: keyword, builtin, manim_class, manim_method,
                string, comment, number, decorator, function, self.
        """
        self._theme.update(theme_dict)
        self._setup_rules()
        self.rehighlight()

    def highlightBlock(self, text: str) -> None:
        """Apply syntax highlighting to a single block of text.

        Args:
            text: The text block to highlight.
        """
        # Apply single-line rules
        for pattern, fmt in self._rules:
            match_iterator = pattern.globalMatch(text)
            while match_iterator.hasNext():
                match = match_iterator.next()
                start = match.capturedStart()
                length = match.capturedLength()
                self.setFormat(start, length, fmt)

        # Handle multi-line strings
        self._highlight_multiline_strings(text)

    def _highlight_multiline_strings(self, text: str) -> None:
        """Handle multi-line string highlighting.

        Args:
            text: The text block to check for multi-line strings.
        """
        # State values for tracking multi-line strings
        IN_TRIPLE_SINGLE = 1
        IN_TRIPLE_DOUBLE = 2

        string_format = self._create_format(self._theme["string"])

        # Check previous state
        previous_state = self.previousBlockState()
        start_index = 0
        add = 0

        # If we're continuing a multi-line string
        if previous_state == IN_TRIPLE_SINGLE:
            delimiter = self._triple_single_quote_end
            current_state = IN_TRIPLE_SINGLE
        elif previous_state == IN_TRIPLE_DOUBLE:
            delimiter = self._triple_double_quote_end
            current_state = IN_TRIPLE_DOUBLE
        else:
            # Look for start of triple-quoted string
            single_match = self._triple_single_quote_start.match(text)
            double_match = self._triple_double_quote_start.match(text)

            if single_match.hasMatch() and (
                not double_match.hasMatch() or single_match.capturedStart() < double_match.capturedStart()
            ):
                start_index = single_match.capturedStart()
                add = single_match.capturedLength()
                delimiter = self._triple_single_quote_end
                current_state = IN_TRIPLE_SINGLE
            elif double_match.hasMatch():
                start_index = double_match.capturedStart()
                add = double_match.capturedLength()
                delimiter = self._triple_double_quote_end
                current_state = IN_TRIPLE_DOUBLE
            else:
                self.setCurrentBlockState(0)
                return

        # Search for the end delimiter
        while start_index >= 0:
            end_match = delimiter.match(text, start_index + add)
            if end_match.hasMatch():
                end_index = end_match.capturedStart()
                length = end_index - start_index + end_match.capturedLength()
                self.setFormat(start_index, length, string_format)

                # Look for another multi-line string start
                single_match = self._triple_single_quote_start.match(text, start_index + length)
                double_match = self._triple_double_quote_start.match(text, start_index + length)

                if single_match.hasMatch() and (
                    not double_match.hasMatch() or single_match.capturedStart() < double_match.capturedStart()
                ):
                    start_index = single_match.capturedStart()
                    add = single_match.capturedLength()
                    delimiter = self._triple_single_quote_end
                    current_state = IN_TRIPLE_SINGLE
                elif double_match.hasMatch():
                    start_index = double_match.capturedStart()
                    add = double_match.capturedLength()
                    delimiter = self._triple_double_quote_end
                    current_state = IN_TRIPLE_DOUBLE
                else:
                    self.setCurrentBlockState(0)
                    return
            else:
                # No end found, highlight to end of block
                self.setFormat(start_index, len(text) - start_index, string_format)
                self.setCurrentBlockState(current_state)
                return

        self.setCurrentBlockState(0)
