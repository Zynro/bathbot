import discord
from discord.ext import commands
import random
import requests
import aiohttp
import json
import pprint
from modules.ffxiv.models.parse import Parse
from tokens.fflogs_tokens import public_token as FFLOGS_TOKEN

XIV_API = "https://xivapi.com/search?string="
FFLOGS_API = "https://www.fflogs.com:443/v1"


def randcolor():
    return random.randint(0, 0xFFFFFF)


def generate_fflogs_link(self, character, world, method="rankings"):
    return (
        f"{FFLOGS_API}/{method}/character/{character}/{world}/NA?api_key={FFLOGS_TOKEN}"
    )


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
            async with session.get(f"{XIV_API}{item}") as resp:
                json_result = json.loads(await resp.text())
                for each in json_result["Results"]:
                    if each["UrlType"] == "Item":
                        results.append((each["Name"], each["ID"]))
        return results

    async def universalis_embed(self, results):
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
        return await ctx.send(embed=await self.universalis_embed(results))

    @ffxiv.command(name="fflogs", aliases=["log", "logs", "fflog", "ffl"])
    async def fflogs(
        self, ctx, first_name=None, last_name=None, world=None, method=None
    ):
        character = f"{first_name} {last_name}"
        if not first_name or not last_name or not world:
            return await ctx.send(
                "A name and a world must be provided to search FFlogs."
            )
        if world.lower() not in self.worlds:
            return await ctx.send(f"World {world} was not found.")

        return


def setup(bot):
    bot.add_cog(FFXIV(bot))
