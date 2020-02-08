import random
import re
from itertools import combinations as combs

REPO_URL = "https://github.com/Mushymato/mushymato.github.io"
RAW_REPO_URL = (
    "https://raw.githubusercontent.com/Mushymato/mushymato.github.io/master/dl-sim"
)

d_emoji = {
    "flame": "<:flame_:641010593205190657>",
    "water": "<:water_:641010711073390594>",
    "wind": "<:wind_:641008886307880961>",
    "light": "<:light_:641008871317569597>",
    "shadow": "<:shadow_:641008878774910986>",
    "sword": "<:sword:641010676042825740>",
    "blade": "<:blade_:641010564784586763>",
    "dagger": "<:dagger_:641010584057544744>",
    "axe": "<:axe_:641010556089663498>",
    "lance": "<:lance_:641010603804065802>",
    "bow": "<:bow_:641010576767582209>",
    "wand": "<:wand_:641010751607406623>",
    "staff": "<:staff_:641010666148331551>",
    "3*": "<:3_star:641018606972567582>",
    "4*": "<:4_star:641018617147949076>",
    "5*": "<:5_star:641018624991166497>",
}

react_emoji = {"star": "⭐", "up_arrow": "⬆", "down_arrow": "⬇"}

react_coab_emoji = {
    "blade": d_emoji["blade"],
    "wand": d_emoji["wand"],
    "dagger": d_emoji["dagger"],
    "bow": d_emoji["bow"],
}

COAB_DICT = {
    "blade": "k",
    "wand": "r",
    "dagger": "d",
    "bow": "b",
    "none": "_",
    "k": "k",
    "r": "r",
    "d": "d",
    "b": "b",
}

COAB_DICT_REV = {
    "k": d_emoji["blade"],
    "r": d_emoji["wand"],
    "d": d_emoji["dagger"],
    "b": d_emoji["bow"],
    "_": "None",
}

DATA_FILE = "data__.csv"

DPS_URL_60 = f"{RAW_REPO_URL}/60/{DATA_FILE}"
DPS_URL_120 = f"{RAW_REPO_URL}/120/{DATA_FILE}"
DPS_URL_180 = f"{RAW_REPO_URL}/180/{DATA_FILE}"

coab_sort_key = ["k", "r", "d", "b"]

dragalia_elements = ["flame", "water", "wind", "light", "shadow"]
dragalia_elements_images = {
    "flame": "https://b1ueb1ues.github.io//dl-sim/pic/element/flame.png",
    "water": "https://b1ueb1ues.github.io//dl-sim/pic/element/water.png",
    "wind": "https://b1ueb1ues.github.io//dl-sim/pic/element/wind.png",
    "light": "https://b1ueb1ues.github.io//dl-sim/pic/element/light.png",
    "shadow": "https://b1ueb1ues.github.io//dl-sim/pic/element/shadow.png",
    "all": "https://icon-library.net/images/muscle-icon-png/muscle-icon-png-24.jpg",
}

elements_colors = {
    "flame": 0xE73031,
    "water": 0x1890DE,
    "wind": 0x00D771,
    "light": 0xFFBB10,
    "shadow": 0xA738DE,
    "all": random.randint(0, 0xFFFFFF),
}


alts = [
    "dragonyule",
    "student",
    "halloween",
    "valentine's",
    "summer",
    "wedding",
    "gala",
    "beautician",
    "hunter",
]


team_damage = "16,000"

parses = ["180", "120", "60"]

coab_combos = ["_"] + [
    "".join(coabs)
    for x in range(1, len(coab_sort_key) + 1)
    for coabs in combs(coab_sort_key, x)
]


def copy_parses():
    return {"180": {}, "120": {}, "60": {}}.copy()


def coab_sort(coabs):
    if "none" == coabs.lower():
        return "_"
    else:
        return "".join(
            sorted(coabs, key=lambda c_list: [coab_sort_key.index(c) for c in c_list])
        )


def GET_URL(parse="180", coabs=None):
    parse = str(parse)
    if not coabs:
        coabs = "_"
    if coabs != "_":
        if len(coabs) > 4:
            coabs = re.split("[^a-zA-Z]", coabs)
            coabs = [COAB_DICT[i] for i in coabs]

        coabs = coab_sort(coabs)
    return f"{RAW_REPO_URL}/{parse}/data_{coabs}.csv"


def parse_coabs(coab_input=None):
    if not coab_input:
        return "_"
    coab_input = coab_input.lower()
    if "none" in coab_input:
        return "_"
    else:
        try:
            coabs = coab_input.split(" ")
            if coab_input in d_emoji.keys():
                coabs_result = COAB_DICT[coab_input]
            elif len(coabs) > 1:
                coabs_result = "".join([COAB_DICT[coab] for coab in coabs])
            else:
                coabs_result = "".join([COAB_DICT[coab] for coab in coabs[0]])
            return coab_sort(coabs_result)
        except KeyError:
            return None


def parse_coab_disp(coabs):
    return " ".join([COAB_DICT_REV[c] for c in coabs])
