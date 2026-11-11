"""Check that platform normalization does not hide source changes."""

import hashlib
from pathlib import Path

import pytest

from .evidence_helpers import canonical_text_bytes


def test_checkout_line_endings_have_same_git_blob(tmp_path: Path) -> None:
    source = b"first = 1\nsecond = 2\n"
    path = tmp_path / "source.py"
    hashes = []
    for data in (source, source.replace(b"\n", b"\r\n")):
        path.write_bytes(data)
        normalized = canonical_text_bytes(path)
        assert normalized == source
        hashes.append(hashlib.sha1(
            b"blob " + str(len(normalized)).encode() + b"\0" + normalized).hexdigest())
    assert hashes[0] == hashes[1]


@pytest.mark.parametrize("changed", [
    b"value = 2\n", b"value = 1 \n", b"value = 1\r",
    b"\xef\xbb\xbfvalue = 1\n", b"value = 1",
])
def test_other_changes_remain_visible(tmp_path: Path, changed: bytes) -> None:
    path = tmp_path / "source.py"
    path.write_bytes(changed)
    assert canonical_text_bytes(path) != b"value = 1\n"


def test_evidence_decoding_ignores_platform_default(monkeypatch: pytest.MonkeyPatch) -> None:
    from .test_native_metal205_evidence import (
        test_actual_bonkers_identity_is_separate_from_post_defeat_fixture,
    )

    original = Path.read_text

    def windows_read_text(path: Path, encoding: str | None = None,
                          errors: str | None = None) -> str:
        return original(path, encoding=encoding or "cp1252", errors=errors)

    monkeypatch.setattr(Path, "read_text", windows_read_text)
    test_actual_bonkers_identity_is_separate_from_post_defeat_fixture()
