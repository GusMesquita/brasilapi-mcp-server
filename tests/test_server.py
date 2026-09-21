"""Fumaça do servidor MCP.

Nenhum teste importava `server.py`: quando `mcp[cli]>=1.2.0` resolveu para a
2.x — que renomeou `FastMCP` para `MCPServer` — o entrypoint parou de importar
e a CI continuou verde. Este arquivo existe para isso não se repetir.
"""

import pytest

from brasilapi_mcp import server


@pytest.mark.asyncio
async def test_as_quatro_tools_estao_registradas():
    nomes = sorted(tool.name for tool in await server.mcp.list_tools())

    assert nomes == ["get_holidays", "list_banks", "lookup_cep", "lookup_cnpj"]


@pytest.mark.asyncio
async def test_tools_declaram_se_read_only():
    for tool in await server.mcp.list_tools():
        assert tool.annotations is not None, tool.name
        assert tool.annotations.read_only_hint is True, tool.name
        assert tool.annotations.destructive_hint is False, tool.name
