# Agent 2: AI Provider System

## Scope
Build the AI provider abstraction layer, all 4 provider implementations (Claude, ChatGPT, Gemini, Ollama), prompt engineering, and response parsing.

## Files to Create

```
manim_engine/
└── ai/
    ├── __init__.py
    ├── provider_base.py
    ├── provider_registry.py
    ├── ai_service.py
    ├── ai_worker.py
    ├── prompt_builder.py
    ├── response_parser.py
    └── providers/
        ├── __init__.py
        ├── anthropic_provider.py
        ├── openai_provider.py
        ├── gemini_provider.py
        └── ollama_provider.py
└── tests/
    └── test_ai/
        ├── __init__.py
        ├── test_prompt_builder.py
        ├── test_response_parser.py
        └── test_providers.py
```

---

## Detailed Specifications

### `provider_base.py` — Abstract Base

```python
from abc import ABC, abstractmethod

class AIProviderError(Exception):
    """Raised when an AI provider call fails."""
    pass

class AIProvider(ABC):
    def __init__(self, config: AIProviderConfig):
        self._config = config

    @abstractmethod
    async def generate(self, messages: list[dict], system_prompt: str | None = None) -> str:
        """Send messages to the AI model.
        messages format: [{"role": "user", "content": "..."}]
        Returns raw response text. Raises AIProviderError on failure."""
        ...

    @abstractmethod
    def validate_config(self) -> tuple[bool, str | None]:
        """Check if API key/settings are configured. Returns (valid, error_message)."""
        ...

    @property
    def name(self) -> str:
        return self._config.provider_name

    @property
    def model(self) -> str:
        return self._config.model_name
```

### `provider_registry.py`

```python
class ProviderRegistry:
    def __init__(self):
        self._providers: dict[str, type[AIProvider]] = {}
        self._instances: dict[str, AIProvider] = {}

    def register(self, name: str, provider_class: type[AIProvider]) -> None:
        """Register a provider class by name."""

    def create_provider(self, name: str, config: AIProviderConfig) -> AIProvider:
        """Instantiate a registered provider with config. Cache instance."""

    def get_provider(self, name: str) -> AIProvider:
        """Get cached provider instance. Raises KeyError if not created."""

    def list_providers(self) -> list[str]:
        """Return registered provider names."""

    def has_provider(self, name: str) -> bool: ...
```

### Provider Implementations

All providers use `httpx.AsyncClient` for HTTP calls.

**`anthropic_provider.py`** — Claude (Anthropic API)
```python
class AnthropicProvider(AIProvider):
    API_URL = "https://api.anthropic.com/v1/messages"

    async def generate(self, messages, system_prompt=None):
        async with httpx.AsyncClient() as client:
            headers = {
                "x-api-key": self._config.api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            }
            body = {
                "model": self._config.model_name or "claude-sonnet-4-5-20250929",
                "max_tokens": self._config.max_tokens,
                "messages": messages,
            }
            if system_prompt:
                body["system"] = system_prompt
            response = await client.post(self.API_URL, headers=headers, json=body, timeout=60)
            response.raise_for_status()
            data = response.json()
            return data["content"][0]["text"]

    def validate_config(self):
        if not self._config.api_key:
            return False, "Anthropic API key not set"
        return True, None
```

**`openai_provider.py`** — ChatGPT (OpenAI API)
```python
class OpenAIProvider(AIProvider):
    API_URL = "https://api.openai.com/v1/chat/completions"

    async def generate(self, messages, system_prompt=None):
        msgs = []
        if system_prompt:
            msgs.append({"role": "system", "content": system_prompt})
        msgs.extend(messages)
        async with httpx.AsyncClient() as client:
            headers = {
                "Authorization": f"Bearer {self._config.api_key}",
                "Content-Type": "application/json",
            }
            body = {
                "model": self._config.model_name or "gpt-4o",
                "messages": msgs,
                "max_tokens": self._config.max_tokens,
                "temperature": self._config.temperature,
            }
            response = await client.post(self.API_URL, headers=headers, json=body, timeout=60)
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]

    def validate_config(self):
        if not self._config.api_key:
            return False, "OpenAI API key not set"
        return True, None
```

**`gemini_provider.py`** — Google Gemini API
```python
class GeminiProvider(AIProvider):
    API_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

    async def generate(self, messages, system_prompt=None):
        url = self.API_URL.format(model=self._config.model_name or "gemini-2.0-flash")
        contents = []
        if system_prompt:
            contents.append({"role": "user", "parts": [{"text": system_prompt}]})
            contents.append({"role": "model", "parts": [{"text": "Understood."}]})
        for msg in messages:
            role = "user" if msg["role"] == "user" else "model"
            contents.append({"role": role, "parts": [{"text": msg["content"]}]})
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url, params={"key": self._config.api_key},
                json={"contents": contents,
                       "generationConfig": {"maxOutputTokens": self._config.max_tokens,
                                            "temperature": self._config.temperature}},
                timeout=60
            )
            response.raise_for_status()
            return response.json()["candidates"][0]["content"]["parts"][0]["text"]

    def validate_config(self):
        if not self._config.api_key:
            return False, "Gemini API key not set"
        return True, None
```

**`ollama_provider.py`** — Local Ollama
```python
class OllamaProvider(AIProvider):
    async def generate(self, messages, system_prompt=None):
        base_url = self._config.base_url or "http://localhost:11434"
        msgs = []
        if system_prompt:
            msgs.append({"role": "system", "content": system_prompt})
        msgs.extend(messages)
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{base_url}/api/chat",
                json={"model": self._config.model_name or "llama3",
                      "messages": msgs, "stream": False},
                timeout=120  # local models can be slow
            )
            response.raise_for_status()
            return response.json()["message"]["content"]

    def validate_config(self):
        if not self._config.model_name:
            return False, "Ollama model name not set"
        return True, None
```

### `prompt_builder.py`

```python
SYSTEM_PROMPT = """You are a Manim Community animation expert. Generate a single Manim Scene class that creates a 5-15 second animation.

Rules:
1. Return ONLY Python code wrapped in ```python ... ``` markers
2. Use `from manim import *` at the top
3. Name the main class `GeneratedScene(Scene)`
4. Define tweakable values as TOP-LEVEL variables before the class (e.g., RADIUS = 2, TEXT_COLOR = BLUE)
5. Use descriptive variable names with ALL_CAPS for constants
6. Keep animations between 5-15 seconds total
7. Use self.play() with appropriate animation durations
8. Ensure the code is complete and runnable with `manim render`"""

class PromptBuilder:
    def build(self, user_prompt: str, current_code: str | None = None) -> list[dict]:
        """Build message list for AI provider.

        If current_code is provided, include it as context with instruction
        to modify/improve it based on the new prompt.

        Returns list of message dicts: [{"role": "user", "content": "..."}]
        """
        content_parts = []
        if current_code:
            content_parts.append(f"Here is the current Manim code:\n```python\n{current_code}\n```\n")
            content_parts.append(f"Please modify this code based on the following request:\n{user_prompt}")
        else:
            content_parts.append(f"Create a Manim animation: {user_prompt}")
        return [{"role": "user", "content": "\n".join(content_parts)}]

    def get_system_prompt(self) -> str:
        return SYSTEM_PROMPT
```

### `response_parser.py`

```python
import re
import ast

class ResponseParser:
    CODE_BLOCK_PATTERN = re.compile(r"```python\s*\n(.*?)```", re.DOTALL)

    def extract_code(self, response: str) -> str:
        """Extract Python code from AI response.

        Strategy:
        1. Look for ```python ... ``` code blocks
        2. If multiple blocks, take the longest one
        3. If no blocks, try the entire response as code
        4. Validate with ast.parse()
        5. Raise ValueError if no valid code found
        """
        matches = self.CODE_BLOCK_PATTERN.findall(response)
        if matches:
            # Take the longest code block (most likely the full scene)
            code = max(matches, key=len).strip()
        else:
            code = response.strip()

        # Validate syntax
        try:
            ast.parse(code)
        except SyntaxError as e:
            raise ValueError(f"Generated code has syntax errors: {e}")

        return code

    def find_scene_class_name(self, code: str) -> str | None:
        """Find the name of the Scene subclass in the code."""
        tree = ast.parse(code)
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                for base in node.bases:
                    base_name = getattr(base, 'id', getattr(base, 'attr', ''))
                    if 'Scene' in base_name:
                        return node.name
        return None
```

### `ai_worker.py` — QThread for Async AI Calls

```python
from PySide6.QtCore import QThread, Signal
import asyncio

class AIWorker(QThread):
    """Runs async AI generation on a background thread."""
    finished = Signal(str)   # generated code
    failed = Signal(str)     # error message

    def __init__(self, provider: AIProvider, messages: list[dict],
                 system_prompt: str, response_parser: ResponseParser):
        super().__init__()
        self._provider = provider
        self._messages = messages
        self._system_prompt = system_prompt
        self._parser = response_parser

    def run(self):
        loop = asyncio.new_event_loop()
        try:
            raw_response = loop.run_until_complete(
                self._provider.generate(self._messages, self._system_prompt)
            )
            code = self._parser.extract_code(raw_response)
            self.finished.emit(code)
        except Exception as e:
            self.failed.emit(str(e))
        finally:
            loop.close()
```

### `ai_service.py` — Facade

```python
class AIService(QObject):
    """High-level facade. Coordinates prompt building, provider dispatch, response parsing."""

    def __init__(self, registry: ProviderRegistry, signal_bus: SignalBus):
        super().__init__()
        self._registry = registry
        self._bus = signal_bus
        self._prompt_builder = PromptBuilder()
        self._response_parser = ResponseParser()
        self._active_provider_name: str | None = None
        self._worker: AIWorker | None = None

    def set_active_provider(self, name: str) -> None:
        self._active_provider_name = name

    def generate_code(self, prompt: str, current_code: str | None = None) -> None:
        """Start async code generation. Results come via signal bus."""
        provider = self._registry.get_provider(self._active_provider_name)
        messages = self._prompt_builder.build(prompt, current_code)
        system_prompt = self._prompt_builder.get_system_prompt()

        self._bus.ai_generation_started.emit()
        self._worker = AIWorker(provider, messages, system_prompt, self._response_parser)
        self._worker.finished.connect(self._on_generation_finished)
        self._worker.failed.connect(self._on_generation_failed)
        self._worker.start()

    def _on_generation_finished(self, code: str):
        self._bus.ai_generation_finished.emit(code)

    def _on_generation_failed(self, error: str):
        self._bus.ai_generation_failed.emit(error)

    def get_available_providers(self) -> list[str]:
        return self._registry.list_providers()
```

---

## Tests

**`test_prompt_builder.py`**:
- Test build without current_code → single user message
- Test build with current_code → message includes code block
- Test system prompt is non-empty

**`test_response_parser.py`**:
- Test extraction from ```python blocks
- Test extraction when multiple blocks exist (takes longest)
- Test fallback to raw response
- Test syntax error raises ValueError
- Test find_scene_class_name finds Scene subclass

**`test_providers.py`**:
- Test validate_config returns False when no API key
- Test validate_config returns True when key is set
- Mock httpx calls to test generate method structure

## Verification

```bash
python -m pytest tests/test_ai/ -v
python -c "from ai.provider_registry import ProviderRegistry; print('Registry OK')"
python -c "from ai.response_parser import ResponseParser; p = ResponseParser(); print(p.extract_code('```python\nfrom manim import *\nclass S(Scene):\n    def construct(self): pass\n```'))"
```

## Dependencies on Other Agents
- Agent 1: `app.signals.get_signal_bus`, `core.models.ai_config.AIProviderConfig`

## What Other Agents Need From You
- Agent 7 (Main Window): `AIService` instance with `generate_code()`, `set_active_provider()`, `get_available_providers()`
