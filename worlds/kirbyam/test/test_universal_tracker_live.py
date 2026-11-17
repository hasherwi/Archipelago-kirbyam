"""Opt-in real loopback server/UT acceptance; no emulator, GUI or socket mocks.

AP_TEST_WORLDS=kirbyam,tracker AP_RUN_UT_LIVE=1 python -m pytest -p pytest_asyncio.plugin -m '' \
    worlds/kirbyam/test/test_universal_tracker_live.py
Requires upstream UT installed as worlds.tracker and permission to bind loopback.
"""
import asyncio
from collections import Counter
from functools import partial
import os
from pathlib import Path

import pytest

pytestmark = pytest.mark.skipif(os.environ.get('AP_RUN_UT_LIVE') != '1', reason='opt-in live UT socket acceptance')


async def wait_until(predicate, label):
    try:
        async with asyncio.timeout(30):
            while not predicate():
                await asyncio.sleep(0.05)
    except TimeoutError as exc:
        raise AssertionError(f"Timed out: {label}") from exc


@pytest.mark.asyncio
async def test_live_yamlless_tracker_history_reconnect_and_goal(tmp_path: Path, monkeypatch):
    # Configure headless operation only; protocol, generation, core and server
    # handlers below are all the real implementations, without mocks.
    import Utils
    monkeypatch.setattr(Utils, 'gui_enabled', False)
    ut = pytest.importorskip('worlds.tracker.TrackerClient')
    monkeypatch.setattr(ut, 'gui_enabled', False)
    from worlds.tracker import TrackerWorld
    from CommonClient import server_loop
    from MultiServer import Context, server
    from NetUtils import ClientStatus, decode, encode
    import websockets
    from .support.integration_generation import generate_archive_from_fixture, load_multidata_from_archive

    player = tmp_path / 'generate.yaml'
    player.write_text('''name: UTLive1054
game: Kirby & The Amazing Mirror
Kirby & The Amazing Mirror:
  ability_randomization_mode: shuffled
  configured_area_boss: random
  goal: defeat_area_boss
  shards: random
  start_inventory:
    Sword Ability: 2
    Cell Phone Battery: 2
    Copy Ability Room Access: 1
''')
    archive = generate_archive_from_fixture(player, tmp_path / 'generated', seed=1054)
    data = load_multidata_from_archive(archive)
    empty_players = tmp_path / 'empty-players'
    empty_players.mkdir()
    # Local settings and persistence remain inside the disposable directory.
    monkeypatch.setattr(Utils.user_path, 'cached_path', str(tmp_path), raising=False)
    monkeypatch.setattr(Utils.persistent_load, 'storage', {}, raising=False)
    (tmp_path / 'Players').mkdir()
    monkeypatch.setattr(TrackerWorld.settings, 'player_files_path', str(empty_players))
    monkeypatch.setattr(TrackerWorld.settings, 'save_entered_commands', False)
    ctx = Context('127.0.0.1', 0, '', '', 1, 10, False)
    ctx.load(str(archive))
    ctx.init_save(False)
    packet_commands = []
    watcher_tasks = []
    received_batches = []

    class ObservedTracker(ut.TrackerGameContext):
        def on_package(self, cmd, args):
            packet_commands.append(cmd)
            if cmd == "ReceivedItems":
                received_batches.append((args["index"], len(args["items"])))
            result = super().on_package(cmd, args)
            if cmd == "Connected" and self.watcher_task is not None:
                watcher_tasks.append(self.watcher_task)
            return result

    tracker = None
    # Port 0 lets the OS atomically allocate an unused loopback port; never
    # probe, reuse, terminate or reconfigure another task's listener.
    async with websockets.serve(partial(server, ctx=ctx), '127.0.0.1', 0) as listener:
        port = listener.sockets[0].getsockname()[1]
        address = f'ws://127.0.0.1:{port}'
        tracker = ObservedTracker(address, None)
        tracker.auth = 'UTLive1054'
        try:
            tracker.run_generator()  # Normal UT startup, with an empty YAML folder.
            tracker.server_task = asyncio.create_task(server_loop(tracker))
            starts = data['precollected_items'][1]
            await wait_until(lambda: tracker.tracker_core.multiworld is not None
                             and len(tracker.items_received) == len(starts), 'initial UT connection/history')
            assert Counter(i.item for i in tracker.items_received) == Counter(starts)
            assert not list(empty_players.iterdir())
            initial = tracker.updateTracker()
            mw = tracker.tracker_core.multiworld
            assert not mw.has_beaten_game(initial.state, 1)
            history_before = list(tracker.items_received)
            checked = set()
            # A protocol game peer reports checks; this is not a Kirby emulator.
            async with websockets.connect(address) as game:
                await game.recv()  # Actual RoomInfo
                await game.send(encode([{'cmd': 'Connect', 'password': None, 'name': 'UTLive1054',
                                         'game': 'Kirby & The Amazing Mirror', 'version': Utils.version_tuple,
                                         'items_handling': 7, 'tags': ['AP'], 'uuid': 'ut1054-live-game',
                                         'slot_data': True}]))
                async with asyncio.timeout(30):
                    while True:
                        messages = decode(await game.recv())
                        assert not any(m['cmd'] == 'ConnectionRefused' for m in messages), messages
                        if any(m['cmd'] == 'Connected' for m in messages):
                            break
                sphere_count = 0
                for sphere in data['spheres']:
                    checks = set(sphere.get(1, []))
                    if not checks:
                        continue
                    reachable = set(tracker.tracker_core.locations_available)
                    assert checks == reachable
                    await game.send(encode([{'cmd': 'LocationChecks', 'locations': sorted(checks)}]))
                    checked |= checks
                    expected_count = len(starts) + len(checked)
                    await wait_until(lambda: len(tracker.items_received) == expected_count
                                     and tracker.checked_locations == checked, 'live checks and received items')
                    result = tracker.updateTracker()
                    assert not checked.intersection(tracker.tracker_core.locations_available)
                    sphere_count += 1
                assert checked == set(data["locations"][1])
                assert mw.has_beaten_game(result.state, 1)
                expected_history = starts + [data['locations'][1][location][0]
                                             for location in checked]
                assert Counter(i.item for i in tracker.items_received) == Counter(expected_history)
                assert tracker.items_received[:len(starts)] == history_before
                await game.send(encode([{'cmd': 'StatusUpdate', 'status': ClientStatus.CLIENT_GOAL}]))
                await wait_until(lambda: ctx.client_game_state[0, 1] == ClientStatus.CLIENT_GOAL,
                                 'server accepted goal status')
                full_history = list(tracker.items_received)
                # Reconnect the same real UT client and require server replay.
                await tracker.disconnect()
                tracker.auth = 'UTLive1054'
                tracker.server_task = asyncio.create_task(server_loop(tracker, address))
                await wait_until(lambda: tracker.tracker_core.multiworld is not None
                                 and len(tracker.items_received) == len(expected_history)
                                 and tracker.checked_locations == checked, 'reconnect full history and checks')
                assert tracker.items_received == full_history
                assert received_batches[-1] == (0, len(full_history))
                replay = tracker.updateTracker()
                assert Counter(i.item for i in tracker.items_received) == Counter(expected_history)
                assert tracker.tracker_core.multiworld.has_beaten_game(replay.state, 1)
                assert packet_commands.count('Connected') == 2
                assert packet_commands.count('ReceivedItems') >= 2
                assert 'RoomUpdate' in packet_commands
                print(f'LIVE_UT_OK port={port} spheres={sphere_count} checks={len(checked)} '
                      f'items={len(expected_history)} connected=2 goal_status=30')
        finally:
            tracker.exit_event.set()
            try:
                await tracker.shutdown()
            finally:
                for task in watcher_tasks:
                    task.cancel()
                await asyncio.gather(*watcher_tasks, return_exceptions=True)
