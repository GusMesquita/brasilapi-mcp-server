# Agent behavior contract

This server has no LLM calls of its own — it's a pure data-access layer. The
"agent behavior" that matters here is what an LLM client is entitled to
assume when it calls these tools.

## Guarantees

- **All four tools are read-only.** `readOnlyHint=true`, `destructiveHint=false`,
  `idempotentHint=true` on every tool — an agent may retry any call safely,
  and never needs to ask for destructive-action confirmation before calling one.
- **Errors are typed, not swallowed.** `NotFoundError` (bad CNPJ/CEP) vs.
  `RateLimitedError` (back off) vs. generic `BrasilAPIError` are distinct
  exceptions — a calling agent (or the FastAPI wrapper in `lead-router`) can
  branch on `isinstance()` instead of parsing message strings.
- **A 404 is not retried; a 429 or 5xx is, twice, with exponential backoff**
  (`client.py::_get`). An agent never sees a transient blip as a hard failure.
- **Successful lookups are cached for 1 hour** (`cache.py`). Calling
  `lookup_cnpj` twice for the same CNPJ in a session costs one real HTTP call.

## What an agent should NOT assume

- No write/mutation tools exist or will be added silently — this server's
  scope is deliberately limited to lookups.
- Dígito verificador de CNPJ e existência do CEP **não** são checados
  localmente: isso continua vindo da BrasilAPI como `NotFoundError`. O que é
  validado antes da chamada é só a forma — 14 dígitos para CNPJ, 8 para CEP,
  ano entre 1900 e 2199 — e a falha vem como `InvalidInputError`, que é um
  `ValueError`, não um `BrasilAPIError`. A distinção importa para o agente:
  `InvalidInputError` significa "corrija a entrada", `NotFoundError` significa
  "a entrada está bem formada, o registro é que não existe".
