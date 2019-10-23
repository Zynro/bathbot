import requests
import aiohttp
import csv
from modules.dragalia.models.parse import Parse

DPS_URL_60 = "https://b1ueb1ues.github.io/dl-sim/60/data_kr.csv"
DPS_URL_120 = "https://b1ueb1ues.github.io/dl-sim/120/data_kr.csv"
DPS_URL_180 = "https://b1ueb1ues.github.io/dl-sim/180/data_kr.csv"


def remove_brackets(input_str):
    return input_str.replace("[", "").replace("]", "")


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


def get_src_csv(path):
    response_dict = {}
    response_dict["180"] = requests.get(DPS_URL_180).text
    response_dict["120"] = requests.get(DPS_URL_120).text
    response_dict["60"] = requests.get(DPS_URL_60).text
    for parse in response_dict.keys():
        path_to_file = f"{path}_{parse}.csv"
        with open(path_to_file, "w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            response_dict[parse] = response_dict[parse].split("\n")
            for row in response_dict[parse]:
                row = row.split(",")
                try:
                    row[1]
                except IndexError:
                    continue
                writer.writerow(row)
    return response_dict


async def async_get_src_csv(cls, path):
    response_dict = {}
    async with aiohttp.ClientSession() as session:
        async with session.get(DPS_URL_180) as response:
            response_dict["180"] = await response.text()
        async with session.get(DPS_URL_120) as response:
            response_dict["120"] = await response.text()
        async with session.get(DPS_URL_60) as response:
            response_dict["60"] = await response.text()
    for parse in response_dict.keys():
        path_to_file = f"{path}_{parse}.csv"
        with open(path_to_file, "w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            response_dict[parse] = response_dict[parse].split("\n")
            for row in response_dict[parse]:
                row = row.split(",")
                try:
                    row[1]
                except IndexError:
                    continue
                writer.writerow(row)
    return response_dict


def build_adven_db(response_dict):
    full_char_dict = {}
    damage = {}
    for parse_value in response_dict.keys():
        del response_dict[parse_value][0]
        parse = response_dict[parse_value]
        for row in parse:
            row = row.split(",")
            # print(row)
            try:
                row[1]
            except IndexError:
                continue
            if "_c_" in row[1]:
                continue
            if "Fleur" in row[1]:
                del row[9]
            internal_name = row[1]
            if "_" in row[1]:
                name = row[1].replace("_", "").lower().strip()
                alt = True
            else:
                name = row[1].lower().strip()
                alt = False
            if parse_value == "180":
                amulets = row[6].split("][")
                wyrmprints = amulets[0].split("+")
                wyrmprints = remove_brackets(" + ".join(wyrmprints))
                wyrmprints = wyrmprints.replace("_", " ")
                dragon = remove_brackets(amulets[1])
                full_char_dict[name] = {
                    "name": name,
                    "internal_name": internal_name,
                    "rarity": row[2],
                    "element": row[3],
                    "weapon": row[4],
                    "str": row[5],
                    "wyrmprints": wyrmprints,
                    "dragon": dragon,
                    "alt": alt,
                }
                full_char_dict[name]["parse"] = {}
            damage = {}
            damage_list = row[9:]
            damage["dps"] = row[0]
            damage["types"] = {}
            for damage_type in damage_list:
                damage_type = damage_type.split(":")
                damage_name = damage_type[0].replace("_", " ").title()
                damage["types"][damage_name] = damage_type[1]
            full_char_dict[name]["parse"][parse_value] = {}
            full_char_dict[name]["parse"][parse_value]["damage"] = damage
            (full_char_dict[name]["parse"][parse_value]["condition"]) = (
                row[7].replace("<", "").replace(">", ""),
            )
            full_char_dict[name]["parse"][parse_value]["comment"] = row[8]
    return full_char_dict


class DPS:
    def __init__(self, adventurer, dps_dict):
        self.owner = adventurer
        self.wyrmprints = dps_dict["wyrmprints"]
        if "dps" in dps_dict["dragon"]:
            split = dps_dict["dragon"].split(";")
            dps_range = split[1].lower().replace("dpsrange:", "DPS Range: ")
            dps_range = dps_range.replace("~", " ~ ")
            self.dragon = f"{split[0]}\n*{dps_range}*"
        else:
            self.dragon = dps_dict["dragon"]
        self.parse = {}
        for parse_value in ["180", "120", "60"]:
            self.parse[parse_value] = Parse(dps_dict["parse"][parse_value])
        self.image = adventurer.image
        self.alt = dps_dict["alt"]
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
