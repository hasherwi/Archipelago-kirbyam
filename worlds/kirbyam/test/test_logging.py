"""Tests for KirbyAM test logging support."""

import logging

import pytest


@pytest.mark.asyncio
async def test_kirbyam_test_logging_records_protocol_traffic(
    kirbyam_test_log_file,
    mock_bizhawk_context,
    mock_bizhawk_read,
    mock_bizhawk_write,
    caplog,
) -> None:
    test_logger = logging.getLogger("worlds.kirbyam.test")
    previous_level = test_logger.level
    test_logger.setLevel(logging.DEBUG)
    caplog.set_level(logging.DEBUG, logger="worlds.kirbyam.test")
    try:
        await mock_bizhawk_read(mock_bizhawk_context.bizhawk_ctx, [(0x0202C000, 4, "System Bus")])
        await mock_bizhawk_write(mock_bizhawk_context.bizhawk_ctx, [(0x0202C004, (1).to_bytes(4, "little"), "System Bus")])
        await mock_bizhawk_context.send_msgs([{"cmd": "LocationChecks", "locations": [3860101]}])

        for handler in logging.getLogger().handlers:
            flush = getattr(handler, "flush", None)
            if callable(flush):
                flush()

        assert kirbyam_test_log_file.exists()
        assert "bizhawk.read" in caplog.text
        assert "bizhawk.write" in caplog.text
        assert "ap.send_msgs" in caplog.text
    finally:
        test_logger.setLevel(previous_level)
