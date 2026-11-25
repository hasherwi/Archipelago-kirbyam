"""Best-effort item art for first ACKs of live remote deliveries."""
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass
from struct import pack, unpack
from time import monotonic

import worlds._bizhawk as bizhawk

from .reward_art_types import KIRBY_NATIVE_ART_BY_ITEM_CODE, RewardArt

VISUAL_ROM_OFFSET = 0x1000028
VISUAL_ROM_MARKER = b"APVIS05\0"
VISUAL_MAILBOX = 0x0203B1E0
VISUAL_GEM = RewardArt.GEM + 1
VISUAL_TRAP = RewardArt.TRAP + 1
VISUAL_ART_BITS = 7
VISUAL_MAX_OPCODE = max(RewardArt) + 1
VISUAL_REJECTED = 1 << 31
VISUAL_FRAME_MASK = (1 << 24) - 1
VISUAL_LIMIT = 8
VISUAL_MAX_ATTEMPTS = 3
VISUAL_MAX_AGE_SECONDS = 5.0
BUS = "System Bus"


def visual_for_remote_receipt(item: object, local_slot: int) -> int:
    location = getattr(item, "location", None)
    finder = getattr(item, "player", None)
    flags = getattr(item, "flags", None)
    if (type(location) is not int or location < 0 or type(finder) is not int
            or finder <= 0 or finder == local_slot or type(flags) is not int):
        return 0
    if flags & 4:
        return VISUAL_TRAP
    code = getattr(item, "item", None)
    if type(code) is not int:
        return 0
    return KIRBY_NATIVE_ART_BY_ITEM_CODE.get(code, RewardArt.GEM) + 1


@dataclass
class _PendingVisual:
    opcode: int
    expires_at: float
    native_rejections: int = 0


class ReceiptVisuals:
    """Track append provenance separately from durable delivery and audio."""

    def __init__(self, *, clock: Callable[[], float] = monotonic) -> None:
        self._clock = clock
        self.revision = 0
        self.socket = None
        self.session = None
        self.history = None
        self.history_end: int | None = None
        self.live: dict[int, tuple[object, int]] = {}
        self.pending: deque[_PendingVisual] = deque()
        self.in_flight = 0
        self._in_flight_item: _PendingVisual | None = None
        self._last_token = 0
        self.supported: bool | None = None

    def matches(self, socket: object, session: tuple) -> bool:
        return (socket is not None and self.socket is socket and self.session == session
                and not getattr(socket, "closed", True))

    def baseline(self, socket: object, session: tuple, history: list) -> None:
        revision = self.revision + 1
        self.__init__(clock=self._clock)
        self.revision = revision
        self.socket, self.session, self.history = socket, session, history
        self.history_end = len(history)

    def packet(self, socket: object, session: tuple, history: list, start: int,
               packet_length: int, cursor: int | None, local_slot: int) -> None:
        # Ignore initial history and index-zero rewrites from Sync. The first
        # append to an already established *empty* list may legitimately be zero.
        ends_at_history_end = start >= 0 and start + packet_length == len(history)
        exact_append = (self.matches(socket, session) and self.history_end == start
                        and ends_at_history_end and (self.history is history or start == 0))
        if not exact_append:
            self.baseline(socket, session, history)
            if start != 0 or not ends_at_history_end:
                # CommonClient sends Sync for any gap. Its eventual index-zero
                # replay is catch-up even if the old native history was empty.
                self.history_end = None
            return
        self.history, self.history_end = history, len(history)
        if cursor is None or cursor < start:
            return  # A native/connection backlog is catch-up, not a live cue.
        for index in range(start, len(history)):
            if len(self.live) >= VISUAL_LIMIT:
                break
            item = history[index]
            art = visual_for_remote_receipt(item, local_slot)
            if art:
                self.live[index] = item, art

    def acknowledge(self, index: int, item: object, *, first: bool) -> None:
        for older in tuple(self.live):
            if older < index:
                self.live.pop(older)
        witnessed = self.live.pop(index, None)
        if first and witnessed is not None and witnessed[0] is item:
            self._enqueue(witnessed[1])

    def _expire(self, now: float) -> None:
        while self.pending and self.pending[0].expires_at <= now:
            expired = self.pending.popleft()
            if expired is self._in_flight_item:
                # Keep its wire token as a drain fence, but detach the local
                # entry. Late acceptance/rejection belongs to no queued item.
                self._in_flight_item = None

    def _enqueue(self, opcode: int) -> None:
        now = self._clock()
        self._expire(now)
        if len(self.pending) < VISUAL_LIMIT and self.supported is not False:
            self.pending.append(_PendingVisual(opcode, now + VISUAL_MAX_AGE_SECONDS))

    async def pump(self, transport, *, auth_offset: int, auth: bytes, frame_addr: int,
                   session_current) -> None:
        revision = self.revision

        def current():
            return self.revision == revision and session_current()

        if self.supported is False or not current():
            return
        self._expire(self._clock())
        if not self.pending and not self.in_flight:
            return
        if self.supported is None:
            marker, = await bizhawk.read(transport, [(VISUAL_ROM_OFFSET, len(VISUAL_ROM_MARKER), "ROM")])
            if not current():
                return
            self.supported = marker == VISUAL_ROM_MARKER
            if not self.supported:
                self.pending.clear()
                return
            self._expire(self._clock())
            if not self.pending and not self.in_flight:
                return

        mailbox, native_frame = await bizhawk.read(transport, [
            (VISUAL_MAILBOX, 16, BUS), (frame_addr, 4, BUS),
        ])
        if len(mailbox) != 16 or len(native_frame) != 4 or not current():
            return
        self._expire(self._clock())
        request, result, ready, active = unpack("<IIII", mailbox)
        if self.in_flight:
            if request == self.in_flight:
                if self._in_flight_item is None:
                    # Expiry can race native consumption. Retract only the
                    # exact unconsumed request in this ROM; never clear its
                    # result or associated active/ready state. If native already
                    # consumed it, this guard fails and the next poll drains it.
                    await bizhawk.guarded_write(transport, [
                        (VISUAL_MAILBOX, bytes(4), BUS),
                    ], [
                        (auth_offset, auth, "ROM"),
                        (VISUAL_ROM_OFFSET, VISUAL_ROM_MARKER, "ROM"),
                        (VISUAL_MAILBOX, pack("<I", self.in_flight), BUS),
                    ])
                return
            item = self._in_flight_item
            if item is not None:
                rejected = result == (self.in_flight | VISUAL_REJECTED)
                if rejected:
                    item.native_rejections += 1
                if not rejected or item.native_rejections >= VISUAL_MAX_ATTEMPTS:
                    # Missing result after reset is ambiguous; don't replay.
                    self.pending.popleft()
            self.in_flight = 0
            self._in_flight_item = None

        if request or active or not self.pending or ready != 1:
            return
        item = self.pending[0]
        opcode = item.opcode
        if not 1 <= opcode <= VISUAL_MAX_OPCODE:
            self.pending.popleft()
            return
        frame, = unpack("<I", native_frame)
        token = ((frame & VISUAL_FRAME_MASK) << VISUAL_ART_BITS) | opcode
        if token == self._last_token or token == (result & ~VISUAL_REJECTED):
            # A paused or rewound frame can repeat the exact token. Wait for a
            # distinguishable request rather than misread a prior result.
            return
        self.in_flight = token
        self._in_flight_item = item
        old_token, self._last_token = self._last_token, token
        written = await bizhawk.guarded_write(transport, [
            (VISUAL_MAILBOX + 4, bytes(4), BUS),
            (VISUAL_MAILBOX, pack("<I", token), BUS),
        ], [
            (auth_offset, auth, "ROM"),
            (VISUAL_MAILBOX, bytes(4), BUS),
        ])
        if not written and current():
            # A false guard is known not to have published anything. Errors,
            # on the other hand, leave the token for ambiguous-result handling.
            self._last_token = old_token
            self.in_flight = 0
            self._in_flight_item = None
