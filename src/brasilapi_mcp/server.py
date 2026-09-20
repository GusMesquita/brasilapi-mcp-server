"""MCP server exposing BrasilAPI as tools for LLM clients (Claude Desktop, Claude Code, etc.).

Transport is stdio by default (local clients). Set MCP_TRANSPORT=streamable-http
to run it as an HTTP service instead — this is how other services in this
portfolio (lead-router) reach it over the network. See AGENTS.md for the
behavioral contract each tool follows.
"""

import os

from mcp.server.fastmcp import FastMCP

from brasilapi_mcp import client
from brasilapi_mcp.logging_config import configure_logging

configure_logging()

mcp = FastMCP("brasilapi", stateless_http=True)

_READ_ONLY = {
    "readOnlyHint": True,
    "destructiveHint": False,
    "idempotentHint": True,
    "openWorldHint": True,
}


@mcp.tool(annotations=_READ_ONLY)
async def lookup_cnpj(cnpj: str) -> dict:
    """Look up a Brazilian company (CNPJ) — legal name, address, status, and business activity.

    Args:
        cnpj: CNPJ number, with or without formatting
            (e.g. "19131243000197" or "19.131.243/0001-97").
    """
    return await client.get_cnpj(cnpj)


@mcp.tool(annotations=_READ_ONLY)
async def lookup_cep(cep: str) -> dict:
    """Look up a Brazilian postal code (CEP) — street, neighborhood, city, state, and coordinates.

    Args:
        cep: CEP number, with or without formatting (e.g. "01310930" or "01310-930").
    """
    return await client.get_cep(cep)


@mcp.tool(annotations=_READ_ONLY)
async def list_banks() -> list[dict]:
    """List all Brazilian banks registered with the Central Bank, with their codes (COMPE/ISPB)."""
    return await client.list_banks()


@mcp.tool(annotations=_READ_ONLY)
async def get_holidays(year: int) -> list[dict]:
    """List Brazilian national holidays for a given year.

    Args:
        year: Four-digit year (e.g. 2026).
    """
    return await client.get_holidays(year)


def main() -> None:
    transport = os.environ.get("MCP_TRANSPORT", "stdio")
    if transport == "streamable-http":
        mcp.settings.host = os.environ.get("MCP_HTTP_HOST", "0.0.0.0")
        mcp.settings.port = int(os.environ.get("MCP_HTTP_PORT", "8001"))
    mcp.run(transport=transport)


if __name__ == "__main__":
    main()
