from modules.dragalia.models.dps import DPS
from modules.dragalia.models.skill import Skill
from discord import Embed, Colour
import modules.dragalia.models.constants as CONSTANTS


class Adventurer:
    def __init__(self, adven_dict, skills, dps_db, rank_db):
        for k in adven_dict.keys():
            k = k.lower()
            setattr(self, k, adven_dict[k])
        skill_1 = [x for x in skills if x["name"] == self.skill_1]
        skill_2 = [x for x in skills if x["name"] == self.skill_2]
        self.skill_1 = Skill(skill_1)
        self.skill_2 = Skill(skill_2)
        self.dps = DPS(self, dps_db, rank_db)

    def embed(self):
        embed = Embed(
            title=f"__**{self.name}**__",
            description=f"*{self.title}*",
            colour=Colour(CONSTANTS.elements_colors[self.adventurer.element.lower()]),
        )
        embed.set_thumbnail(url=self.image)
        embed.add_field()
        embed.set_author(name="Adventurer:")
        return embed
