from discord.ext import commands
import sys
import config
import os

class Test(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

def setup(bot):
    bot.add_cog(Test(bot))