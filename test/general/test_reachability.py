import unittest

from BaseClasses import CollectionState
from worlds.AutoWorld import AutoWorldRegister
from . import setup_solo_multiworld, gen_steps


class TestBase(unittest.TestCase):
    world_relevant = True
    gen_steps = gen_steps

    default_settings_unreachable_regions = {
        # Kirby retains empty tutorial/final-area placeholders and dormant split rooms.
        # Active locations are still checked above; #945 covers room-sanity ingress.
        "Kirby & The Amazing Mirror": {
            'REGION_CANDY_CONSTELLATION/ROOM_9_CHEST_2',
            'REGION_CARROT_CASTLE/ROOM_5_13',
            'REGION_DIMENSION_MIRROR/ROOM_10_01',
            'REGION_DIMENSION_MIRROR/ROOM_10_02',
            'REGION_DIMENSION_MIRROR/ROOM_10_03',
            'REGION_DIMENSION_MIRROR/ROOM_10_04',
            'REGION_DIMENSION_MIRROR/ROOM_10_05',
            'REGION_DIMENSION_MIRROR/ROOM_10_06',
            'REGION_DIMENSION_MIRROR/ROOM_10_07',
            'REGION_DIMENSION_MIRROR/ROOM_10_08',
            'REGION_DIMENSION_MIRROR/ROOM_10_09',
            'REGION_DIMENSION_MIRROR/ROOM_10_10',
            'REGION_DIMENSION_MIRROR/ROOM_10_11',
            'REGION_DIMENSION_MIRROR/ROOM_10_12',
            'REGION_DIMENSION_MIRROR/ROOM_10_13',
            'REGION_DIMENSION_MIRROR/ROOM_10_14',
            'REGION_DIMENSION_MIRROR/ROOM_10_15',
            'REGION_DIMENSION_MIRROR/ROOM_10_16',
            'REGION_DIMENSION_MIRROR/ROOM_10_17',
            'REGION_MOONLIGHT_MANSION/ROOM_2_04_FROM_2_07',
            'REGION_MOONLIGHT_MANSION/ROOM_2_05_LOWER',
            'REGION_MOONLIGHT_MANSION/ROOM_2_06',
            'REGION_MOONLIGHT_MANSION/ROOM_2_08_BOMB_ROOM',
            'REGION_MOONLIGHT_MANSION/ROOM_2_12_RIGHT',
            'REGION_MOONLIGHT_MANSION/ROOM_2_15_UPPER_LEDGE_SPAWN',
            'REGION_OLIVE_OCEAN/ROOM_6_05',
            'REGION_RADISH_RUINS/ROOM_8_07__LOGIC__ENTRY_FROM_8_18_OR_8_21_OR_8_23',
            'REGION_RADISH_RUINS/ROOM_8_07__LOGIC__ENTRY_FROM_8_GOAL_1',
            'REGION_RADISH_RUINS/ROOM_8_09',
            'REGION_TUTORIAL/ROOM_0_01',
            'REGION_TUTORIAL/ROOM_0_02',
            'REGION_TUTORIAL/ROOM_0_03',
        },
        "A Link to the Past": {
            "Chris Houlihan Room",  # glitch room by definition
            "Desert Northern Cliffs",  # on top of mountain, only reachable via OWG
            "Dark Death Mountain Bunny Descent Area"  # OWG Mountain descent
        },
        # These Blasphemous regions are not reachable with default options
        "Blasphemous": {
            "D01Z04S13[SE]", # difficulty must be hard
            "D01Z05S25[E]", # difficulty must be hard
            "D02Z02S05[W]", # difficulty must be hard and purified_hand must be true
            "D04Z01S06[E]", # purified_hand must be true
            "D04Z02S02[NE]", # difficulty must be hard and purified_hand must be true
            "D05Z01S11[SW]", # difficulty must be hard
            "D06Z01S08[N]", # difficulty must be hard and purified_hand must be true
            "D20Z02S11[NW]", # difficulty must be hard
            "D20Z02S11[E]", # difficulty must be hard
        },
        "Ocarina of Time": {
            "Prelude of Light Warp",  # Prelude is not progression by default
            "Serenade of Water Warp",  # Serenade is not progression by default
            "Lost Woods Mushroom Timeout",  # trade quest starts after this item
            "ZD Eyeball Frog Timeout",  # trade quest starts after this item
            "ZR Top of Waterfall",  # dummy region used for entrance shuffle
        },
        # The following SM regions are only used when the corresponding StartLocation option is selected (so not with
        # default settings). Also, those don't have any entrances as they serve as starting Region (that's why they
        # have to be excluded for testAllStateCanReachEverything).
        "Super Metroid": {
            "Ceres",
            "Gauntlet Top",
            "Mama Turtle"
        }
    }

    def test_default_all_state_can_reach_everything(self):
        """Ensure all state can reach everything and complete the game with the defined options"""
        for game_name, world_type in AutoWorldRegister.testable_worlds.items():
            unreachable_regions = self.default_settings_unreachable_regions.get(game_name, set())
            with self.subTest("Game", game=game_name):
                multiworld = setup_solo_multiworld(world_type)
                state = multiworld.get_all_state()
                for location in multiworld.get_locations():
                    with self.subTest("Location should be reached", location=location.name):
                        self.assertTrue(location.can_reach(state), f"{location.name} unreachable")

                for region in multiworld.get_regions():
                    if region.name in unreachable_regions:
                        with self.subTest("Region should be unreachable", region=region.name):
                            self.assertFalse(region.can_reach(state))
                    else:
                        with self.subTest("Region should be reached", region=region.name):
                            self.assertTrue(region.can_reach(state))

                with self.subTest("Completion Condition"):
                    self.assertTrue(multiworld.can_beat_game(state))

    def test_default_empty_state_can_reach_something(self):
        """Ensure empty state can reach at least one location with the defined options"""
        for game_name, world_type in AutoWorldRegister.testable_worlds.items():
            with self.subTest("Game", game=game_name):
                multiworld = setup_solo_multiworld(world_type)
                state = CollectionState(multiworld)
                all_locations = multiworld.get_locations()
                if all_locations:
                    locations = set()
                    for location in all_locations:
                        if location.can_reach(state):
                            locations.add(location)
                    self.assertGreater(len(locations), 0,
                                       msg="Need to be able to reach at least one location to get started.")
