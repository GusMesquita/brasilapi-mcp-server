"""A13 — o cache não pode crescer sem teto no modo streamable-http."""

import pytest

from brasilapi_mcp import cache


@pytest.fixture(autouse=True)
def _limpa():
    cache.clear()
    yield
    cache.clear()


def test_cache_respeita_o_teto_de_entradas(monkeypatch):
    monkeypatch.setattr(cache, "_MAX_ENTRIES", 10)

    for i in range(50):
        cache.set(f"/cnpj/v1/{i:014d}", {"i": i}, ttl_seconds=3600)

    assert len(cache._store) == 10


def test_evicao_descarta_o_menos_recentemente_usado(monkeypatch):
    monkeypatch.setattr(cache, "_MAX_ENTRIES", 3)
    for chave in ("a", "b", "c"):
        cache.set(chave, chave, ttl_seconds=3600)

    cache.get("a")  # "a" volta para o fim da fila; "b" passa a ser o mais antigo
    cache.set("d", "d", ttl_seconds=3600)

    assert cache.get("b") is None
    assert cache.get("a") == "a"


def test_entrada_expirada_sai_mesmo_sem_ser_consultada():
    # A expiração só era verificada no `get`: o que ninguém reconsulta ficava
    # retido para sempre num processo de vida longa.
    cache.set("velha", "x", ttl_seconds=-1)
    cache.set("nova", "y", ttl_seconds=3600)

    assert "velha" not in cache._store
