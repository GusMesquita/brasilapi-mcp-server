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


@pytest.mark.parametrize(
    "cnpj",
    ["", "19131243", "191312430001970", "sem dígito nenhum"],
)
@pytest.mark.asyncio
async def test_get_cnpj_rejeita_tamanho_errado(cnpj, monkeypatch):
    async def nao_deve_chamar(path: str) -> dict:
        raise AssertionError(f"entrada inválida não pode virar chamada HTTP: {path}")

    monkeypatch.setattr(client, "_get", nao_deve_chamar)

    with pytest.raises(client.InvalidInputError, match="14 dígitos"):
        await client.get_cnpj(cnpj)


@pytest.mark.parametrize("cep", ["", "0131093", "013109300"])
@pytest.mark.asyncio
async def test_get_cep_rejeita_tamanho_errado(cep, monkeypatch):
    async def nao_deve_chamar(path: str) -> dict:
        raise AssertionError(f"entrada inválida não pode virar chamada HTTP: {path}")

    monkeypatch.setattr(client, "_get", nao_deve_chamar)

    with pytest.raises(client.InvalidInputError, match="8 dígitos"):
        await client.get_cep(cep)


@pytest.mark.parametrize("ano", [1899, 2200, 0, -1])
@pytest.mark.asyncio
async def test_get_holidays_rejeita_ano_fora_da_faixa(ano, monkeypatch):
    async def nao_deve_chamar(path: str) -> dict:
        raise AssertionError(f"ano inválido não pode virar chamada HTTP: {path}")

    monkeypatch.setattr(client, "_get", nao_deve_chamar)

    with pytest.raises(client.InvalidInputError, match="1900"):
        await client.get_holidays(ano)


def test_invalid_input_nao_e_confundivel_com_erro_da_api():
    # O agente distingue "corrija a entrada" de "não existe" pelo tipo.
    assert issubclass(client.InvalidInputError, ValueError)
    assert not issubclass(client.InvalidInputError, client.BrasilAPIError)
