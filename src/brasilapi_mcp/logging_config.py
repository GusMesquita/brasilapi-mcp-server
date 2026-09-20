"""Structured (JSON-lines) logging setup — stdlib only.

One line per event, machine-parseable, safe for stdio transport: everything
goes to stderr so it never collides with MCP's stdout protocol framing.
"""

import json
import logging
import sys
from datetime import UTC, datetime


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload)


def configure_logging(level: int = logging.INFO) -> None:
    handler = logging.StreamHandler(stream=sys.stderr)
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger("brasilapi_mcp")
    root.setLevel(level)
    root.handlers = [handler]
    root.propagate = False
