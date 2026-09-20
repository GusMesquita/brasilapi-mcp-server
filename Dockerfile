FROM python:3.13-slim

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY pyproject.toml ./
COPY src ./src
RUN uv pip install --system .

ENV MCP_TRANSPORT=streamable-http
ENV MCP_HTTP_PORT=8001
EXPOSE 8001

CMD ["brasilapi-mcp-server"]
