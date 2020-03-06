from modules.dragalia.models.dps import DPS
from modules.dragalia.models.skill import Skill
from discord import Embed, Colour
import modules.dragalia.models.constants as CONSTANTS


class Adventurer:
    def __init__(self, name, internal_name, shortcuts):
        self.name = name
        self.internal_name = internal_name.lower()
        self.shortcuts = [x.lower().strip() for x in shortcuts.split(",")]

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
        if dps_db:
            adven_dps = None
            for i_name in dps_db.keys():
                if self.internal_name.lower() == i_name.lower():
                    adven_dps = dps_db[i_name]
                    break
                elif self.internal_name in self.shortcuts:
                    adven_dps = dps_db[i_name]
                    break
            self.dps = DPS(self, adven_dps, rank_db)

    def embed(self):
        embed = Embed(
            title=f"__**{self.name}**__",
            description=f"*{self.title}*",
            colour=Colour(CONSTANTS.elements_colors[self.element.lower()]),
        )
        if self.image == "?":
            embed.set_thumbnail(
                url="https://lh3.googleusercontent.com/proxy/"
                "8segRO0VV4XFNH3CcIyBTp1xB5ITih6En--B3fJm8JjDTFCgvXzWfuMEMQXa_"
                "qa8xf0C9w0abOue4FZMOqlOF0_"
                "vFkhNOefb1WyxDS41boDOhAwgebkWc_yq-dWJcu_LA03Hq9s"
            )
        else:
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
            if "?" in ability:
                continue
            embed.add_field(
                name=f"__Ability:__ {ability[0]}", value=ability[1], inline=False
            )
        return embed
