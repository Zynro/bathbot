from modules.dragalia.models.dps import DPS
from modules.dragalia.models.skill import Skill
from discord import Embed, Colour
import modules.dragalia.models.constants as CONSTANTS


class Adventurer:
    def __init__(self, name, internal_name):
        self.name = name
        self.internal_name = internal_name

    def update(self, adven_dict, skills=None, dps_db=None, rank_db=None):
        for k in adven_dict.keys():
            k = k.lower()
            setattr(self, k, adven_dict[k])
        try:
            self.max_coab = self.max_coab.replace(" Benefits your whole team. ", "")
        except AttributeError:
            pass
        if skills:
            skill_1 = [x for x in skills if x["name"] == self.skill_1]
            skill_2 = [x for x in skills if x["name"] == self.skill_2]
            self.skill_1 = Skill(skill_1)
            self.skill_2 = Skill(skill_2)
        try:
            adven_dps = dps_db[self.internal_name]
        except KeyError:
            adven_dps = None
        self.dps = DPS(self, adven_dps, rank_db)

    def embed(self):
        embed = Embed(
            title=f"__**{self.name}**__",
            description=f"*{self.title}*",
            colour=Colour(CONSTANTS.elements_colors[self.element.lower()]),
        )
        embed.set_thumbnail(url=self.image)
        rarity = CONSTANTS.d_emoji[str(self.rarity) + "*"] * int(self.rarity)
        embed.add_field(
            name=f"{rarity}\n__Max Stats:__",
            value=f"""**HP:** {self.max_hp}
**STR:** {self.max_str}
**DEF:** {self.defense}""",
            inline=True,
        )
        coab = self.max_coab.split(":")
        embed.add_field(
            name=f"""{CONSTANTS.d_emoji[self.element.lower()]}{CONSTANTS.d_emoji[self.weapon.lower()]}
__Max Co-Ab:__""",
            value=f"**{coab[0]}:**\n{coab[1]}",
            inline=True,
        )
        embed.add_field(
            name=f"__Skill:__ {self.skill_1.adven_embed()[0]}",
            value=self.skill_1.adven_embed()[1],
            inline=False,
        )
        embed.add_field(
            name=f"__Skill:__ {self.skill_2.adven_embed()[0]}",
            value=self.skill_2.adven_embed()[1],
            inline=False,
        )
        for x in range(1, 4):
            ability = getattr(self, f"ability_{x}").split(":")
            embed.add_field(
                name=f"__Ability:__ {ability[0]}", value=ability[1], inline=False
            )
        return embed
