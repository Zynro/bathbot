from discord.ext import commands
import config

permission = "You do not have permission to use this command."
owner_list = config.owner_list


class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="list-servers", hidden=True)
    async def list_connected_servers(self, ctx):
        servers = ""
        for each in self.bot.guilds:
            servers = servers + each.name + "\n"
        await ctx.send(f"Here are all the servers I'm currently on:\n```{servers}```")


def setup(bot):
    bot.add_cog(Admin(bot))
