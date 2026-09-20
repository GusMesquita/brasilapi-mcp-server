import httpx
import pytest

from brasilapi_mcp import cache, client


@pytest.fixture(autouse=True)
def _clear_cache():
    cache.clear()
    yield
    cache.clear()


@pytest.mark.asyncio
async def test_404_raises_not_found_without_retry(monkeypatch):
    calls = {"count": 0}

    async def fake_request(self, url, **kwargs):
        calls["count"] += 1
        return httpx.Response(404, text="not found", request=httpx.Request("GET", url))

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_request)

    with pytest.raises(client.NotFoundError):
        await client.get_cnpj("00000000000000")

    assert calls["count"] == 1  # 404 must not be retried


@pytest.mark.asyncio
async def test_second_call_hits_cache_not_network(monkeypatch):
    calls = {"count": 0}

    async def fake_request(self, url, **kwargs):
        calls["count"] += 1
        return httpx.Response(200, json={"code": 1}, request=httpx.Request("GET", url))

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_request)

    await client.list_banks()
    await client.list_banks()

    assert calls["count"] == 1
