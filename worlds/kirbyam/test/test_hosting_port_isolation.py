"""Real Kirby hosting isolation with an occupied default and concurrent listeners."""
import errno
import shutil
import socket
from pathlib import Path
from typing import Any, Callable, cast

from test.hosting.client import Client
from test.hosting.serve import LocalServeGame

from .support.integration_generation import generate_archive_from_fixture, load_multidata_from_archive
from .test_hosting_integration import FIXTURE_YAML, _read_room_info_with_retry

read_room_info = cast(Callable[[str], tuple[dict[str, Any], dict[str, Any]]], _read_room_info_with_retry)


def test_concurrent_kirby_hosts_ignore_occupied_default_port(tmp_path: Path) -> None:
    archive = generate_archive_from_fixture(FIXTURE_YAML, tmp_path / "first", seed=367)
    second_dir = tmp_path / "second"
    second_dir.mkdir()
    second_archive = second_dir / archive.name
    shutil.copy2(archive, second_archive)
    assert "KirbyAM Test" in load_multidata_from_archive(second_archive)["connect_names"]

    # An already occupied default is also a valid setup; never close another test's listener.
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as occupied:
        try:
            occupied.bind(("127.0.0.1", 38281))
            occupied.listen()
        except OSError as error:
            if error.errno not in (errno.EADDRINUSE, 10048):
                raise
        with LocalServeGame(archive) as first, LocalServeGame(second_archive) as second:
            assert first.address != second.address
            assert not first.address.endswith(":38281") and not second.address.endswith(":38281")
            for host in (first, second):
                room_info, packages = read_room_info(host.address)
                assert {"Kirby & The Amazing Mirror", "Archipelago"} <= set(room_info["games"])
                assert {"Kirby & The Amazing Mirror", "Archipelago"} <= set(packages)
            with Client(first.address, "Kirby & The Amazing Mirror", "KirbyAM Test") as client:
                collected_location = next(iter(client.missing_locations))
                client.collect([collected_location])
        assert first._exitcode == second._exitcode == 0
        assert first._proc is None and second._proc is None
        assert archive.with_suffix(".apsave").is_file()
        assert second_archive.with_suffix(".apsave").is_file()

    # The other shared-helper caller relies on persisted checks after a normal stop/restart.
    with LocalServeGame(archive) as restarted:
        with Client(restarted.address, "Kirby & The Amazing Mirror", "KirbyAM Test") as client:
            assert collected_location in client.checked_locations
    assert restarted._exitcode == 0 and restarted._proc is None
