"""Remove only the exact reviewed generated-Ice composition from older records."""
from copy import deepcopy
from .kibble310_history import digest


def before_frosty825_generated(target):
    from .fire825_history import before_fire_target
    result = before_fire_target(target)
    if result['id'] == 'frozen_825_sound_effects':
        assert result.pop('advanced_graphs') == ['generated_ice']
        assert digest(result['graphs'].pop('generated_ice')) == '951c005dbcb4b76d6718ad4ce4d8847a20758ec485f3245f1e01ab0ccae29058'
    return result
