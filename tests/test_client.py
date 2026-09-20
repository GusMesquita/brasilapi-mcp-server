import pytest

from brasilapi_mcp import client


@pytest.mark.asyncio
async def test_get_cnpj_strips_formatting(monkeypatch):
    captured_path = {}

    async def fake_get(path: str) -> dict:
        captured_path["value"] = path
        return {"razao_social": "EXEMPLO LTDA"}

    monkeypatch.setattr(client, "_get", fake_get)

    result = await client.get_cnpj("19.131.243/0001-97")

    assert captured_path["value"] == "/cnpj/v1/19131243000197"
    assert result["razao_social"] == "EXEMPLO LTDA"


@pytest.mark.asyncio
async def test_get_cep_strips_formatting(monkeypatch):
    captured_path = {}

    async def fake_get(path: str) -> dict:
        captured_path["value"] = path
        return {"city": "Sao Paulo"}

    monkeypatch.setattr(client, "_get", fake_get)

    await client.get_cep("01310-930")

    assert captured_path["value"] == "/cep/v2/01310930"
