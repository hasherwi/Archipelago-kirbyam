"""Source manifests remain metadata-only; built APWorlds keep container metadata."""
import json
import pickle
import zipfile

import pytest

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
    assert summary['archives'] == 30
    assert summary['slots'] == 45
    assert summary['rejected_cases'] == 2
    assert summary['rejected_slots'] == 3
    assert summary['attempts'] == 32
    assert summary['attempted_slots'] == 48
    assert {(row['case'], row['seed'], row['players']) for row in summary['rejections']} == {
        (11, 935, 2), (11, 202610120972, 1),
    }
    assert all(row['reason'].startswith('No reviewed source witness for peg_149_35_18 in mode 2;')
               for row in summary['rejections'])
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


@pytest.mark.parametrize('mode', [0, 1, 2])
@pytest.mark.parametrize('weight', [0, 55, 100])
@pytest.mark.parametrize('statues', [0, 1])
def test_packaging_expected_rejection_matches_only_known_options(mode, weight, statues):
    from ..tools.verify_packaged_generation import expected_source_rejection
    options = {'ability_randomization_mode': mode, 'ability_randomization_no_ability_weight': weight,
               'ability_randomization_statues': statues}
    reason = expected_source_rejection(options)
    assert bool(reason) == (mode in (1, 2) and weight == 100 and statues == 0)
    if reason:
        assert reason == {
            1: 'Reviewed Wheel-source search budget exhausted',
            2: 'No reviewed source witness for peg_149_35_18 in mode 2;',
        }[mode]


@pytest.mark.parametrize('mode,prefix', [
    (1, 'Reviewed Wheel-source search budget exhausted'),
    (2, 'No reviewed source witness for peg_149_35_18 in mode 2;'),
])
def test_packaging_rejection_preserves_reason_and_rejects_unexpected_outcomes(mode, prefix):
    from ..tools.verify_packaged_generation import checked_generation
    options = {'ability_randomization_mode': mode, 'ability_randomization_no_ability_weight': 100,
               'ability_randomization_statues': 0}
    message = prefix + ' diagnostic details'

    def expected():
        raise ValueError(message)

    assert checked_generation(expected, options) == message
    with pytest.raises(AssertionError, match='Expected source rejection did not occur'):
        checked_generation(lambda: None, options)

    def unrelated():
        raise ValueError('No reviewed source witness for fuse_126')

    with pytest.raises(ValueError, match='fuse_126'):
        checked_generation(unrelated, options)
    with pytest.raises(ValueError, match=prefix):
        checked_generation(expected, {**options, 'ability_randomization_statues': 1})

    def wrong_type():
        raise RuntimeError(message)

    with pytest.raises(RuntimeError, match=prefix):
        checked_generation(wrong_type, options)
