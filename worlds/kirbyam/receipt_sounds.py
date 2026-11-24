"""Non-blocking, ACK-gated transport for native receipt cues."""
from collections import deque
from struct import pack, unpack

import worlds._bizhawk as bizhawk

CUE_ROM_OFFSET = 0x1000020
CUE_ROM_MARKER = b"APCUE01\0"
CUE_MAILBOX = 0x0203B1B0  # request, result, current ready bitmask
CUE_FRAME_MASK = (1 << 29) - 1
CUE_REJECTED = 1 << 31
BUS = "System Bus"


def cue_for_receipt(item: object) -> int:
    # A real found check has a nonnegative location. Archipelago sends
    # precollected inventory at location -2, with no finder.
    location = getattr(item, "location", None)
    flags = getattr(item, "flags", 0)
    if not isinstance(location, int) or location < 0 or not isinstance(flags, int):
        return 0
    # NetworkItem flags: progression 1, useful 2, trap 4.
    return 3 if flags & 4 else 1 if flags & 1 else 2


class ReceiptSounds:
    def __init__(self) -> None:
        self.pending: deque[int] = deque()
        self.in_flight = 0
        self.supported: bool | None = None

    def enqueue(self, item: object) -> None:
        cue = cue_for_receipt(item)
        if cue and self.supported is not False:
            self.pending.append(cue)

    async def pump(self, transport, *, auth_offset: int, auth: bytes, frame_addr: int) -> None:
        if not self.pending or self.supported is False:
            return
        if self.supported is None:
            marker, = await bizhawk.read(transport, [(CUE_ROM_OFFSET, len(CUE_ROM_MARKER), "ROM")])
            self.supported = marker == CUE_ROM_MARKER
            if not self.supported:
                self.pending.clear()
                return

        mailbox, native_frame = await bizhawk.read(transport, [
            (CUE_MAILBOX, 12, BUS), (frame_addr, 4, BUS),
        ])
        if len(mailbox) != 12 or len(native_frame) != 4:
            return
        request, result, ready = unpack("<III", mailbox)
        if self.in_flight:
            if request == self.in_flight:
                return
            if result != (self.in_flight | CUE_REJECTED):
                # Only an explicit native rejection is retryable. If a reset or
                # load removed the result, replay could duplicate a played cue.
                self.pending.popleft()
            self.in_flight = 0

        if request or not self.pending or not ready & (1 << self.pending[0]):
            return
        frame, = unpack("<I", native_frame)
        token = ((frame & CUE_FRAME_MASK) << 2) | self.pending[0]
        # Publish request last. Guard the ROM and idle state atomically; a
        # connector exception after write is ambiguous, not a safe retry.
        self.in_flight = token
        if not await bizhawk.guarded_write(transport, [
            (CUE_MAILBOX + 4, bytes(4), BUS),
            (CUE_MAILBOX, pack("<I", token), BUS),
        ], [
            (auth_offset, auth, "ROM"),
            (CUE_MAILBOX, bytes(4), BUS),
        ]):
            self.in_flight = 0
