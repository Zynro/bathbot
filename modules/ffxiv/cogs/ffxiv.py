from discord.ext import commands
import random
import requests
import json
from modules.ffxiv.models.xivapi import XIVAPI
from tokens.fflogs_credentials import public_key as FFLOGS_PUBLIC_KEY
import modules.ffxiv.models.constants as CONST


# from modules.ffxiv.models.parse import Parse
from modules.ffxiv.models.fflogs import FFLogs


def randcolor():
    return random.randint(0, 0xFFFFFF)


def get_worlds(path):
    temp_dict = requests.get(path).text.split("\n")
    temp_dict = temp_dict[3:]
    world_dict = []
    for line in temp_dict:
        line = line.split(",")
        if "true" in line[-1].lower():
            world_dict.append(line[1].replace('"', "").lower())
    return world_dict


class FFXIV(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.session = self.bot.session
        self.module = self.bot.modules["ffxiv"]
        self.worlds = get_worlds(CONST.world_path)
        self.fflogs = FFLogs(FFLOGS_PUBLIC_KEY, self.session)
        self.xivapi = XIVAPI(self.session)
        self.load_char_json()

    async def cog_check(self, ctx):
        return ctx.guild.id in self.bot.module_access["ffxiv"]

    def load_char_json(self):
        try:
            with open(f"{self.module.path}/lists/ff_chars.json", "r") as file:
                self.FF_CHARS = json.load(file)
        except FileNotFoundError:
            self.FF_CHARS = {}
            self.char_set_writeout()

    def char_set_writeout(self):
        with open(f"{self.module.path}/lists/ff_chars.json", "w") as file:
            json.dump(self.FF_CHARS, file, indent=2)

    @commands.group(name="ffxiv", aliases=["ff", "xiv"])
    async def ffxiv(self, ctx):
        if not ctx.invoked_subcommand:
            return

    @ffxiv.command(name="universalis", aliases=["u", "univ"])
    async def universalis(self, ctx, world=None, *, item=None):
        if not world or not item:
            return await ctx.send("Both a world and an item must be provided.")
        if world.lower() not in self.worlds:
            return await ctx.send(f"World {world} was not found.")
        results = await self.xiv_find_item(item)
        return await ctx.send(embed=await self.universalis_embed(results))

    @ffxiv.command(name="fflogs", aliases=["log", "logs", "fflog", "ffl"])
    async def fflogs(
        self, ctx, first_name=None, last_name=None, world=None, metric=None
    ):
        character = f"{first_name} {last_name}".strip()
        if not first_name and not last_name:
            return await ctx.send("A name must be provided.")
        elif world.lower() not in self.worlds:
            return await ctx.send(f"World {world} was not found.")
        results = await self.xivapi.xiv_get_chars(character)
        if len(results) == 1:
            character = results[0]
            embed = await self.fflogs.embed(character, world, metric)
        else:
            embed = await self.mult_result_embed(results)
        return await ctx.send(embed=embed)

    @ffxiv.group(name="me")
    async def me(self, ctx, metric=None):
        if not ctx.invoked_subcommand:
            return
        elif ctx.author.id in self.FF_CHARS.keys():
            player = self.FF_CHARS[ctx.author.id]
            embed = await self.fflogs.embed(player["name"], player["world"], metric)
            return await ctx.send(embed=embed)

    @me.command(name="set")
    async def set_self_character(
        self, ctx, first_name=None, last_name=None, world=None
    ):
        if not first_name or not last_name or not world:
            return await ctx.send("Both a name and world must be provided.")
        elif world.lower() not in self.worlds:
            return await ctx.send(f"World {world} was not found.")


def setup(bot):
    bot.add_cog(FFXIV(bot))
