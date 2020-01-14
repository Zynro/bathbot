import aiohttp
from discord import Embed, Colour


class FFLogs:
    def __init__(self, token, session=None):
        self.API = "https://www.fflogs.com:443/v1"
        self.token = token
        if not session:
            self.session = aiohttp.ClientSession()

    async def get_json(self, URL):
        async with self.session.get(URL) as response:
            return await response.json()

    async def embed(self, character, world, metric="rdps", method="rankings"):
        URL = (
            f"{self.API}/{method}/character/{character}/"
            f"{world}/NA?metric={metric}&api_key={self.token}"
        )
        embed = parse_json = await self.get_json(URL)
        return embed
