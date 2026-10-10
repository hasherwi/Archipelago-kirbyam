"""Local receipt evidence, never a substitute for native-save ownership.

A write-ahead pending receipt is deliberately ambiguous after process loss.
Only an observed ACK or an explicit user resolution can complete it.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path

# Delivery semantics must not follow AP progression/filler classification.
TRANSIENT_ITEM_IDS = frozenset({
    3860001,  # 1 Up
    3860026, 3860027, 3860028, 3860029, 3860030, 3860031,  # Consumables
    3860032, 3860033, 3860034, 3860035, 3860036,  # All five transient traps
})


def receipt_key(items, index: int) -> str:
    def identity(item):
        try:
            return (int(item.item), int(item.location), int(item.player))
        except (TypeError, ValueError, AttributeError):
            return None

    try:
        current = identity(items[index])
    except IndexError:
        current = None
    if current is None:
        raise ValueError("Receipt lacks an item/location/player identity")
    occurrence = sum(identity(old) == current for old in items[:index])
    return json.dumps((*current, occurrence), separators=(",", ":"))


def scope_key(seed: str, rom_auth: bytes, team: int, slot: int) -> str:
    # Store only a digest, never ROM authentication material.
    return hashlib.sha256(json.dumps(
        [seed, rom_auth.hex(), team, slot], separators=(",", ":")
    ).encode()).hexdigest()


class ReceiptJournal:
    def __init__(self, path: str, scope: str):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.scope = scope
        self.db = sqlite3.connect(path, timeout=1)
        self.db.execute("PRAGMA synchronous=FULL")
        self.db.execute("CREATE TABLE IF NOT EXISTS receipts "
                        "(scope TEXT, receipt TEXT, state TEXT NOT NULL, notified INTEGER NOT NULL, "
                        "PRIMARY KEY(scope, receipt), CHECK(state IN ('pending', 'acked')))")
        self.db.commit()

    def close(self):
        self.db.close()

    def pending(self) -> list[str]:
        return [row[0] for row in self.db.execute(
            "SELECT receipt FROM receipts WHERE scope=? AND state='pending' ORDER BY receipt", (self.scope,))]

    def acknowledged(self, receipt: str) -> bool:
        row = self.db.execute("SELECT state FROM receipts WHERE scope=? AND receipt=?",
                              (self.scope, receipt)).fetchone()
        return row is not None and row[0] == 'acked'

    def reserve(self, receipt: str) -> bool:
        with self.db:
            result = self.db.execute("INSERT OR IGNORE INTO receipts VALUES (?, ?, 'pending', 0)",
                                     (self.scope, receipt))
        return result.rowcount == 1

    def acknowledge(self, receipt: str):
        with self.db:
            self.db.execute("INSERT INTO receipts VALUES (?, ?, 'acked', 0) "
                            "ON CONFLICT(scope, receipt) DO UPDATE SET state='acked'", (self.scope, receipt))

    def claim_notice(self, receipt: str) -> bool:
        with self.db:
            result = self.db.execute("UPDATE receipts SET notified=1 "
                                     "WHERE scope=? AND receipt=? AND state='acked' AND notified=0",
                                     (self.scope, receipt))
        return result.rowcount == 1

    def resolve(self, receipt: str, decision: str):
        with self.db:
            if decision == 'received':
                self.db.execute("UPDATE receipts SET state='acked', notified=1 "
                                "WHERE scope=? AND receipt=? AND state='pending'", (self.scope, receipt))
            elif decision == 'retry':
                self.db.execute("DELETE FROM receipts WHERE scope=? AND receipt=? AND state='pending'",
                                (self.scope, receipt))
            else:
                raise ValueError('Unknown receipt resolution')
