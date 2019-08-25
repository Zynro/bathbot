from discord.ext import commands
import sys
import config
import traceback
import json

permission = 'You do not have permission to use this command.'
owner_list = config.owner_list

class Modules(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    async def check_cog(self, ctx):
        return ctx.author.id in owner_list    

    def module_access_writeout(self):
        module_access_dict = {}
        for module in self.bot.modules.values():
            module_access_dict[module.name] = []
            for guild_id in module.access:
                module_access_dict[module.name].append(guild_id)
        path_to_file = f'tokens/module_access.json'
        with open(path_to_file, 'w+') as file:
            json.dump(module_access_dict, file, indent = 4)
        return

    @commands.group()
    async def module(self, ctx):
        if not ctx.invoked_subcommand:
            if ctx.author.id == config.owner:
                return await ctx.send("""Current Commands:
```&module check - Checks accesses in current guild.
&module add <module>
    Adds current guild to specified module.
&module remove <module>
    Removes current guild from specified module.
&module gcheck
    Returns a list of modules current guild has access to.```""")
            return

    @module.command(name='check')
    async def check_access_to_module(self, ctx, module=None):
        """Checks what modules the current guild has access to."""
        if not module:
            return await ctx.send("A module name is required.")
        else:
            guild_list = []
            for guild in self.bot.modules[module].access:
                guild_list.append(self.bot.get_guild(guild).name)
            guild_list = "\n".join(guild_list)
            await ctx.send(f"""__Current list of guilds with access to the module '{self.bot.modules[module].name}'__:
{guild_list}""")

    @module.command(name='add')
    async def add_access_to_module(self, ctx, module):
        """Allows thisg guild to access <module>."""
        if module not in self.bot.modules:
            return await ctx.send(f"Module '{module}' does not exist.")
        if ctx.guild.id in self.bot.modules[module].access:
            return await ctx.send(f"Guild '{ctx.guild.name}' already has access to the module '{module}.'")
        self.bot.modules[module].access.append(ctx.guild.id)
        self.module_access_writeout()
        await ctx.send(f"Guild *{ctx.guild.name}* with ID '{ctx.guild.id}' has been added to the access list for module '{module}'.")

    @module.command(name='remove', aliases=['rm'])
    async def remove_access_to_module(self, ctx, module):
        """Removes this guilds access to <module>."""
        if module not in self.bot.modules:
            return await ctx.send(f"Module '{module}' does not exist.")
        if ctx.guild.id not in self.bot.modules[module].access:
            return await ctx.send(f"Guild '{ctx.guild.name}' doesn't have access to the module '{module}.'")
        try:
            self.bot.modules[module].access.remove(ctx.guild.id)
        except KeyError:
            return await ctx.send("Although the guild has access, I could not remove it from the dict.")
        self.module_access_writeout()
        await ctx.send(f"Guild *{ctx.guild.name}* with ID '{ctx.guild.id}' has been removed from the access list for module '{module}'.")

    @module.command(name='gcheck')
    async def check_guilds_acces(self, ctx):
        """Returns a list of modules the current guild has access to."""
        origin_guild = ctx.guild.id
        access_list = []
        for module in self.bot.modules:
            for guild in self.bot.modules[module].access:
                if origin_guild == guild:
                    access_list.append(module)
        access_list = "\n".join(access_list)
        await ctx.send(f"__This guild has access to the following modules:__\n{access_list}")


def setup(bot):
    bot.add_cog(Modules(bot))