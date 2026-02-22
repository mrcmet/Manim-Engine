import asyncio
from PySide6.QtCore import QThread, Signal
from ai.provider_base import AIProvider, AIProviderError
from ai.response_parser import ResponseParser


class AIWorker(QThread):
    finished = Signal(str)  # generated code
    failed = Signal(str)    # error message

    def __init__(
        self,
        provider: AIProvider,
        messages: list[dict],
        system_prompt: str | None = None,
        response_parser: ResponseParser | None = None,
    ):
        super().__init__()
        self._provider = provider
        self._messages = messages
        self._system_prompt = system_prompt
        self._parser = response_parser or ResponseParser()
        self._is_cancelled = False

    def run(self):
        loop = asyncio.new_event_loop()
        try:
            raw_response = loop.run_until_complete(
                self._provider.generate(self._messages, self._system_prompt)
            )
            if self._is_cancelled:
                return
            code = self._parser.extract_code(raw_response)
            self.finished.emit(code)
        except Exception as e:
            if not self._is_cancelled:
                self.failed.emit(str(e))
        finally:
            loop.close()

    def cancel(self):
        self._is_cancelled = True
        self.requestInterruption()
