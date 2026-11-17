"""Source manifests remain metadata-only; built APWorlds keep container metadata."""
import json
import pickle
import zipfile

from ..build import build_apworld_in_place
from ..options import StartingKirbyColor


def test_package_manifest_does_not_mutate_source(tmp_path):
    root = tmp_path / 'kirbyam'
    root.mkdir()
    manifest = root / 'archipelago.json'
    source = b'{"game": "Kirby & The Amazing Mirror", "world_version": "0.3.1"}\n'
    manifest.write_bytes(source)
    (root / '__init__.py').write_text('')
    for version in (7, 8):
        package = build_apworld_in_place(root, 'kirbyam', version)
        assert manifest.read_bytes() == source
        with zipfile.ZipFile(package) as archive:
            built = json.loads(archive.read('kirbyam/archipelago.json'))
        assert built == {**json.loads(source), 'version': version, 'compatible_version': version}


def test_dynamic_starting_color_can_be_pickled_for_webhost():
    for color in StartingKirbyColor.name_lookup:
        value = StartingKirbyColor(color)
        restored = pickle.loads(pickle.dumps(value))
        assert type(restored) is StartingKirbyColor
        assert restored.value == color


def test_built_apworld_generates_single_and_multi_player_archives(tmp_path):
    """Exercise the installed ZIP, including room sanity, not a loose-source import."""
    import os
    from pathlib import Path
    import shutil
    import subprocess
    import sys

    world_root = Path(__file__).resolve().parents[1]
    staged = tmp_path / 'kirbyam'
    shutil.copytree(world_root, staged, ignore=shutil.ignore_patterns(
        '__pycache__', '*.pyc', '*.apworld', 'save_states', '*.gba', '*.sav'))
    artifact = build_apworld_in_place(staged, 'kirbyam')
    # Use the normal world loader in a minimal isolated copy of this AP runtime.
    # Registering the ZIP after importing worlds would miss its network data package.
    runtime = tmp_path / 'runtime'
    runtime.mkdir()
    repository = world_root.parents[1]
    for source in repository.glob('*.py'):
        shutil.copy2(source, runtime / source.name)
    for name in ('rule_builder', 'apmw'):
        shutil.copytree(repository / name, runtime / name,
                        ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    (runtime / 'worlds').mkdir()
    for source in (repository / 'worlds').glob('*.py'):
        shutil.copy2(source, runtime / 'worlds' / source.name)
    for name in ('generic', '_bizhawk'):
        shutil.copytree(repository / 'worlds' / name, runtime / 'worlds' / name,
                        ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    (runtime / 'custom_worlds').mkdir()
    installed = runtime / 'custom_worlds/kirbyam.apworld'
    shutil.copy2(artifact, installed)
    bootstrap = "import runpy,sys;runpy.run_path(sys.argv.pop(1),run_name='__main__')"
    env = dict(os.environ, AP_TEST_WORLDS='kirbyam', SKIP_REQUIREMENTS_UPDATE='1',
               PYTHONDONTWRITEBYTECODE='1')
    result = subprocess.run(
        [sys.executable, '-c', bootstrap, str(world_root / 'tools/verify_packaged_generation.py'),
         '--apworld', str(installed), '--output', str(tmp_path / 'results'),
         '--limit', '4', '--seeds', '935', '202610120972'],
        cwd=runtime, env=env, stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=180,
    )
    assert result.returncode == 0, result.stdout[-8000:]
    summary = json.loads((tmp_path / 'results/summary.json').read_text())
    # The first four cases use native sources. Heterogeneous second players
    # still exercise RoomSanity; the verifier checks their actual room IDs.
    assert summary['archives'] == 8
    assert summary['slots'] == 12
    assert summary['option_values']['ability_randomization_mode'] == ['0']
    # The first randomized-source multiworld from the historical matrix is
    # intentionally rejected under #1099. Exercise the installed guard without
    # teaching the verification tool to forgive arbitrary generation failures.
    rejection_output = tmp_path / 'rejection'
    result = subprocess.run(
        [sys.executable, '-c', bootstrap, str(world_root / 'tools/verify_packaged_generation.py'),
         '--apworld', str(installed), '--output', str(rejection_output),
         '--limit', '5', '--seeds', '935', '202610120972'],
        cwd=runtime, env=env, stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=180,
    )
    assert result.returncode == 1, result.stdout[-8000:]
    assert 'FAIL case=4 seed=202610120972 players=2;' in result.stdout
    assert result.stdout.count('Traceback (most recent call last):') == 1
    assert 'During handling of the above exception' not in result.stdout
    assert 'ExceptionGroup' not in result.stdout
    assert 'worlds.kirbyam.check_accessibility.KirbyAmCheckAccessibilityError:' in result.stdout
    assert 'kirbyam.apworld/kirbyam/check_accessibility.py' in result.stdout.replace('\\', '/')
    diagnostic = ("Player 2 (Probe2): unfilled=[]; unavailable even with all inventory=['Room 4-16']; "
                  "unreachable from placed progression=[]")
    assert result.stdout.rstrip().endswith(diagnostic), result.stdout[-8000:]
    assert result.stdout.count('unavailable even with all inventory=') == 1
    assert not tuple(rejection_output.rglob('*.zip'))
    assert not (rejection_output / 'summary.json').exists()
    retained, = rejection_output.glob('case-*')
    import yaml
    players = [yaml.safe_load((retained / 'players' / f'{player}.yaml').read_text())
               ['Kirby & The Amazing Mirror'] for player in (1, 2)]
    assert [player['room_sanity'] for player in players] == [0, 1]
    assert all(player['ability_randomization_mode'] == 1 for player in players)
    # Real YAML generation, not a manually injected precollection or slot flag.
    result = subprocess.run(
        [sys.executable, '-c', bootstrap, str(world_root / 'tools/verify_packaged_generation.py'),
         '--apworld', str(installed), '--output', str(tmp_path / 'precollection'),
         '--copy-room-precollection', '--seeds', '1002'],
        cwd=runtime, env=env, stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=180,
    )
    assert result.returncode == 0, result.stdout[-8000:]
    summary = json.loads((tmp_path / 'precollection/summary.json').read_text())
    assert summary['archives'] == 2
    assert summary['slots'] == 3
    assert summary['option_values']['room_sanity'] == ['0', '1']


def test_packaged_data_listing_uses_a_package_anchor(monkeypatch, tmp_path):
    """Enforce Python 3.11's package-only resources contract on newer Python too."""
    import importlib
    data_module = importlib.import_module("worlds.kirbyam.data")
    real_files = data_module.resources.files

    def package_only_files(anchor):
        module = importlib.import_module(anchor)
        if module.__spec__.submodule_search_locations is None:
            raise TypeError(f"{anchor!r} is not a package")
        return real_files(anchor)

    # The direct filesystem fast path is unavailable inside an APWorld ZIP.
    monkeypatch.setattr(data_module, "__file__", str(tmp_path / "kirbyam.apworld/kirbyam/data.py"))
    monkeypatch.setattr(data_module.resources, "files", package_only_files)
    assert "rooms.json" in data_module._list_data_files("regions")
