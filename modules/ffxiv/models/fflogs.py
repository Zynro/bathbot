import aiohttp
from discord import Embed, Colour


class FFLogs:
    def __init__(self, token):
        self.API = "https://www.fflogs.com:443/v1"
        self.token = token
        self.session = aiohttp.ClientSession()

    async def get_json(self, URL):
        async with self.session.get(URL) as response:
            return await response.json()

    async def embed(self, character, world, metric="rdps", method="rankings"):
        URL = (
            f"{self.API}/{method}/character/{character}/"
            f"{world}/NA?metric={metric}&api_key={self.token}"
        )
        parse_json = self.get_json(URL)
        return
