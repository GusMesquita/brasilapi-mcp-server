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


async def get_cnpj(cnpj: str) -> dict:
    digits = "".join(filter(str.isdigit, cnpj))
    return await _get(f"/cnpj/v1/{digits}")


async def get_cep(cep: str) -> dict:
    digits = "".join(filter(str.isdigit, cep))
    return await _get(f"/cep/v2/{digits}")


async def list_banks() -> list[dict]:
    return await _get("/banks/v1")


async def get_holidays(year: int) -> list[dict]:
    return await _get(f"/feriados/v1/{year}")
