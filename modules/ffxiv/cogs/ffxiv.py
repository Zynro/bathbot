from discord.ext import commands
import requests
import aiohttp
import json
import pprint

ITEM_SEARCH_PATH = "https://xivapi.com/search?string="


class FFXIV(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        world_path = (
            "https://raw.githubusercontent.com/xivapi/ffxiv-datamining/master/"
            "csv/World.csv"
        )
        self.worlds = self.get_worlds(world_path)

    def get_worlds(self, path):
        temp_dict = requests.get(path).text.split("\n")
        temp_dict = temp_dict[3:]
        world_dict = []
        for line in temp_dict:
            line = line.split(",")
            if "true" in line[-1].lower():
                world_dict.append(line[1].replace('"', ""))
        return world_dict

    async def find_item(self, item):
        item = item.lower().strip()
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{ITEM_SEARCH_PATH}{item}") as resp:
                result = json.loads(await resp.text())
                pp = pprint.PrettyPrinter(indent=2)
                pp.pprint(result)
        return result

    @commands.group(name="ffxiv")
    async def ffxiv(self, ctx):
        if not ctx.invoked_subcommand:
            return

    @ffxiv.command(name="universalis", aliases=["u", "univ"])
    async def universalis(self, ctx, world=None, *, item=None):
        if not world or not item:
            return await ctx.send("Both a world and an item must be provided.")
        if world not in self.worlds:
            return await ctx.send(f"World {world} was not found.")
        print(await self.find_item("Water"))


def setup(bot):
    bot.add_cog(FFXIV(bot))
