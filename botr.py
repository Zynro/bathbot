import discord
from discord.ext import commands
import config
import bot_token
import json
import os
import traceback
import sys
import aiohttp
from models.module import Module


def ext_checks(x):
    return (".py" in x) and ("except" not in x)


ext_dict = {}
bot_directory_modules = [name for name in os.listdir("./modules")]
for module in bot_directory_modules:
    ext_dict[module] = [
        f"modules.{module}.cogs.{x.replace('.py','')}"
        for x in os.listdir(f"./modules/{module}/cogs")
        if ext_checks(x)
    ]
ext_dict["base"] = [
    f'cogs.{x.replace(".py", "")}' for x in os.listdir("./cogs") if ".py" in x
]

# temporary stopgap until more refined solution for ordering cog loads
ext_dict["onmyoji"] = [
    "modules.onmyoji.cogs.guildcmd",
    "modules.onmyoji.cogs.shikigami",
    "modules.onmyoji.cogs.shard",
]


extensions = [item for sublist in ext_dict.values() for item in sublist]


def get_prefix(bot, message):
    prefixes = ["["]
    return commands.when_mentioned_or(*prefixes)(bot, message)


bot = commands.Bot(command_prefix=get_prefix, description="Bathbot")

with open(f"tokens/module_access.json") as file:
    bot.module_access = json.loads(file.read())
    bot.module_access["bathmemes"] = config.memes_access

bot.cog_list = extensions + ["cogs.dev"]

bot_directory_modules = [name for name in os.listdir("./modules")]
bot_access_modules = [name for name in bot.module_access.keys()]
diff_list = list(set(bot_directory_modules).difference(bot_access_modules))
if len(diff_list) > 0:
    writeout = True
    for each in diff_list:
        bot.module_access[each] = []
else:
    writeout = False

bot.modules = {}
for extension in ext_dict.keys():
    if extension == "base":
        continue
    bot.modules[extension] = Module(
        extension, extension, ext_dict[extension], bot.module_access[extension]
    )
bot.modules["bathmemes"] = Module(
    "bathmemes", config.memes_module_path, config.memes_extensions, config.memes_access
)

if writeout is True:
    module_access_dict = {}
    for module in bot.modules.values():
        module_access_dict[module.name] = []
        for guild_id in module.access:
            module_access_dict[module.name].append(guild_id)
    path_to_file = f"tokens/module_access.json"
    with open(path_to_file, "w+") as file:
        json.dump(module_access_dict, file, indent=4)


@bot.event
async def on_ready():
    print("Logged in as")
    print(bot.user.name)
    print(bot.user.id)
    print("------")
    # bot.remove_command('help')
    await bot.change_presence(
        activity=discord.Game(
            name="Shower With Your "
            "Dad Simulator 2015: Do You "
            "Still Shower With Your Dad"
        )
    )
    if __name__ == "__main__":

        # Creates all module base folders
        # Uncessary, remove later
        module_base_folder_list = ["cogs", "images", "lists", "models"]
        for module in bot.modules.keys():
            if not os.path.exists(f"modules/{module}"):
                os.mkdir(f"modules/{module}")
            for folder in module_base_folder_list:
                if not os.path.exists(f"modules/{module}/{folder}"):
                    os.mkdir(f"modules/{module}/{folder}")

        # Create all necessary guild folders
        required_dir_list = ["images", "lists"]
        if not os.path.exists(f"guilds"):
            os.mkdir(f"guilds")
        for guild in bot.guilds:
            if not os.path.exists(f"guilds/{guild.id}"):
                os.mkdir(f"guilds/{guild.id}")
            for module in bot.modules:
                module = bot.modules[module]
                if module.name == "bathmemes":
                    continue
                path = f"guilds/{guild.id}/{module.path}"
                if not os.path.exists(path):
                    os.mkdir(path)
                for path_dir in required_dir_list:
                    path = f"{path}/{path_dir}"
                    if not os.path.exists(path):
                        os.mkdir(path)

        # Create global aiohttp ClientSession
        bot.session = aiohttp.ClientSession()

        # Load all extensions
        for extension in extensions:
            if "dev" in extension:
                continue
            try:
                print(f"Loading {extension}...")
                bot.load_extension(extension)
                print("Success!")
            except Exception:
                print(f"Failed to load extension {extension}.", file=sys.stderr)
                traceback.print_exc()

    print("------")
    print(f"Bathbot is fully ready!")
    if not discord.opus.is_loaded():
        discord.opus.load_opus("libopus.so")
        print("Opus has been loaded!")


bot.last_loaded_cog = None


@bot.check
async def guild_only_commands(ctx):
    return ctx.guild is not None


async def permission_check(ctx):
    return ctx.author.id in config.owner_list


async def cog_locator(arg):
    found_cog = None
    for cog in bot.cog_list:
        cog_name = cog.split(".")[-1]
        if arg in cog_name:
            found_cog = cog
    return found_cog


# Hidden means it won't show up on the default help.
@bot.command(name="load", hidden=True)
@commands.check(permission_check)
async def load_cog(ctx, *, arg=None):
    """Command which Loads a cog."""
    if not arg and bot.last_loaded_cog:
        try:
            bot.load_extension(bot.last_loaded_cog)
            return
        except Exception as e:
            await ctx.send(f"**ERROR:** {type(e).__name__} - {e}")
            traceback.print_exc()
            return
        else:
            await ctx.send("**Success:** " + bot.last_loaded_cog + " has been loaded!")
    try:
        if "." in arg:
            bot.load_extension(arg)
        else:
            cog = await cog_locator(arg)
            if not cog:
                return await ctx.send(f'Cog "{arg}" does not exist.')
            bot.load_extension(cog)
            bot.last_loaded_cog = cog
    except Exception as e:
        await ctx.send(f"**ERROR:** {type(e).__name__} - {e}")
        traceback.print_exc()
    else:
        await ctx.send("**Success: ** " + cog + " has been loaded!")


@bot.command(name="unload", hidden=True)
@commands.check(permission_check)
async def unload_cog(ctx, *, arg: str):
    """Command which Unloads a cog."""
    try:
        if "." in arg:
            bot.unload_extension(arg)
        else:
            cog = await cog_locator(arg)
            if not cog:
                return await ctx.send(f'Cog "{arg}" does not exist.')
            bot.unload_extension(cog)
    except Exception as e:
        await ctx.send(f"**ERROR:** {type(e).__name__} - {e}")
    else:
        await ctx.send("**Success:** " + cog + " has been unloaded!")


@bot.command(name="reload", hidden=True)
@commands.check(permission_check)
async def reload_cog(ctx, *, arg=None):
    """Command which Reloads a Module.
    Remember to use dot path. e.g: cogs.owner"""
    if not arg and bot.last_loaded_cog:
        try:
            bot.unload_extension(bot.last_loaded_cog)
            bot.load_extension(bot.last_loaded_cog)
        except Exception as e:
            await ctx.send(f"**ERROR:** {type(e).__name__} - {e}")
            traceback.print_exc()
            return
        else:
            await ctx.send(
                "**Success:** " + bot.last_loaded_cog + " has been reloaded!"
            )
            return
    try:
        if "." in arg:
            bot.unload_extension(arg)
            bot.load_extension(arg)
        else:
            cog = await cog_locator(arg)
            if not cog:
                return await ctx.send(f'Cog "{arg}" does not exist.')
            bot.unload_extension(cog)
            bot.load_extension(cog)
            bot.last_loaded_cog = cog
    except Exception as e:
        await ctx.send(f"**Error:** {type(e).__name__} - {e}")
        traceback.print_exc()
    else:
        await ctx.send("**Success:** " + cog + " has been reloaded!")


bot.help_command = None


@bot.command(name="help")
async def help_(ctx):
    return await ctx.send(
        "Help is currently under complete re-construction for all modules."
    )


@bot.command(name="kill", hidden=True)
@commands.check(permission_check)
async def kill_bot(ctx):
    """Kills the bot. Only useable by Zynro."""
    await ctx.send(
        "Well, it's time to take a bath. See you soon! BathBot is now exiting."
    )
    sys.exit()


bot.run(bot_token.TOKEN)
