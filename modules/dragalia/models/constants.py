import random

RAW_REPO_URL = "https://mushymato.github.io/dl-sim"
REPO_URL = "https://github.com/Mushymato/mushymato.github.io"

DATA_FILE = "data__.csv"

DPS_URL_60 = f"{RAW_REPO_URL}/60/{DATA_FILE}"
DPS_URL_120 = f"{RAW_REPO_URL}/120/{DATA_FILE}"
DPS_URL_180 = f"{RAW_REPO_URL}/180/{DATA_FILE}"

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

emoji = {"up_arrow": "⬆", "down_arrow": "⬇", "star": "⭐"}


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
