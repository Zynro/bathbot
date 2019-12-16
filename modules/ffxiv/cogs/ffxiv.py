import discord
from discord.ext import commands
import random
import requests
import aiohttp
import json
import pprint

ITEM_SEARCH_PATH = "https://xivapi.com/search?string="


def randcolor():
    return random.randint(0, 0xFFFFFF)


class FFXIV(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.module = self.bot.modules["ffxiv"]
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
                world_dict.append(line[1].replace('"', "").lower())
        return world_dict

    async def find_item(self, item):
        item = item.lower().strip()
        results = []
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{ITEM_SEARCH_PATH}{item}") as resp:
                json_result = json.loads(await resp.text())
                for each in json_result["Results"]:
                    if each["UrlType"] == "Item":
                        results.append((each["Name"], each["ID"]))
        return results

    async def embed_results(self, results):
        embed = discord.Embed(
            title=f"FFXIV Universalis Marketboard", colour=discord.Colour(randcolor())
        )
        if len(results) == 0:
            embed.add_field(
                name="__Error:__", value=f"No results were found for the search term."
            )
            return embed
        elif len(results) > 1 < 20:
            results = "\n".join([x[0] for x in results])
            embed.add_field(name="**Multiple Results Found**:", value=results)
            embed.set_footer(text="Try searching again with a more specific term.")
            return embed
        else:
            embed.add_field(
                name="**Error:**",
                value=f"There are either too much results"
                " to display, or an unknown error has occured.",
            )
            return embed

    @commands.group(name="ffxiv")
    async def ffxiv(self, ctx):
        if not ctx.invoked_subcommand:
            return

    @ffxiv.command(name="universalis", aliases=["u", "univ"])
    async def universalis(self, ctx, world=None, *, item=None):
        if not world or not item:
            return await ctx.send("Both a world and an item must be provided.")
        if world.lower() not in self.worlds:
            return await ctx.send(f"World {world} was not found.")
        results = await self.find_item(item)
        return await ctx.send(embed=await self.embed_results(results))


def setup(bot):
    bot.add_cog(FFXIV(bot))
