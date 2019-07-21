from discord.ext import commands
import sys
import config
import traceback

owner_list = config.owner_list

class Basic(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name='purge', aliases=['prune','wipe','delete'])
    async def prune(self, ctx, amount: int = None):
        """
        Deletes the previous x amount of messages, including the prune command line.

        Parameters:
        amount (int): The amount of messages to prune
        """
        try:
            if not amount:
                return await ctx.send("You must enter an amount of messages to be deleted.")
            try:
                await ctx.channel.purge(limit=amount+1)
            except Exception as e:
                await ctx.send(f"I failed to delete the messages.\n{e}")
        except TypeError:
            await ctx.send("Must be a whole number of an amount.")
        return
    

def setup(bot):
    bot.add_cog(Basic(bot))
