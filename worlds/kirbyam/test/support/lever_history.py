"""Reverse only the exact reviewed Radish/Carrot compartment surface changes.

Keep historical native evidence immutable. The projection asserts every changed
surface before restoring its previous structural form; it is not route proof.
"""
import json
from pathlib import Path


def before_lever_compartments(surfaces):
    fixture = json.loads((Path(__file__).parents[1] / 'data/lever-surface-projection.json').read_text())
    owners = {row['owner'] for row in fixture['current']}
    assert [row for row in surfaces if row['owner'] in owners] == fixture['current']
    historical = fixture['historical']
    projected = []
    for owner in sorted({row['owner'] for row in surfaces}):
        projected.extend(historical.get(owner, [] if owner in owners else
                                        [row for row in surfaces if row['owner'] == owner]))
    assert len(surfaces) - len(projected) == 8
    return projected
