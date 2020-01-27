import requests
import csv
import random
import json
from discord import Embed, Colour
from modules.dragalia.models.parse import Parse
import modules.dragalia.models.constants as CONST
import lib.misc_methods as MISC
from itertools import combinations as combs


def remove_brackets(input_str):
    return input_str.replace("[", "").replace("]", "")


def add_number_suffix(number):
    number = int(number)
    suffixes = {1: "st", 2: "nd", 3: "rd", "1": "st", "2": "nd", "3": "rd"}
    if len(str(number)) > 1:
        if int(str(number)[-2]) in [11, 12, 13]:
            return str(number) + "th"
    if int(str(number)[-1]) in suffixes.keys():
        return str(number) + suffixes[str(number)[-1]]
    return str(number) + "th"


def save_parse_csvs(self, path, dps_dict):
    """
    Given a DPS dict, the combo, and the parse dic
    """
    with open(path, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        dps_dict = dps_dict.split("\n")
        for row in dps_dict:
            row = row.split(",")
            try:
                writer.writerow(row)
            except IndexError:
                continue


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
        for parse_value in CONST.parses:
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
                description=f"**Parse:** {parse_value} Seconds\n"
                f"**Team DPS:** {CONST.team_damage}",
                colour=Colour(CONST.elements_colors[self.adventurer.element.lower()]),
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
            value=MISC.num_emoji_gen(self.parse[parse_value].dps),
            inline=True,
        )
        element_rank = add_number_suffix(self.parse[parse_value].rank_element)
        overall_rank = add_number_suffix(self.parse[parse_value].rank_overall)
        embed.add_field(
            name="__Ranks:__",
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

    def embed_update(self):
        return Embed(
            title="__**Notice:**__",
            description="There is an update available"
            " for adventurer DPS profiles.\nPlease run the command `&drag update` and "
            "check your adventurer again after the update has completed.",
        )

    @staticmethod
    def update_master_hash():
        path = f"modules/dragalia/lists"
        with open(f"{path}/dps_hash.json", "w") as file:
            version = MISC.get_master_hash(CONST.REPO_URL)
            json.dump(version, file, indent=4)
            return version

    @staticmethod
    def pull_csvs(path):
        """
        Given a path, gets and saves all csvs for all co-ability combinations
        from source, returning a complete dictionary of all combinations and all parses.
        """
        dps_dict = {}
        parsed_dict = {}
        dps_dict["none"] = {
            "180": requests.get(CONST.GET_URL(180, "none")).text,
            "120": requests.get(CONST.GET_URL(120, "none")).text,
            "60": requests.get(CONST.GET_URL(60, "none")).text,
        }
        for x in range(1, len(CONST.coab_sort) + 1):
            for coabs in combs(CONST.coab_sort, x):
                dps_dict[coabs] = {}
                dps_dict[coabs]["180"] = requests.get(CONST.GET_URL(180, coabs)).text
                dps_dict[coabs]["120"] = requests.get(CONST.GET_URL(120, coabs)).text
                dps_dict[coabs]["60"] = requests.get(CONST.GET_URL(60, coabs)).text
                parsed_dict[coabs] = {}
                for parse, dps_dict in dps_dict[coabs].items():
                    path_to_file = f"{path}_{coabs}_{parse}.csv"
                    parsed_dict[coabs][parse] = DPS.build_dps_dict(dps_dict[coabs])
                    save_parse_csvs(path_to_file, dps_dict)
        return parsed_dict

    @staticmethod
    async def async_pull_csvs(session, path):
        """
        Given a path, gets and saves all csvs for all co-ability combinations
        from source, returning a complete dictionary of all combinations and all parses.
        ++ASYNC version++
        """
        dps_dict = {}
        parsed_dict = {}
        dps_dict["none"] = {
            "180": requests.get(CONST.GET_URL(180, "none")).text,
            "120": requests.get(CONST.GET_URL(120, "none")).text,
            "60": requests.get(CONST.GET_URL(60, "none")).text,
        }
        for x in range(1, len(CONST.coab_sort) + 1):
            for coabs in combs(CONST.coab_sort, x):
                dps_dict[coabs] = {}
                dps_dict[coabs]["180"] = MISC.async_fetch_text(
                    session, CONST.GET_URL(180, coabs)
                )
                dps_dict[coabs]["120"] = MISC.async_fetch_text(
                    session, CONST.GET_URL(120, coabs)
                )
                dps_dict[coabs]["60"] = MISC.async_fetch_text(
                    session, CONST.GET_URL(60, coabs)
                )
                parsed_dict[coabs] = {}
                for parse, dps_dict in dps_dict[coabs].items():
                    path_to_file = f"{path}_{coabs}_{parse}.csv"
                    parsed_dict[coabs][parse] = DPS.build_dps_dict(dps_dict[coabs])
                    save_parse_csvs(path_to_file, dps_dict)
        return parsed_dict

    @staticmethod
    def build_dps_dict(response_dict):
        """
        Given a csv of dps values for a specific combination of
        parse time and co-abilities, returns a parsed dict for all chars in csv.
        """
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

    @classmethod
    def build_ranking(cls, dps_db):
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
            for element in CONST.dragalia_elements:
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
        return cls(rankings_db)

    @staticmethod
    def gen_ranks(dps_db):
        rank_dict = {"none": DPS.build_ranking(dps_db)}
        for x in range(0, 4):
            for each in combs(MISC.coab_sort, x):
                rank_dict[each] = None
        return rank_dict
