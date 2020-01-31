import requests
import csv
import random
import json
import os
from discord import Embed, Colour
from modules.dragalia.models.parse import Parse
import modules.dragalia.models.constants as CONST
import lib.misc_methods as MISC
from itertools import combinations as combs

DPS_PATH = "modules/dragalia/ists/dps"

skip_msg = (
    "===========================================\n"
    "||Skipping DPS update, version matches...||\n"
    "==========================================="
)


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


def check_version():
    try:
        path = f"modules/dragalia/lists/dps_hash.json"
        with open(path, "r") as file:
            saved = json.load(file)
    except FileNotFoundError:
        return True
    current = MISC.get_master_hash(CONST.REPO_URL)
    if current != saved:
        print("[DRAGALIA]: ++DPS UPDATE REQUIRED++")
        return True
    else:
        return False


def load_csvs(path):
    dps_dict = {}
    for root, dirs, files in os.walk(DPS_PATH):
        for filename in files:
            with open(filename, "r") as f:
                name = filename.split("optimal_dps_")[1].split("_")
                parse = str(name[0])
                coabs = str(name[1])
                reader = csv.reader(f)
                dps_dict[parse] = {}
                dps_dict[parse][coabs] = list(reader)
    return dps_dict


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
        for parse_value in dps_dict.keys():
            for coabs in dps_dict[parse_value].keys():
                self.parse[parse_value][coabs] = Parse(
                    dps_dict[parse_value][coabs], coabs
                )
        self.image = adventurer.image
        self.alt = dps_dict["alt"]

        for parse_value, coabs_dict in self.parse.items():
            for coabs in coabs_dict.values():
                self.parse[parse_value][coabs].rank_element = str(
                    rank_db[parse_value][coabs][self.element].index(self.owner) + 1
                )
                self.parse[parse_value][coabs].rank_overall = str(
                    rank_db[parse_value][coabs]["all"].index(self.owner) + 1
                )

    def embed(self, parse_value="180", coabs="none"):
        if coabs == "none":
            coabs_disp = "None"
        else:
            coabs_disp = ", ".join([CONST.COAB_DICT_REV[c] for c in coabs])
        try:
            embed = Embed(
                title=f"__**{self.adventurer.name}**__",
                description=f"**Parse:** {parse_value} Seconds\n"
                f"**Co-Abilities:** {coabs_disp}\n"
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
            value=MISC.num_emoji_gen(self.parse[parse_value][coabs].dps),
            inline=True,
        )
        element_rank = add_number_suffix(self.parse[parse_value][coabs].rank_element)
        overall_rank = add_number_suffix(self.parse[parse_value][coabs].rank_overall)
        embed.add_field(
            name="__Ranks:__",
            value=f"**{self.element.title()}:** {element_rank} "
            f"\n**Overall:** {overall_rank}",
        )
        embed.add_field(name="__Dragon:__", value=self.dragon, inline=True)
        embed.add_field(name="__Wyrmprints:__", value=self.wyrmprints, inline=True)
        embed.add_field(
            name="__Damage Breakdown:__",
            value=self.parse[parse_value][coabs].to_dps_string(),
            inline=False,
        )
        if self.parse[parse_value][coabs].condition:
            embed.add_field(
                name="__Condition:__", value=self.parse[parse_value][coabs].condition
            )
        if self.parse[parse_value][coabs].comment:
            embed.add_field(
                name="__Comment:__", value=self.parse[parse_value][coabs].comment
            )
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
        if check_version() is True:
            dps_dict = {
                "180": {
                    "none": requests.get(CONST.GET_URL(180, "none")).text.split("\n")
                },
                "120": {
                    "none": requests.get(CONST.GET_URL(120, "none")).text.split("\n")
                },
                "60": {
                    "none": requests.get(CONST.GET_URL(60, "none")).text.split("\n")
                },
            }
            MISC.check_dir(path)
            for x in range(1, len(CONST.coab_sort) + 1):
                for coabs in combs(CONST.coab_sort, x):
                    coabs = "".join(coabs)
                    for parse in dps_dict.keys():
                        dps_dict[parse][coabs] = requests.get(
                            CONST.GET_URL(parse, coabs)
                        ).text.split("\n")
                        path_to_file = f"{path}/optimal_dps_{parse}_{coabs}.csv"
                        MISC.save_csv(path_to_file, dps_dict[parse][coabs])
            DPS.update_master_hash()
            return DPS.build_dps_dict(dps_dict)
        else:
            print(skip_msg)
            return DPS.build_dps_dict(load_csvs(path))

    @staticmethod
    async def async_pull_csvs(session, path):
        """
        Given a path, gets and saves all csvs for all co-ability combinations
        from source, returning a complete dictionary of all combinations and all parses.
        ++ASYNC version++
        """
        if check_version() is True:
            dps_dict = {
                "180": {
                    "none": MISC.async_fetch_text(
                        session, CONST.GET_URL(180, "none").split("\n")
                    )
                },
                "120": {
                    "none": MISC.async_fetch_text(
                        session, CONST.GET_URL(120, "none").split("\n")
                    )
                },
                "60": {
                    "none": MISC.async_fetch_text(
                        session, CONST.GET_URL(60, "none").split("\n")
                    )
                },
            }
            for x in range(1, len(CONST.coab_sort) + 1):
                for coabs in combs(CONST.coab_sort, x):
                    for parse in dps_dict.keys():
                        dps_dict[parse][coabs] = MISC.async_fetch_text(
                            session, CONST.GET_URL(parse, coabs)
                        ).split("\n")
                        path_to_file = f"{path}/optimal_dps_{parse}_{coabs}.csv"
                        MISC.save_csv(path_to_file, dps_dict[parse][coabs])
            DPS.update_master_hash()
            return DPS.build_dps_dict(dps_dict)
        else:
            print(skip_msg)
            return DPS.build_dps_dict(load_csvs(path))

    @staticmethod
    def build_dps_dict(response_dict):
        """
        Given a csv of dps values for a specific combination of
        parse time and co-abilities, returns a parsed dict for all chars in csv.
        """
        all_char_dps = {}
        damage = {}
        for parse_val in response_dict.keys():
            for coabs in response_dict[parse_val].keys():
                parse = response_dict[parse_val][coabs]
                del parse[0]
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
                        i_name = row[1].replace("_", "").lower().strip()
                    else:
                        i_name = row[1].lower().strip()
                        alt = False
                    if parse_val == "180":
                        amulets = row[6].split("][")
                        wyrmprints = amulets[0].split("+")
                        wyrmprints = remove_brackets(" + ".join(wyrmprints))
                        wyrmprints = wyrmprints.replace("_", " ")
                        dragon = remove_brackets(amulets[1])
                        all_char_dps[i_name] = {
                            "i_name": i_name,
                            "rarity": row[2],
                            "element": row[3],
                            "weapon": row[4],
                            "str": row[5],
                            "wyrmprints": wyrmprints,
                            "dragon": dragon,
                            "alt": alt,
                        }
                        all_char_dps[i_name][parse_val] = {}
                    all_char_dps[i_name][parse_val] = {}
                    damage = {}
                    damage_list = row[9:]
                    damage["dps"] = row[0]
                    damage["types"] = {}
                    for damage_type in damage_list:
                        damage_type = damage_type.split(":")
                        damage_name = damage_type[0].replace("_", " ").title()
                        damage["types"][damage_name] = damage_type[1]
                    all_char_dps[i_name][parse_val][coabs] = {}
                    all_char_dps[i_name][parse_val][coabs]["damage"] = damage
                    (all_char_dps[i_name][parse_val][coabs]["condition"]) = (
                        row[7].replace("<", "").replace(">", ""),
                    )
                    all_char_dps[i_name][parse_val][coabs]["comment"] = row[8]
        return all_char_dps

    @staticmethod
    def gen_ranks(dps_db):
        """
        Given a dps dict, builds a rankings of overall and each adventurers
        specific element.
        """
        rankings_db = {}
        for parse, coabs in dps_db.items():
            for coab in coabs:
                sorted_list = sorted(
                    [
                        (
                            dps_db[adven]["internal_name"],
                            int(dps_db[adven][parse][coabs]["damage"]["dps"]),
                        )
                        for adven in dps_db.keys()
                    ],
                    key=lambda x: x[1],
                    reverse=True,
                )
                rankings_db[parse][coab]["all"] = [i[0] for i in sorted_list]
                for element in CONST.dragalia_elements:
                    sorted_list = sorted(
                        [
                            (
                                dps_db[adven]["internal_name"],
                                int(dps_db[adven][parse][coabs]["damage"]["dps"]),
                            )
                            for adven in dps_db.keys()
                            if dps_db[adven]["element"] == element
                        ],
                        key=lambda x: x[1],
                        reverse=True,
                    )
                    rankings_db[parse][coab][element] = [i[0] for i in sorted_list]
        return rankings_db
