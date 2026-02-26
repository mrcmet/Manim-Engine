"""Prompt builder for generating Manim code with AI.

This module constructs prompts that guide AI models to generate
high-quality Manim animation code.
"""

# System prompt that defines the AI's role and capabilities
SYSTEM_PROMPT = """You are an expert Manim developer specialized in creating beautiful, mathematically precise animations.

Your role is to generate complete, working Manim code based on user descriptions. Follow these guidelines:

1. **Code Quality**: Write clean, well-structured code with proper imports and class definitions.

2. **Scene Structure**: Always create a Scene subclass. The main animation logic goes in the `construct` method.

3. **Manim Best Practices**:
   - Use appropriate mobjects (Text, MathTex, Circle, Square, Arrow, etc.)
   - Apply animations like Create, Write, FadeIn, FadeOut, Transform, ReplacementTransform
   - Use proper timing with wait() and run_time parameters
   - Position objects using .move_to(), .shift(), .next_to(), etc.
   - Use color constants (BLUE, RED, YELLOW, etc.) for better visuals

4. **Mathematical Accuracy**: When creating mathematical animations:
   - Use MathTex for LaTeX math expressions
   - Ensure formulas are correctly formatted
   - Use proper mathematical notation

5. **Code Format**: Always wrap your code in triple backticks with python language tag:
   ```python
   from manim import *

   class MyScene(Scene):
       def construct(self):
           # Your code here
   ```

6. **Completeness**: Provide complete, runnable code. Include all necessary imports and ensure the Scene class is properly defined.

7. **Comments**: Add brief comments to explain complex animations or mathematical concepts.

Generate creative, visually appealing animations that bring concepts to life."""


class PromptBuilder:
    """Builder class for constructing AI prompts.

    This class handles the assembly of system prompts, user prompts,
    and context (like existing code) into properly formatted messages
    for AI providers.
    """

    def __init__(self, system_prompt: str | None = None):
        """Initialize the prompt builder.

        Args:
            system_prompt: Custom system prompt. If None, uses SYSTEM_PROMPT.
        """
        self._system_prompt = system_prompt or SYSTEM_PROMPT

    def build(
        self,
        user_prompt: str,
        current_code: str | None = None,
        selected_code: str | None = None,
    ) -> list[dict]:
        """Build a messages list for AI generation.

        Args:
            user_prompt: The user's description of what animation to create.
            current_code: Optional existing code to refine or modify.
            selected_code: Optional highlighted code the user wants to focus on.

        Returns:
            A list of message dicts suitable for AI providers.

        Raises:
            ValueError: If user_prompt is empty or invalid.
        """
        if not user_prompt or not isinstance(user_prompt, str):
            raise ValueError("User prompt must be a non-empty string")

        user_prompt = user_prompt.strip()
        if not user_prompt:
            raise ValueError("User prompt must be a non-empty string")

        messages = []

        # Build the user message content
        content_parts = []

        if selected_code and selected_code.strip():
            # Focused selection with full file context
            content_parts.append("I have selected the following code to work on:")
            content_parts.append(f"```python\n{selected_code}\n```")
            if current_code:
                content_parts.append("\nFull file context:")
                content_parts.append(f"```python\n{current_code}\n```")
            content_parts.append(f"\nRequest: {user_prompt}")
        elif current_code:
            # If there's existing code, include it as context
            content_parts.append("Here is the current code:")
            content_parts.append(f"```python\n{current_code}\n```")
            content_parts.append("\nPlease modify or improve it based on this request:")
            content_parts.append(user_prompt)
        else:
            # No existing code, just use the prompt
            content_parts.append(user_prompt)

        content = "\n".join(content_parts)

        messages.append({
            "role": "user",
            "content": content
        })

        return messages

    def get_system_prompt(self) -> str:
        """Get the system prompt.

        Returns:
            The system prompt string.
        """
        return self._system_prompt

    def set_system_prompt(self, system_prompt: str) -> None:
        """Set a custom system prompt.

        Args:
            system_prompt: The new system prompt.

        Raises:
            ValueError: If system_prompt is empty or invalid.
        """
        if not system_prompt or not isinstance(system_prompt, str):
            raise ValueError("System prompt must be a non-empty string")

        system_prompt = system_prompt.strip()
        if not system_prompt:
            raise ValueError("System prompt must be a non-empty string")

        self._system_prompt = system_prompt
