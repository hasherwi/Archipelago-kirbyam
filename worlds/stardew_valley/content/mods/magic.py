from ...data.skill import Skill
from ...mods.mod_data import ModNames
from ...strings.skill_names import ModSkill
from ..game_content import ContentPack
from ..mod_registry import register_mod_content_pack

register_mod_content_pack(ContentPack(
    ModNames.magic,
    skills=(Skill(name=ModSkill.magic, has_mastery=False),)
))
