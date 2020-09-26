from discord.ext import commands
from discord import Embed
import config

permission = "You do not have permission to use this command."
owner_list = config.owner_list


class Modules(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def check_cog(self, ctx):
        return ctx.author.id in owner_list or ctx.author.id == ctx.guild.owner.id

    @commands.group()
    async def module(self, ctx):
        if not ctx.invoked_subcommand:
            if ctx.author.id == config.owner:
                mod_list = ", ".join(
                    [i for i in self.bot.modules.keys() if "meme" not in i]
                )
                embed = Embed(
                    title="**Welcome to Bathbot's Modules**",
                    description=f"__The currently available modules are:__\n{mod_list}",
                )
                embed.add_field(
                    name="**__Current Commands__**:",
                    value="""
`&module check`
 ▫️ Checks accesses in current guild.
`&module add <module>`
 ▫️ Adds current guild to specified module.
`&module remove <module>`
 ▫️ Removes current guild from specified module.
`&module gcheck`
 ▫️ Returns a list of modules current guild has access to.""",
                )
                return await ctx.send(embed=embed)
            return

    @module.command(name="check")
    @commands.is_owner()
    async def check_access_to_module(self, ctx, module=None):
        """Checks what guilds have access to the given module."""
        if not module:
            return await ctx.send("A module name is required.")
        else:
            guild_list = []
            for guild in self.bot.modules[module].access:
                guild_list.append(self.bot.get_guild(guild).name)
            guild_list = "\n".join(guild_list)
            await ctx.send(
                f"**Guild Access to** `{self.bot.modules[module].name}`:"
                f"\n{guild_list}"
            )

    @module.command(name="add")
    async def add_access_to_module(self, ctx, module):
        """Allows this guild to access <module>."""
        if module not in self.bot.modules:
            return await ctx.send(f"Module '{module}' does not exist.")
        if ctx.guild.id in self.bot.modules[module].access:
            return await ctx.send(
                f"Guild '{ctx.guild.name}' already has access to the module '{module}.'"
            )
        self.bot.modules[module].add_access(ctx.guild.id)
        await ctx.send(
            f"Guild *{ctx.guild.name}* with ID '{ctx.guild.id}'"
            f" has been added to the access list for module '{module}'."
        )

    @module.command(name="remove", aliases=["rm"])
    async def remove_access_to_module(self, ctx, module):
        """Removes this guilds access to <module>."""
        if module not in self.bot.modules:
            return await ctx.send(f"Module '{module}' does not exist.")
        if ctx.guild.id not in self.bot.modules[module].access:
            return await ctx.send(
                f"Guild '{ctx.guild.name}' doesn't have "
                f"access to the module '{module}.'"
            )
        try:
            self.bot.modules[module].remove_access(ctx.guild.id)
        except Exception:
            return await ctx.send("Error.")
        await ctx.send(
            f"Guild *{ctx.guild.name}* with ID '{ctx.guild.id}' has"
            f" been removed from the access list for module '{module}'."
        )

    @module.command(name="gcheck")
    async def check_guilds_access(self, ctx):
        """Returns a list of modules the current guild has access to."""
        origin_guild = ctx.guild.id
        access_list = []
        for module in self.bot.modules:
            for guild in self.bot.modules[module].access:
                if origin_guild == guild:
                    access_list.append(module)
        access_list = "\n".join(access_list)
        await ctx.send(
            f"__This guild has access to the following modules:__\n{access_list}"
        )


def setup(bot):
    bot.add_cog(Modules(bot))
