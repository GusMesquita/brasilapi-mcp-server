# Convenções deste repositório

Este documento é auto-contido: não depende de nenhum outro repositório.

## Ambiente

- **Python 3.13.13**, declarado em `.mise.toml`. Com [mise](https://mise.jdx.dev)
  instalado, `mise install` no diretório do projeto resolve a versão automaticamente.
- **Dependências**: `uv`, com `[dependency-groups] dev = [...]`. Não usar
  `[project.optional-dependencies]` — `uv sync --group dev` não o reconhece.
- `uv.lock` é commitado. Build sem lock não é reprodutível.

## Compatibilidade de versão

`requires-python = ">=3.11"` e `target-version = "py311"` no ruff são **intencionais** e
diferentes do 3.13 de desenvolvimento: este pacote é publicado e instalado por terceiros,
então o alvo do lint é a versão **mínima suportada**, não a da máquina de quem desenvolve.

## Lint e formatação

```
ruff check .
ruff format .
```
`select = ["E", "F", "I", "UP", "B"]`, `line-length = 100`.

## Erros de API externa

Hierarquia de exceções tipada (`BrasilAPIError` → `NotFoundError`, `RateLimitedError`)
para que quem chama use `isinstance()` em vez de comparar strings de mensagem.
404 nunca é re-tentado — não é transiente. 429 e 5xx usam backoff exponencial.

## Logging

JSON estruturado, uma linha por evento, **sempre em `stderr`**. No transporte stdio o
`stdout` é o protocolo MCP — escrever log ali corrompe o frame.

## Contrato das tools MCP

Toda tool declara `readOnlyHint`, `idempotentHint` e `openWorldHint`. Este servidor não
expõe nenhuma tool de escrita, e o contrato MCP declara isso explicitamente em vez de
deixar implícito. Detalhes em `AGENTS.md`.

## Testes

Toda lógica não trivial ganha um teste que **falha se a lógica for removida**. O critério
é verificado por mutação: altere o comportamento, rode o teste, confirme que ele quebra.
Um teste que passa com qualquer implementação não conta como cobertura.

## Docker

O uso principal deste servidor é stdio (Claude Desktop/Code), onde Docker só atrapalha —
a distribuição recomendada é via PyPI. O `Dockerfile` existe exclusivamente para o modo
`MCP_TRANSPORT=streamable-http`.
