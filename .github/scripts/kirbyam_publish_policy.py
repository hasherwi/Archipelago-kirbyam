"""Trusted-main publisher policy. Never import or execute tagged project code."""
import importlib
import json
import os
from pathlib import Path
import re
import subprocess
from typing import Mapping

metadata = importlib.import_module("kirbyam_release_metadata")


def authorize(context: Mapping[str, str], approved_source: bool) -> None:
    if context.get("GITHUB_REPOSITORY") != "hasherwi/Archipelago-kirbyam":
        raise ValueError("wrong repository")
    if context.get("GITHUB_EVENT_NAME") != "push" or context.get("GITHUB_REF_PROTECTED") != "true":
        raise ValueError("publication requires a protected tag push")
    ref = context.get("GITHUB_REF", "")
    if not ref.startswith("refs/tags/kirbyam-v") or not metadata.build_release_metadata(ref).release_enabled:
        raise ValueError("invalid release ref")
    if not re.fullmatch(r"[0-9a-f]{40}", context.get("GITHUB_SHA", "")) or not approved_source:
        raise ValueError("release source is not approved main history")


def main() -> None:
    sha = os.environ.get("GITHUB_SHA", "")
    # Validate untrusted context before passing the SHA as a git argument.
    authorize(os.environ, approved_source=True)
    subprocess.run(["git", "merge-base", "--is-ancestor", sha, "HEAD"], check=True)
    release = metadata.build_release_metadata(os.environ["GITHUB_REF"])
    manifest = json.loads(subprocess.check_output(
        ["git", "show", f"{sha}:worlds/kirbyam/archipelago.json"], text=True))
    if manifest.get("world_version") != release.manifest_version:
        raise ValueError("tagged manifest version must already match release")
    changelog = subprocess.check_output(["git", "show", f"{sha}:worlds/kirbyam/CHANGELOG.md"], text=True)
    notes = Path("release-source-changelog.md")
    notes.write_text(changelog, encoding="utf-8")
    metadata.check_changelog_has_version(notes, release.version)
    Path("release_notes.md").write_text(metadata.extract_changelog_section(notes, release.version), encoding="utf-8")
    metadata.write_github_output(release, Path(os.environ["GITHUB_OUTPUT"]))


if __name__ == "__main__":
    main()
