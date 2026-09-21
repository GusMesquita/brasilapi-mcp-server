"""In-memory TTL cache for BrasilAPI responses.

BrasilAPI data (banks, holidays, CNPJ registration data) changes rarely, so a
short-lived cache avoids hammering a public, rate-limited API. This is a
single-process dict — not shared across replicas.

ponytail: global dict + lock, not Redis. Swap for a shared cache (Redis) only
if you run this behind more than one replica and need cache coherence.
ponytail: eviction é LRU varrendo o dicionário inteiro — O(n) por inserção
quando lota. Com 5.000 entradas é irrelevante; se o teto subir muito, troque
por uma estrutura com expiração indexada.
"""

import time
from collections import OrderedDict
from threading import Lock
from typing import Any

# Sem teto, o dicionário só cresce: no modo stdio o processo é curto e ninguém
# nota, mas em `streamable-http` ele vive por dias e cada CNPJ consultado fica
# retido até o TTL. Entrada só sai por expiração — e quem nunca é reconsultado
# nunca expira, porque a expiração é verificada no `get`.
_MAX_ENTRIES = 5_000

_store: OrderedDict[str, tuple[float, Any]] = OrderedDict()
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
        _store.move_to_end(key)  # LRU: o que é usado vai para o fim da fila
        return value


def set(key: str, value: Any, ttl_seconds: float) -> None:
    with _lock:
        _store[key] = (time.monotonic() + ttl_seconds, value)
        _store.move_to_end(key)
        _evict(time.monotonic())


def _evict(now: float) -> None:
    """Expirados primeiro; só então o mais antigo em uso. Chamar com o lock."""
    for key in [k for k, (expires_at, _) in _store.items() if now >= expires_at]:
        del _store[key]
    while len(_store) > _MAX_ENTRIES:
        _store.popitem(last=False)


def clear() -> None:
    with _lock:
        _store.clear()
