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
         '--limit', '16', '--seeds', '935', '202610120972'],
        cwd=runtime, env=env, stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=180,
    )
    assert result.returncode == 0, result.stdout[-8000:]
    summary = json.loads((tmp_path / 'results/summary.json').read_text())
    assert summary['archives'] == 32
    assert summary['slots'] == 48
    assert summary['option_values']['room_sanity'] == ['0', '1']
