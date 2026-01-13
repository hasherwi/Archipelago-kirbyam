from __future__ import annotations

import logging
from typing import Any, Mapping

_LOGGER = logging.getLogger("kirbyam")


def _fmt_kv(fields: Mapping[str, Any]) -> str:
    # Simple, stable "key=value" format (safe for grep and log parsing)
    parts: list[str] = []
    for k in sorted(fields.keys()):
        v = fields[k]
        if v is None:
            parts.append(f"{k}=null")
        elif isinstance(v, bool):
            parts.append(f"{k}={'true' if v else 'false'}")
        else:
            s = str(v).replace("\n", "\\n")
            parts.append(f"{k}={s}")
    return " ".join(parts)


def log_event(event: str, **fields: Any) -> None:
    _LOGGER.info("%s %s", event, _fmt_kv(fields))


def log_debug(event: str, **fields: Any) -> None:
    _LOGGER.debug("%s %s", event, _fmt_kv(fields))


def log_warning(event: str, **fields: Any) -> None:
    _LOGGER.warning("%s %s", event, _fmt_kv(fields))
