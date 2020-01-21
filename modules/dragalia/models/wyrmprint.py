from discord import Embed, Colour
import modules.dragalia.models.constants as CONSTANTS
import lib.misc_methods as MISC


class Wyrmprint:
    def __init__(self, name):
        self.name = name

    def update(self, wp_dict):
        self.abilities = {}
        for k in wp_dict.keys():
            k = k.lower()
            if k.lower().startswith("ability") and "N/A" not in wp_dict[k]:
                name = wp_dict[k].split(":")[0].strip()
                desc = ":".join(wp_dict[k].split(":")[1:])
                desc = desc.strip()
                self.abilities[name] = desc
            setattr(self, k, wp_dict[k])

    def embed(self):
        rarity = CONSTANTS.d_emoji[str(self.rarity) + "*"] * int(self.rarity)
        embed = Embed(
            title=self.name,
            description=rarity,
            colour=Colour(MISC.generate_random_color()),
        )
        embed.set_thumbnail(url=self.thumbnail)

        embed.add_field(
            name="__Max Stats:__",
            value=f"""**HP:** {self.max_hp}
**STR:** {self.max_str}""",
            inline=True,
        )
        embed.add_field(
            name="__Obtained From:__",
            value=f"{self.obtained}: {self.availability}",
            inline=True,
        )
        for k, v in self.abilities.items():
            embed.add_field(name=f"__Ability__: {k}", value=v, inline=False)
        return embed
