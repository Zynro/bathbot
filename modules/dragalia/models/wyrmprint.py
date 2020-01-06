from discord import Embed, Colour
import modules.dragalia.models.constants as CONSTANTS
import lib.misc_methods as MISC


class Wyrmprint:
    def __init__(self, wp_dict):
        self.update(self)

    def update(self, wp_dict):
        self.abilites = {}
        for k in wp_dict.keys():
            k = k.lower()
            if "ability" in k.lower() and "N/A" not in wp_dict[k]:
                self.abilities[wp_dict[k].split(": ")[0]] = wp_dict[k].split(": ")[1]
            setattr(self, k, wp_dict[k])

    def embed(self):
        embed = Embed(
            title=self.name,
            description=" ",
            colour=Colour(MISC.generate_random_color()),
        )
        embed.set_thumbnail(url=self.thumbnail)
        rarity = CONSTANTS.d_emoji[str(self.rarity) + "*"] * int(self.rarity)
        embed.add_field(
            name=f"{rarity}\n__Max Stats:__",
            value=f"""**HP:** {self.max_hp}
**STR:** {self.max_str}""",
            inline=True,
        )
        embed.add_field(
            name=f"__Obtained From:__",
            value=f"{self.obtained}: {self.availability}",
            inline=True,
        )
        for k, v in self.abilities:
            embed.add_field(name=f"__Ability__: {k}", value=v, inline=False)
        return Embed
