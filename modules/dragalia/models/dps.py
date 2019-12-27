import requests
import aiohttp
import csv
import random
from discord import Embed, Colour
from modules.dragalia.models.parse import Parse
import modules.dragalia.models.constants as CONSTANTS


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
    suffixes = {1: "st", 2: "nd", 3: "rd", "1": "st", "2": "nd", "3": "rd"}
    if len(str(number)) > 1:
        if int(str(number)[-2]) in [11, 12, 13]:
            return str(number) + "th"
    if int(str(number)[-1]) in suffixes.keys():
        return str(number) + suffixes[str(number)[-1]]
    return str(number) + "th"


class DPS:
    def __init__(self, adventurer, dps_dict, rank_db):
        if not dps_dict:
            return
        self.adventurer = adventurer
        self.owner = adventurer.internal_name
        self.wyrmprints = dps_dict["wyrmprints"]
        self.element = adventurer.element.lower()
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

        for parse_value in self.parse.keys():
            self.parse[parse_value].rank_element = str(
                rank_db[parse_value][self.element].index(self.owner) + 1
            )
            self.parse[parse_value].rank_overall = str(
                rank_db[parse_value]["all"].index(self.owner) + 1
            )

    def embed(self, parse_value="180"):
        try:
            embed = Embed(
                title=f"__**{self.adventurer.name}**__",
                description=f"*Parse: {parse_value} Seconds*",
                colour=Colour(
                    CONSTANTS.elements_colors[self.adventurer.element.lower()]
                ),
            )
        except (AttributeError, IndexError):
            embed = Embed(
                title=f"__**Error:**__",
                description=f"This adventurer does exist, but currently does not have a"
                " simulated DPS profile.\n"
                "Check back later for updates!\n\n"
                "You can also see their adventurer info embed by using the"
                " `&d [a/adv/adven] <adventurer>` command, where <adventurer>"
                " is an adventurer.\n\n"
                "i.e. `&d adv Marth`",
                colour=Colour(random.randint(0, 0xFFFFFF)),
            )
            return embed
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
            value=self.parse[parse_value].to_dps_string(),
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

    @staticmethod
    def get_src_csv(path):
        dps_dict = {}
        dps_dict["180"] = requests.get(CONSTANTS.DPS_URL_180).text
        dps_dict["120"] = requests.get(CONSTANTS.DPS_URL_120).text
        dps_dict["60"] = requests.get(CONSTANTS.DPS_URL_60).text
        for parse in dps_dict.keys():
            path_to_file = f"{path}_{parse}.csv"
            with open(path_to_file, "w", newline="", encoding="utf-8") as file:
                writer = csv.writer(file)
                dps_dict[parse] = dps_dict[parse].split("\n")
                for row in dps_dict[parse]:
                    row = row.split(",")
                    try:
                        if "_c_" in row[1]:
                            continue
                        else:
                            row[1] = row[1].replace("_", "").lower().strip()
                            writer.writerow(row)
                    except IndexError:
                        continue
        return dps_dict

    @staticmethod
    async def async_get_src_csv(path):
        dps_dict = {}
        async with aiohttp.ClientSession() as session:
            async with session.get(CONSTANTS.DPS_URL_180) as response:
                dps_dict["180"] = await response.text()
            async with session.get(CONSTANTS.DPS_URL_120) as response:
                dps_dict["120"] = await response.text()
            async with session.get(CONSTANTS.DPS_URL_60) as response:
                dps_dict["60"] = await response.text()
        for parse in dps_dict.keys():
            path_to_file = f"{path}_{parse}.csv"
            with open(path_to_file, "w", newline="", encoding="utf-8") as file:
                writer = csv.writer(file)
                dps_dict[parse] = dps_dict[parse].split("\n")
                for row in dps_dict[parse]:
                    row = row.split(",")
                    try:
                        if "_c_" in row[1]:
                            continue
                        else:
                            writer.writerow(row)
                    except IndexError:
                        continue
        return dps_dict

    @staticmethod
    def build_dps_db(response_dict):
        all_char_dps = {}
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
                if "fleur" in row[1]:
                    del row[9]
                if "_" in row[1]:
                    internal_name = row[1].replace("_", "").lower().strip()
                    """if (
                        "geuden" in internal_name
                    ):  # dps has it as geuden, wiki is gala prince
                        internal_name = "gprince"
                    if "euden" in internal_name:  # same as above, but normal version
                        internal_name = "theprince"
                    alt = True"""
                else:
                    internal_name = row[1].lower().strip()
                    alt = False
                if parse_value == "180":
                    amulets = row[6].split("][")
                    wyrmprints = amulets[0].split("+")
                    wyrmprints = remove_brackets(" + ".join(wyrmprints))
                    wyrmprints = wyrmprints.replace("_", " ")
                    dragon = remove_brackets(amulets[1])
                    all_char_dps[internal_name] = {
                        "internal_name": internal_name,
                        "rarity": row[2],
                        "element": row[3],
                        "weapon": row[4],
                        "str": row[5],
                        "wyrmprints": wyrmprints,
                        "dragon": dragon,
                        "alt": alt,
                    }
                    all_char_dps[internal_name]["parse"] = {}
                damage = {}
                damage_list = row[9:]
                damage["dps"] = row[0]
                damage["types"] = {}
                for damage_type in damage_list:
                    damage_type = damage_type.split(":")
                    damage_name = damage_type[0].replace("_", " ").title()
                    damage["types"][damage_name] = damage_type[1]
                all_char_dps[internal_name]["parse"][parse_value] = {}
                all_char_dps[internal_name]["parse"][parse_value]["damage"] = damage
                (all_char_dps[internal_name]["parse"][parse_value]["condition"]) = (
                    row[7].replace("<", "").replace(">", ""),
                )
                all_char_dps[internal_name]["parse"][parse_value]["comment"] = row[8]
        return all_char_dps

    @staticmethod
    def build_rank_db(dps_db):
        rankings_db = {}
        parses = ["180", "120", "60"]

        for parse in parses:
            rankings_db[parse] = {}
            sorted_list = sorted(
                [
                    (
                        dps_db[adven]["internal_name"],
                        int(dps_db[adven]["parse"][parse]["damage"]["dps"]),
                    )
                    for adven in dps_db.keys()
                ],
                key=lambda x: x[1],
                reverse=True,
            )
            rankings_db[parse]["all"] = [i[0] for i in sorted_list]
            for element in CONSTANTS.dragalia_elements:
                sorted_list = sorted(
                    [
                        (
                            dps_db[adven]["internal_name"],
                            int(dps_db[adven]["parse"][parse]["damage"]["dps"]),
                        )
                        for adven in dps_db.keys()
                        if dps_db[adven]["element"] == element
                    ],
                    key=lambda x: x[1],
                    reverse=True,
                )
                rankings_db[parse][element] = [i[0] for i in sorted_list]
        return rankings_db
