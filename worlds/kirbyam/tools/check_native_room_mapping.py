"""Validate the complete USA room-slot inventory and render its documentation table."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import struct
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "dev-docs/native-room-wikirby-map.json"
DOC = ROOT / "dev-docs/native-room-wikirby-map.md"
BEGIN = "<!-- native-room-table:start -->"
END = "<!-- native-room-table:end -->"
SLOTS = 983
OFFSET = 0x9331AC
STRIDE = 0x28
SHA1 = "274b102b6d940f46861a92b4e65f89a51815c12c"
SENTINEL = (0xFFFF,) * 19 + (0,)


def validate_row(row: dict[str, Any], rooms: dict[str, Any], keys: set[str], rom: bytes | None) -> None:
    native, completion = row["native_id"], row["completion_index"]
    if not 0 <= native < SLOTS:
        raise ValueError("native ID out of bounds")
    for key in row["ap_keys"]:
        if key in keys or key not in rooms:
            raise ValueError("duplicate or unknown AP key")
        keys.add(key)
        room = rooms[key]
        sanity = room.get("room_sanity") or (room.get("locations") or {}).get("room_sanity") or {}
        if sanity.get("included") and sanity["bit_index"] != completion:
            raise ValueError("wrong completion-index join")
    status, url = row["verification"], row["wiki_url"]
    if status not in {"page", "category", "shared", "unverified", "unresolved"}:
        raise ValueError("unknown verification status")
    if status in {"unverified", "unresolved"}:
        if url is not None:
            raise ValueError("unverified target must not pretend to be a verified URL")
    elif url != "https://wikirby.com/wiki/" + row["wiki_title"].replace(" ", "_"):
        raise ValueError("unexpected wiki URL")
    if rom is not None:
        fields = struct.unpack_from("<20H", rom, OFFSET + native * STRIDE)
        if (fields[18], fields[16]) != (completion, row["object_list_index"]):
            raise ValueError("ROM identity mismatch")


def validate(data: dict[str, Any], rooms: dict[str, Any], rom: bytes | None = None) -> None:
    if data["slot_count"] != SLOTS or data["rom_sha1"] != SHA1:
        raise ValueError("wrong inventory revision")
    rooms = dict(rooms)
    for parent, definition in list(rooms.items()):
        for key in definition.get("logical_subregions", {}):
            rooms[f"{parent}__LOGIC__{key}"] = definition
    slots: set[int] = set()
    keys: set[str] = set()
    completions: set[int] = set()
    if rom is not None and (len(rom) != 0x1000000 or hashlib.sha1(rom).hexdigest() != SHA1):
        raise ValueError("expected unmodified USA ROM")
    for row in data["rooms"]:
        native = row["native_id"]
        completion = row["completion_index"]
        if native in slots or completion in completions or not 0 <= completion < 287:
            raise ValueError("duplicate room or invalid completion index")
        slots.add(native)
        completions.add(completion)
        validate_row(row, rooms, keys, rom)
    for start, end in data["unused_ranges"]:
        if start > end:
            raise ValueError("reversed unused range")
        for native in range(start, end + 1):
            if native in slots:
                raise ValueError("overlapping slot coverage")
            slots.add(native)
            if rom is not None and struct.unpack_from("<20H", rom, OFFSET + native * STRIDE) != SENTINEL:
                raise ValueError("unused slot is not the verified sentinel")
    if slots != set(range(SLOTS)) or keys != set(rooms):
        raise ValueError("incomplete native-slot or AP-key coverage")
    if len(data["rooms"]) != 286 or completions != set(range(287)) - {4}:
        raise ValueError("unexpected populated/completion inventory")


def render(data: dict[str, Any]) -> str:
    lines = ["| Native ID (decimal / hex) | Completion index | WiKirby target | Evidence / exceptions | AP keys |",
             "| --- | --- | --- | --- | --- |"]
    for row in data["rooms"]:
        native = row["native_id"]
        title = row["wiki_title"] or "No established wiki equivalent"
        target = f"[{title}]({row['wiki_url']})" if row["wiki_url"] else title
        keys = "<br>".join(f"`{key}`" for key in row["ap_keys"]) or "—"
        lines.append(f"| {native} / `0x{native:03X}` | {row['completion_index']} | {target} | "
                     f"**{row['verification']}**: {row['note']} | {keys} |")
    lines.extend(["", "### Unpopulated native slots", "",
                  "Every inclusive range below consists solely of the verified sentinel record. "
                  "There is no wiki room mapping; these are slots, not 697 playable rooms.", "",
                  "| Decimal range | Hex range | Count |", "| --- | --- | --- |"])
    for start, end in data["unused_ranges"]:
        lines.append(f"| {start}–{end} | `0x{start:03X}`–`0x{end:03X}` | {end - start + 1} |")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rom", type=Path, help="Optional privately held unmodified USA ROM; never emitted")
    parser.add_argument("--write", action="store_true", help="Refresh only the generated Markdown table")
    args = parser.parse_args()
    data = json.loads(DATA.read_text())
    rooms = json.loads((ROOT / "data/regions/rooms.json").read_text())
    validate(data, rooms, args.rom.read_bytes() if args.rom else None)
    text = DOC.read_text()
    pattern = re.escape(BEGIN) + r".*?" + re.escape(END)
    if len(re.findall(pattern, text, flags=re.DOTALL)) != 1:
        raise ValueError("expected exactly one generated table block")
    expected = re.sub(pattern, lambda _: BEGIN + "\n\n" + render(data) + "\n\n" + END,
                      text, flags=re.DOTALL)
    if args.write:
        DOC.write_text(expected)
    elif text != expected:
        raise ValueError("documentation table is stale; run with --write")
    print("983 slots accounted for: 286 populated, 697 sentinel; "
          "335 AP keys covered (321 top-level, 14 generated logical aliases)")


if __name__ == "__main__":
    main()
