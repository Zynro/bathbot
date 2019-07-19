from discord.ext import commands
import sys
import config
import traceback

owner_list = config.owner_list

class Basic(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    commands.command(name='purge', aliases=['prune','wipe','delete'])
    async def prune
    

def setup(bot):
    bot.add_cog(Basic(bot))
