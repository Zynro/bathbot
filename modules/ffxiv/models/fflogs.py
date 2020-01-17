import aiohttp
from discord import Embed, Colour
from bs4 import BeautifulSoup
from modules.ffxiv.models.parse import Parse
import modules.ffxiv.models.constants as CONST
import lib.misc_methods as MISC

API = "https://www.fflogs.com:443/v1"
FFLOGS_URL = "https://www.fflogs.com"

difficulty_ids = {"Normal": 100, "Savage": 101}


def parse_json(json_resp, job=None):
    tier = {"Savage": {}, "Normal": {}}
    for encounter in json_resp:
        for diff in tier.keys():
            diff_id = difficulty_ids[diff]
            if int(encounter["difficulty"]) != diff_id:
                continue
            fight_name = encounter["encounterName"]
            if fight_name not in tier[diff].keys():
                tier[diff][fight_name] = None
            if (
                not tier[diff][fight_name]
                or tier[diff][fight_name].percentile <= encounter["percentile"]
            ):
                tier[diff][fight_name] = Parse(encounter)
    if not tier["Savage"]:
        diff = "Normal"
        return diff, tier[diff]
    else:
        diff = "Savage"
        return diff, tier[diff]


async def scrape_char(session, url):
    resp = await MISC.async_fetch_text(session, url)
    soup = BeautifulSoup(resp, "html.parser")
    info = {}
    info["thumbnail"] = soup.find(class_="character-name-link").select("img[src]")[0][
        "src"
    ]
    ilevel = soup.find("div", {"id": "gear-box-ilvl-text"}).get_text()
    ilevel = ilevel.split(" ")[-1]
    info["ilevel"] = ilevel
    return info


def get_parse_color(value: int):
    try:
        return CONST.parse_colors[value]
    except (KeyError, AttributeError):
        if value < 25:
            return CONST.parse_colors[0]
        elif 25 < value < 50:
            return CONST.parse_colors[25]
        elif 50 < value < 75:
            return CONST.parse_colors[50]
        elif 75 < value < 95:
            return CONST.parse_colors[75]
        elif 95 < value < 99:
            return CONST.parse_colors[95]


class FFLogs:
    def __init__(self, token, session=None):
        self.token = token
        if not session:
            self.session = aiohttp.ClientSession()
        else:
            self.session = session

    async def embed(self, character, world, metric, method="rankings", region="NA"):
        """
        Returns a discord embed object given a character, world, metric, method,
        and region.
        Everything but character, world, and metric have defaults.
        """
        if not metric:
            metric = "rdps"
        URL = (
            f"{API}/{method}/character/{character}/"
            f"{world}/{region}?metric={metric}"
            f"&timeframe=historical&api_key={self.token}"
        )
        difficulty, results = parse_json(await MISC.async_get_json(self.session, URL))
        highest = int(max([x.percentile for x in results.values()]))
        color = get_parse_color(highest)
        char_url = (
            f"{FFLOGS_URL}/character/{region}/{world}/{character.replace(' ', '%20')}"
        )
        fflogs_char = await scrape_char(self.session, char_url)
        thumbnail = fflogs_char["thumbnail"]
        ilevel = fflogs_char["ilevel"]
        embed = Embed(
            title=f"{str.title(character)} @ {str.title(world)}",
            description=f"Parses for {str.title(method)}, Historical\n\n"
            f"*Average i-Level:* ***{ilevel}***",
            url=char_url,
            colour=Colour(color),
        )
        embed.set_thumbnail(url=thumbnail)
        tier_list = []
        # max_name_length = max([len(x.fight) for x in results.values()])
        for encounter in results.values():
            # extra_spaces = ((max_name_length - len(encounter.fight)) * 3) - 5
            # if extra_spaces <= 0:
            #    extra_spaces = 0
            fight_name = str.title(encounter.fight)
            # fight = f"__{fight_name}__ " + (" " * extra_spaces)
            fight = f"__{fight_name}__"
            job = f"{CONST.ff_job_emoji[encounter.job.lower()]}"
            parse = f"**{MISC.num_emoji_gen(f'{encounter.percentile}%')}**"
            dps = round(encounter.total, 2)
            rank = f"{encounter.rank}/{encounter.outof}"
            report_url = (
                f"https://www.fflogs.com/reports/{encounter.reportid}"
                f"#fight={encounter.fightid}"
            )
            tier_list.append(
                f"{job} {fight} - {parse} 🔸 [{dps} rDPS]({report_url}) 🔸 Rank: {rank}"
            )
        tier_string = "\n".join(tier_list)
        embed.add_field(name=f"**Eden's Gate ({difficulty})**", value=tier_string)
        return embed
