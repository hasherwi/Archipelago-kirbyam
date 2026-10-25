"""Kirby-only artifact receipts and read-only draft upload planning."""
import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Mapping

REPOSITORY = "hasherwi/Archipelago-kirbyam"
WORKFLOW = ".github/workflows/kirbyam-apworld.yml"
ASSETS = ("kirbyam.apworld", "kirbyam.provenance.json", "kirbyam.attestation.jsonl")


def digest(path: Path) -> str:
    if path.is_symlink() or not path.is_file():
        raise ValueError("artifact must be a regular file")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def receipt(directory: Path, context: Mapping[str, str]) -> dict[str, str]:
    return {"repository": context["GITHUB_REPOSITORY"], "source": context["GITHUB_SHA"],
            "ref": context["GITHUB_REF"], "event": context["GITHUB_EVENT_NAME"], "workflow": WORKFLOW,
            "run_id": context["GITHUB_RUN_ID"], "run_attempt": context["GITHUB_RUN_ATTEMPT"],
            "subject": ASSETS[0], "sha256": digest(directory / ASSETS[0])}


def verify(directory: Path, context: Mapping[str, str]) -> None:
    actual = json.loads((directory / ASSETS[1]).read_text(encoding="utf-8"))
    expected = receipt(directory, context)
    if expected["repository"] != REPOSITORY or actual != expected:
        raise ValueError("artifact bytes or provenance identity do not match the intended build")


def plan(directory: Path, state: dict[str, Any]) -> list[str]:
    """Return missing allowlisted assets; never mutate a release or replace an asset."""
    if state.get("isDraft") is not True:
        raise ValueError("refusing to change a published release")
    if {path.name for path in directory.iterdir()} != set(ASSETS):
        raise ValueError("staging must contain exactly the APWorld, receipt and attestation bundle")
    hashes = {name: "sha256:" + digest(directory / name) for name in ASSETS}
    existing: set[str] = set()
    for asset in state["assets"]:
        name = asset["name"]
        if name not in hashes or name in existing:
            raise ValueError("unexpected or duplicate release asset; owner review required")
        if asset.get("digest") != hashes[name]:
            raise ValueError("existing asset differs or lacks digest; refusing replacement")
        existing.add(name)
    return [name for name in ASSETS if name not in existing]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("record", "verify", "plan"))
    parser.add_argument("directory", type=Path)
    parser.add_argument("--state", type=Path)
    args = parser.parse_args()
    if args.command == "record":
        (args.directory / ASSETS[1]).write_text(json.dumps(receipt(args.directory, os.environ), indent=2) + "\n")
    elif args.command == "verify":
        verify(args.directory, os.environ)
    else:
        if args.state is None:
            parser.error("plan requires --state")
        for name in plan(args.directory, json.loads(args.state.read_text())):
            print(name)


if __name__ == "__main__":
    main()
