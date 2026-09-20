# brasilapi-mcp-server

Servidor [MCP](https://modelcontextprotocol.io) que expõe a [BrasilAPI](https://brasilapi.com.br) (pública, sem autenticação) como ferramentas para LLMs: consulta de CNPJ, CEP, bancos e feriados nacionais.

Serve dois papéis:
1. **Standalone**: conectado ao Claude Desktop/Claude Code via stdio, permite que o modelo consulte dados públicos brasileiros durante uma conversa.
2. **Serviço de enriquecimento**: usado por outros projetos deste portfólio ([lead-router](../lead-router)) para enriquecer leads com dados de CNPJ/CEP.

## Ferramentas expostas

| Tool | Descrição |
|---|---|
| `lookup_cnpj(cnpj)` | Razão social, endereço, situação cadastral e CNAE de uma empresa |
| `lookup_cep(cep)` | Endereço e coordenadas de um CEP |
| `list_banks()` | Lista de bancos registrados no Banco Central (códigos COMPE/ISPB) |
| `get_holidays(year)` | Feriados nacionais de um ano |

## Rodando localmente

```bash
uv sync
uv run brasilapi-mcp-server
```

## Conectando no Claude Desktop

Adicione em `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "brasilapi": {
      "command": "uv",
      "args": ["--directory", "/caminho/para/brasilapi-mcp-server", "run", "brasilapi-mcp-server"]
    }
  }
}
```

## Rodando como serviço HTTP (streamable-http)

Para ser chamado por outros serviços deste portfólio (`lead-router`) sem um
processo MCP dedicado por cliente:

```bash
MCP_TRANSPORT=streamable-http MCP_HTTP_PORT=8001 uv run brasilapi-mcp-server
```

Ou via Docker:

```bash
docker build -t brasilapi-mcp-server .
docker run -p 8001:8001 brasilapi-mcp-server
```

## Resiliência

- **Cache em memória** (1h de TTL) para respostas de sucesso — ver `cache.py`.
- **Retry com backoff exponencial** (2 tentativas) em 429/5xx; um 404 nunca é
  re-tentado — ver `client.py`.
- **Erros tipados**: `NotFoundError`, `RateLimitedError`, `BrasilAPIError` —
  ver [AGENTS.md](./AGENTS.md) para o contrato completo de comportamento.
- **Logs estruturados** (JSON-lines em stderr) — `logging_config.py`.

## Testes

```bash
uv sync --group dev
uv run pytest
uv run ruff check .
```

## Roadmap

- [ ] Cobertura de mais endpoints da BrasilAPI (DDD, tabela FIPE, câmbio)
- [ ] Cache compartilhado (Redis) se rodar com mais de uma réplica
