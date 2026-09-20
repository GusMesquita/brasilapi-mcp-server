"""In-memory TTL cache for BrasilAPI responses.

BrasilAPI data (banks, holidays, CNPJ registration data) changes rarely, so a
short-lived cache avoids hammering a public, rate-limited API. This is a
single-process dict — not shared across replicas.

ponytail: global dict + lock, not Redis. Swap for a shared cache (Redis) only
if you run this behind more than one replica and need cache coherence.
"""

import time
from threading import Lock
from typing import Any

_store: dict[str, tuple[float, Any]] = {}
_lock = Lock()


def get(key: str) -> Any | None:
    with _lock:
        entry = _store.get(key)
        if entry is None:
            return None
        expires_at, value = entry
        if time.monotonic() >= expires_at:
            del _store[key]
            return None
        return value


def set(key: str, value: Any, ttl_seconds: float) -> None:
    with _lock:
        _store[key] = (time.monotonic() + ttl_seconds, value)


def clear() -> None:
    with _lock:
        _store.clear()
