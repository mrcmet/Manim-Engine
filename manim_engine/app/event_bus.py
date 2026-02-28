from __future__ import annotations
import threading
from typing import Callable, Type, TypeVar

T = TypeVar("T")


class EventBus:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._listeners: dict[type, list[Callable]] = {}

    def subscribe(self, event_type: Type[T], callback: Callable[[T], None]) -> None:
        with self._lock:
            self._listeners.setdefault(event_type, []).append(callback)

    def unsubscribe(self, event_type: Type[T], callback: Callable[[T], None]) -> None:
        with self._lock:
            listeners = self._listeners.get(event_type, [])
            if callback in listeners:
                listeners.remove(callback)

    def emit(self, event: object) -> None:
        with self._lock:
            listeners = list(self._listeners.get(type(event), []))
        for cb in listeners:
            cb(event)
