"""Handshake recovery for the Kirby mGBA launcher, without changing shared AP."""
from worlds._bizhawk import BizHawkContext, RequestFailedError, disconnect


class KirbyMGBATransport(BizHawkContext):
    async def _send_message(self, message: str):
        if message != "VERSION":
            return await super()._send_message(message)

        # Linux can connect a socket to itself when an ephemeral source port
        # equals the absent connector's destination port. Reject it before I/O.
        if self.streams is not None:
            writer = self.streams[1]
            local = writer.get_extra_info("sockname")
            peer = writer.get_extra_info("peername")
            if local is not None and local == peer:
                disconnect(self)
                raise RequestFailedError("KirbyAM rejected a self-connected connector socket")

        try:
            response = await super()._send_message(message)
            int(response)
        except ValueError as exc:  # includes UnicodeDecodeError
            # The shared watcher already retries RequestFailedError. Closing
            # here also discards any pending bytes from the invalid handshake.
            disconnect(self)
            raise RequestFailedError("KirbyAM received an invalid connector VERSION reply") from exc
        return response
