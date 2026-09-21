import httpx
import pytest

from brasilapi_mcp import cache, client


async def _sem_espera(seconds: float) -> None:
    """Pula o backoff: o teste verifica o número de tentativas, não o relógio."""


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


@pytest.mark.asyncio
async def test_erro_de_rede_e_retentado_e_vira_erro_tipado(monkeypatch):
    """Timeout/DNS/conexão recusada não têm status code.

    Antes escapavam do laço de retry inteiro e subiam como exceção crua do
    httpx — a falha de rede mais comum era justamente a única não tratada.
    """
    chamadas = {"count": 0}

    async def sempre_falha(self, url, **kwargs):
        chamadas["count"] += 1
        raise httpx.ConnectTimeout("conexão estourou o tempo")

    monkeypatch.setattr(httpx.AsyncClient, "get", sempre_falha)
    monkeypatch.setattr(client.asyncio, "sleep", _sem_espera)

    with pytest.raises(client.UpstreamUnavailableError) as erro:
        await client.list_banks()

    assert chamadas["count"] == 3  # tentativa inicial + 2 retries
    assert erro.value.status_code == 503


@pytest.mark.asyncio
async def test_erro_de_rede_transitorio_se_recupera(monkeypatch):
    chamadas = {"count": 0}

    async def falha_uma_vez(self, url, **kwargs):
        chamadas["count"] += 1
        if chamadas["count"] == 1:
            raise httpx.ReadTimeout("primeira tentativa")
        return httpx.Response(200, json={"ok": True}, request=httpx.Request("GET", url))

    monkeypatch.setattr(httpx.AsyncClient, "get", falha_uma_vez)
    monkeypatch.setattr(client.asyncio, "sleep", _sem_espera)

    assert await client.list_banks() == {"ok": True}
    assert chamadas["count"] == 2


@pytest.mark.asyncio
async def test_indisponibilidade_nao_e_confundivel_com_inexistencia():
    # O agente precisa distinguir "não respondeu" de "respondeu que não existe".
    assert not issubclass(client.UpstreamUnavailableError, client.NotFoundError)
    assert issubclass(client.UpstreamUnavailableError, client.BrasilAPIError)


@pytest.mark.asyncio
async def test_cliente_http_e_reaproveitado_entre_chamadas(monkeypatch):
    async def ok(self, url, **kwargs):
        return httpx.Response(200, json={"ok": True}, request=httpx.Request("GET", url))

    monkeypatch.setattr(httpx.AsyncClient, "get", ok)
    await client.aclose()

    await client.list_banks()
    primeiro = client._http
    await client.get_holidays(2026)

    # Um cliente por processo: pool de conexões e handshake TLS só se pagam se
    # sobreviverem à chamada.
    assert client._http is primeiro
    await client.aclose()
    assert client._http is None
