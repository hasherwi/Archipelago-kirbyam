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
