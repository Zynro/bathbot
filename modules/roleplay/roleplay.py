from discord.ext import commands
import asyncio
import random
import modules.roleplay.models.campaign as Campaign
import os
import json
from models import db as DB

pnp_file = "roleplay_info.json"
push_emoji = "<a:push:656219039814909955>"


def generate_rand_color():
    return random.randint(0, 0xFFFFFF)


def roll_dice(amount: int, dice: int = 6):
    return [random.randint(1, dice) for x in range(1, amount + 1)]


class Roleplay(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.module = self.bot.modules["roleplay"]
        self.initial_dir_creation()
        self.guild_info = self.load_guild_info()
        self.campaign = Campaign.pnp_list["mutant"]

    async def cog_check(self, ctx):
        return ctx.guild.id in self.module.access

    def guild_info_dump(self, guild, guild_info):
        with open(f"guilds/{guild}/{self.module.path}/lists/{pnp_file}", "w+") as file:
            json.dump(guild_info, file, indent=2)

    def load_guild_info(self):
        for guild in self.bot.module_access["roleplay"]:
            path = f"guilds/{guild}/{self.module.path}/lists/{pnp_file}"
            with open(path, "r") as file:
                return json.load(file)

    @commands.command(name="roll", aliases=["r"])
    async def roll(self, ctx, *, string):
        embed, roll_dict = self.campaign.dice(string, ctx.author)
        message = await ctx.send(ctx.author.mention, embed=embed)
        return

        def check_response(reaction, user):
            return (
                reaction.emoji == push_emoji
                and user != self.bot.user
                and message.id == reaction.message.id
            )

        while True:
            try:
                reaction, user = await self.bot.wait_for(
                    "reaction_add", timeout=300.0, check=check_response
                )
            except asyncio.TimeoutError:
                return
            else:

                def check_response(reaction, user):
                    return (
                        reaction.emoji == push_emoji
                        and user != self.bot.user
                        and message.id == reaction.message.id
                    )

                return


def setup(bot):
    bot.add_cog(Roleplay(bot))
