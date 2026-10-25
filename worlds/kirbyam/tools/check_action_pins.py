"""Fail closed on unreviewed executable action references in Kirby workflows."""
import json
from pathlib import Path
import re

import yaml


def check(text: str, pins: dict[str, str]) -> None:
    def visit(value: object) -> None:
        if isinstance(value, dict):
            for key, item in value.items():
                if key == "uses":
                    if not isinstance(item, str):
                        raise ValueError("Action reference must be a string")
                    action, separator, revision = item.partition("@")
                    if not separator or not re.fullmatch(r"[0-9a-f]{40}", revision) or pins.get(action) != revision:
                        raise ValueError(f"Unreviewed action reference: {item}")
                visit(item)
        elif isinstance(value, list):
            for item in value:
                visit(item)

    visit(yaml.safe_load(text))


def main() -> None:
    root = Path(__file__).resolve().parents[3]
    pins = json.loads(Path(__file__).with_name("action-pins.json").read_text())
    for workflow in (root / ".github/workflows").glob("kirby*.yml"):
        check(workflow.read_text(), pins)


if __name__ == "__main__":
    main()
