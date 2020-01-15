import aiohttp
from discord import Embed, Colour
from modules.ffxiv.models.parse import Parse
import modules.ffxiv.models.constants as CONST


def parse_json(json_resp, job=None):
    tier = {}
    for encounter in json_resp:
        if int(encounter["difficulty"]) == 100:
            continue
        fight_name = encounter["encounterName"]
        if fight_name not in tier.keys():
            tier[fight_name] = None
        if (
            not tier[fight_name]
            or tier[fight_name].percentile <= encounter["percentile"]
        ):
            tier[fight_name] = Parse(encounter)
    return tier


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
        self.API = "https://www.fflogs.com:443/v1"
        self.token = token
        if not session:
            self.session = aiohttp.ClientSession()
        else:
            self.session = session

    async def get_json(self, URL):
        async with self.session.get(URL) as response:
            return await response.json()

    async def embed(self, character, world, metric="rdps", method="rankings"):
        URL = (
            f"{self.API}/{method}/character/{character}/"
            f"{world}/NA?metric={metric}&timeframe=historical&api_key={self.token}"
        )
        results = parse_json(await self.get_json(URL))
        highest = int(max([x.percentile for x in results.values()]))
        color = get_parse_color(highest)
        embed = Embed(
            title=f"{character} @ {world}",
            description=f"Parses for {str.title(method)}, Historical",
            colour=Colour(color),
        )
        tier_list = []
        # max_name_length = max([len(x.fight) for x in results.values()])
        for encounter in results.values():
            # extra_spaces = max_name_length - len(encounter.fight)
            fight_name = str.title(encounter.fight)
            # fight = f"__{fight_name}__ " + (" " * extra_spaces)
            fight = f"__{fight_name}__ "
            job = f"{CONST.ff_job_emoji[encounter.job.lower()]}"
            parse = f"**[{encounter.percentile}%]**"
            dps = round(encounter.total, 2)
            rank = f"{encounter.rank}/{encounter.outof}"
            report_url = (
                f"https://www.fflogs.com/reports/{encounter.reportid}"
                f"#fight={encounter.fightid}"
            )
            tier_list.append(
                f"{job} {fight} {parse} 🔸 [{dps} rDPS]({report_url}) 🔸 Rank: {rank}"
            )
        tier_string = "\n".join(tier_list)
        embed.add_field(name="**Eden's Gate (Savage)**", value=tier_string)
        return embed
