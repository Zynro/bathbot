import discord
from discord.ext import commands
import random
from modules.roleplay.models import campaign
import os
import json


def generate_rand_color():
    return random.randint(0, 0xFFFFFF)


def roll_dice(amount: int, dice: int = 6):
    return [random.randint(1, dice) for x in range(1, amount + 1)]


class Dice(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.initial_dir_creation()
        self.guild_info = self.load_guilds_info()

    def initial_dir_creation(self):
        for guild in self.bot.module_access["roleplay"]:
            path_to_guild = f"guilds/{guild}/{self.bot.modules['roleplay'].path}"
            if not os.path.exists(path_to_guild):
                self.guild_info[guild] = {}
                self.guild_info[guild]["pnp"] = None
                os.mkdir(path_to_guild)
            if not os.path.exists(f"{path_to_guild}/lists"):
                os.mkdir(f"{path_to_guild}/lists")
            if not os.path.exists(f"{path_to_guild}/images"):
                os.mkdir(f"{path_to_guild}/images")
            self.guild_info_dump(guild)

    def guild_info_dump(self, guild):
        with open(
            f"guilds/{guild}/{self.bot.modules['roleplay'].path}/lists/", "w"
        ) as file:
            json.dump(file, self.guild_info[guild])

    def load_guilds_info(self):
        for guild in self.bot.module_access["roleplay"]:
            path_to_guild = f"guilds/{guild}/{self.bot.modules['roleplay'].path}/lists/"
            with open(f"{path_to_guild}/guild_info.json", "w") as file:
                return json.load(file)

    @commands.command(name="roll")
    async def roll(self, ctx, *, string):
        embed = discord.Embed(
            title=f"**`{string}`**", description=f" ", color=generate_rand_color()
        )
        rolls = campaign.roll_dice(string)
        if "d" in string:  # split by game mode later, temporary stopgap
            for index, each in enumerate(rolls):
                embed.add_field(
                    name=f"**__{rolls[index]}__**",
                    value=f"{', '.join([str(x) for x in each])}",
                    inline=False,
                )
                flat = sum([item for sublist in rolls for item in sublist])
                embed.add_field(
                    name="**__Totals:__**", value=f"Sum: {flat}", inline=False
                )
        else:
            for index, each in enumerate(rolls):
                embed.add_field(
                    name=f"**__{rolls[index]}d6__**",
                    value=f"{', '.join([str(x) for x in each])}",
                    inline=False,
                )
                flat = [item for sublist in rolls for item in sublist]
                successes = flat.count(6)
                failures = flat.count(1)
                embed.add_field(
                    name="**__Totals:__**",
                    value=f"Success: **{successes}**\nFailure: {failures}",
                    inline=False,
                )
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Dice(bot))
