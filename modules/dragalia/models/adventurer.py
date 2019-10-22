from modules.dragalia.models.parse import Parse


def number_emoji_generator(dps: str = None):
    number_emoji_dict = {
        "1": ":one:",
        "2": ":two:",
        "3": ":three:",
        "4": ":four:",
        "5": ":five:",
        "6": ":six:",
        "7": ":seven:",
        "8": ":eight:",
        "9": ":nine:",
        "0": ":zero:",
    }
    dps_string = ""
    for digit in dps:
        dps_string += number_emoji_dict[digit]
    return dps_string


def add_number_suffix(number):
    number = int(number)
    suffixes = {1: "st", 2: "nd", 3: "rd"}
    if number in [11, 12, 13]:
        return str(number) + "th"
    elif number in suffixes.keys():
        return str(number) + suffixes[number]
    else:
        return str(number) + "th"


class Adventurer:
    def __init__(self, adven_db):
        self.name = adven_db["name"]
        self.image = adven_db["image"]
        self.internal_name = adven_db["internal_name"]
        self.title = adven_db["title"]
        self.max_hp = adven_db["max_hp"]
        self.max_str = adven_db["max_str"]
        self.defense = adven_db["defense"]
        self.unit_type = adven_db["type"]
        self.rarity = adven_db["rarity"]
        self.element = adven_db["element"]
        self.weapon = adven_db["weapon"]
        self.max_coab = adven_db["max_coab"]
        self.skill_1 = adven_db["skill_1"]
        self.skill_2 = adven_db["skill_2"]
        self.ability_1 = adven_db["ability_1"]
        self.ability_2 = adven_db["ability_2"]
        self.ability_3 = adven_db["ability_3"]
        self.availability = adven_db["availability"]
        self.obtained = adven_db["obtained"]
        self.release = adven_db["release"]

        self.wyrmprints = adven_db["wyrmprints"]
        if "dps" in character_dict["dragon"]:
            split = character_dict["dragon"].split(";")
            dps_range = split[1].lower().replace("dpsrange:", "DPS Range: ")
            dps_range = dps_range.replace("~", " ~ ")
            self.dragon = f"{split[0]}\n*{dps_range}*"
        else:
            self.dragon = character_dict["dragon"]
        self.parse = {}
        for parse_value in ["180", "120", "60"]:
            self.parse[parse_value] = Parse(character_dict["parse"][parse_value])
        self.image = (
            f"https://b1ueb1ues.github.io/dl-sim/pic/character/{internal_name}.png"
        )
        self.internal_name = internal_name.replace("_", " ")
        self.alt = character_dict["alt"]
        return

    def update_rank(self, rank_dict):
        for parse_value in self.parse:
            self.parse[parse_value].rank_element = str(
                rank_dict[parse_value][self.element].index(self.name) + 1
            )
            self.parse[parse_value].rank_overall = str(
                rank_dict[parse_value]["all"].index(self.name) + 1
            )

    def populate_embed(self, embed, parse_value):
        embed.set_thumbnail(url=self.image)
        embed.add_field(
            name="__DPS:__",
            value=number_emoji_generator(self.parse[parse_value].dps),
            inline=True,
        )
        element_rank = add_number_suffix(self.parse[parse_value].rank_element)
        overall_rank = add_number_suffix(self.parse[parse_value].rank_overall)
        embed.add_field(
            name="__Rankings:__",
            value=f"**{self.element.title()}:** {element_rank} "
            f"\n**Overall:** {overall_rank}",
        )
        embed.add_field(name="__Dragon:__", value=self.dragon, inline=True)
        embed.add_field(name="__Wyrmprints:__", value=self.wyrmprints, inline=True)
        embed.add_field(
            name="__Damage Breakdown:__",
            value=self.parse[parse_value].type_to_string(),
            inline=False,
        )
        if self.parse[parse_value].condition:
            embed.add_field(
                name="__Condition:__", value=self.parse[parse_value].condition
            )
        if self.parse[parse_value].comment:
            embed.add_field(name="__Comment:__", value=self.parse[parse_value].comment)
        embed.set_footer(
            text="Use the up/down arrows to increase or decrease parse time."
        )
        embed.set_author(name="Adventurer:")
        return embed
