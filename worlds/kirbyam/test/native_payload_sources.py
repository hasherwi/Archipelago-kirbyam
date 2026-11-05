"""Link shipping payload modules into mapped-memory host harnesses."""
from pathlib import Path


def link_payload_modules(source: str, payload: Path, *, native_start: str | None = None) -> str:
    # Keep native shared-save/Goal Game logic in these regressions. The harness
    # adapts only the native startup call when testing its color-order behavior.
    for name in ('shared_save.c', 'goal_game.c'):
        path = payload / name
        if path.exists():
            module = path.read_text()
            if native_start is not None:
                module = module.replace('0x080332BDu', '&' + native_start)
            source += '\n' + module
    return source
