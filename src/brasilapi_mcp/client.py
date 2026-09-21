"""Thin async client for BrasilAPI (https://brasilapi.com.br) — no auth required."""

import asyncio
import logging

import httpx

from brasilapi_mcp import cache

BASE_URL = "https://brasilapi.com.br/api"
_CACHE_TTL_SECONDS = 3600
_MAX_RETRIES = 2

logger = logging.getLogger("brasilapi_mcp.client")


class BrasilAPIError(Exception):
    """Base error for any non-2xx response from BrasilAPI."""

    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        super().__init__(f"BrasilAPI error {status_code}: {message}")


class InvalidInputError(ValueError):
    """Entrada malformada — barrada aqui, sem gastar uma chamada na BrasilAPI."""


class NotFoundError(BrasilAPIError):
    """404 — the requested CNPJ/CEP/resource doesn't exist."""


class RateLimitedError(BrasilAPIError):
    """429 — back off before retrying."""


def _error_for(status_code: int, message: str) -> BrasilAPIError:
    if status_code == 404:
        return NotFoundError(status_code, message)
    if status_code == 429:
        return RateLimitedError(status_code, message)
    return BrasilAPIError(status_code, message)


async def _get(path: str, *, cacheable: bool = True) -> dict:
    if cacheable:
        cached = cache.get(path)
        if cached is not None:
            logger.info("cache hit path=%s", path)
            return cached

    last_error: BrasilAPIError | None = None
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=10.0) as client:
        for attempt in range(_MAX_RETRIES + 1):
            response = await client.get(path)
            if not response.is_error:
                data = response.json()
                if cacheable:
                    cache.set(path, data, _CACHE_TTL_SECONDS)
                return data

            error = _error_for(response.status_code, response.text)
            if isinstance(error, NotFoundError):
                raise error  # not transient, retrying won't help
            last_error = error
            if attempt < _MAX_RETRIES:
                backoff = 0.5 * (2**attempt)
                logger.warning(
                    "retrying path=%s attempt=%d status=%d backoff=%.1fs",
                    path,
                    attempt + 1,
                    response.status_code,
                    backoff,
                )
                await asyncio.sleep(backoff)

    assert last_error is not None
    raise last_error


def _only_digits(value: str, *, expected: int, label: str) -> str:
    """Normaliza e valida antes de montar a URL.

    Sem o check de tamanho, uma string vazia vira `/cnpj/v1/` (outro endpoint) e
    qualquer lixo vira uma chamada garantidamente perdida na BrasilAPI — com o
    404 de lá chegando ao cliente MCP como se o documento não existisse, em vez
    de como o erro de entrada que é.
    """
    digits = "".join(filter(str.isdigit, value))
    if len(digits) != expected:
        raise InvalidInputError(
            f"{label} deve ter {expected} dígitos; recebido {len(digits)} em {value!r}"
        )
    return digits


async def get_cnpj(cnpj: str) -> dict:
    return await _get(f"/cnpj/v1/{_only_digits(cnpj, expected=14, label='CNPJ')}")


async def get_cep(cep: str) -> dict:
    return await _get(f"/cep/v2/{_only_digits(cep, expected=8, label='CEP')}")


async def list_banks() -> list[dict]:
    return await _get("/banks/v1")


# Faixa suportada pela BrasilAPI: fora dela a resposta é 404, indistinguível
# de "não há feriados" para quem consome a tool.
_MIN_YEAR, _MAX_YEAR = 1900, 2199


async def get_holidays(year: int) -> list[dict]:
    if not _MIN_YEAR <= year <= _MAX_YEAR:
        raise InvalidInputError(f"ano deve estar entre {_MIN_YEAR} e {_MAX_YEAR}; recebido {year}")
    return await _get(f"/feriados/v1/{year}")
