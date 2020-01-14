import aiohttp
from discord import Embed, Colour
from modules.ffxiv.models.parse import Parse

parse_colors = {
    0: 0x666666,
    25: 0x1EFF00,
    50: 0x0070FF,
    75: 0xA335EE,
    95: 0xFF8000,
    99: 0xE268A8,
    100: 0xE5CC80,
}

job_icon_dict = {}


def parse_json(json_resp, job=None):
    tier = {}
    for encounter in json_resp:
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
        return parse_colors[value]
    except (KeyError, AttributeError):
        if value < 25:
            return parse_colors[0]
        elif 25 < value < 50:
            return parse_colors[25]
        elif 50 < value < 75:
            return parse_colors[50]
        elif 75 < value < 95:
            return parse_colors[75]
        elif 95 < value < 99:
            return parse_colors[95]


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
            f"{world}/NA?metric={metric}&api_key={self.token}"
        )
        results = parse_json(await self.get_json(URL))
        highest = int(max([x.percentile for x in results.values()]))
        color = get_parse_color(highest)
        embed = Embed(
            title=f"{character} - {world}",
            description=f"Parses for {str.title(method)}",
            colour=Colour(color),
        )
        tier_list = []
        for encounter in results.values():
            job = f"**__{encounter.job}__**"
            parse = f"**[{encounter.percentile}%]**"
            dps = round(encounter.total, 2)
            rank = f"{encounter.rank}/{encounter.outof}"
            report_url = (
                f"https://www.fflogs.com/reports/{encounter.reportid}"
                f"#fight={encounter.fightid}"
            )
            tier_list.append(
                f"{job}: {parse} 🔸 [{dps} rDPS]({report_url}) 🔸 Rank: {rank}"
            )
        tier_string = "\n".join(tier_list)
        embed.add_field(name="**Eden's Gate (Savage)**", value=tier_string)
        return embed
