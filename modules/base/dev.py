from discord.ext import commands
import os
import json

class Dev(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='arg')
    async def arg_return(self, ctx, *, arg):
        try:
            await ctx.send(eval(arg))
        except Exception as e:
            await ctx.send(e)

    @commands.command(name='arge')
    async def arg_return_exec(self, ctx, *, arg):
        args = arg
        exec(args)

def setup(bot):
    bot.add_cog(Dev(bot))