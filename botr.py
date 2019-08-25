import discord
from discord.ext import commands
import asyncio
import requests
import config
import bot_token
import json
import os

class Module:
    def __init__(self, name, path=None, cog_list=None, guild_access=None):
        self.name = name
        self.path = path
        self.cog_list = cog_list
        self.access = guild_access

base_extensions = [
                    'cogs.admin',
                    'cogs.voicecmd',
                    'cogs.basic',
                    'cogs.modules'
                    ]

onmyoji_extensions = [
                    'modules.onmyoji.cogs.guildcmd',
                    'modules.onmyoji.cogs.shikigami',
                    'modules.onmyoji.cogs.shard'                    
                    ]

twitter_extensions = [
                    'modules.twitter.cogs.twitter'                    
                    ]

dragalia_extensions = [
                    'modules.dragalia.cogs.wyrmprints'                    
                    ]

initial_extensions = base_extensions + onmyoji_extensions + twitter_extensions + dragalia_extensions
extensions = initial_extensions + config.meme_extensions

def get_prefix(bot, message):
    prefixes = ['&']
    return commands.when_mentioned_or(*prefixes)(bot, message)

bot = commands.Bot(command_prefix=get_prefix, description='I am Bathbot. I meme.')

with open(f'tokens/module_access.json') as file:
    bot.module_access = json.loads(file.read())

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

bot.modules['bathmemes'] = Module('bathmemes', 
                        config.memes_module_path, 
                        config.meme_extensions, 
                        bot.module_access['bathmemes'])
bot.modules['onmyoji'] = Module('onmyoji', 
                        config.onmyoji_module_path, 
                        onmyoji_extensions, 
                        bot.module_access['onmyoji'])
bot.modules['twitter'] = Module('twitter', 
                        config.twitter_module_path, 
                        twitter_extensions, 
                        bot.module_access['twitter'])
bot.modules['dragalia'] = Module('dragalia', 
                        config.dragalia_module_path, 
                        dragalia_extensions, 
                        bot.module_access['dragalia'])
if writeout == True:
    module_access_dict = {}
    for module in bot.modules.values():
        module_access_dict[module.name] = []
        for guild_id in module.access:
            module_access_dict[module.name].append(guild_id)
    path_to_file = f'tokens/module_access.json'
    with open(path_to_file, 'w+') as file:
        json.dump(module_access_dict, file, indent = 4)

@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')
    #bot.remove_command('help')
    await bot.change_presence(activity=discord.Game(name='Shower With Your Dad Simulator 2015: Do You Still Shower With Your Dad'))
    if __name__ == '__main__':

        #Creates all module base folders
        module_base_folder_list = ['cogs', 'images', 'lists']
        if not os.path.exists("modules"):
            os.mmkdir("modules")
        for module in bot.modules.keys():
            if not os.path.exists(f"modules/{module}"):
                os.mkdir(f"modules/{module}")
            for folder in module_base_folder_list:
                if not os.path.exists(f"modules/{module}/{folder}"):
                    os.mkdir(f"modules/{module}/{folder}")

        #Create all necessary guild folders
        required_dir_list = ['images', 'lists', 'modules']
        if not os.path.exists(f"guilds"):
                os.mkdir(f"guilds")
        for guild in bot.guilds:
            if not os.path.exists(f"guilds/{guild.id}"):
                os.mkdir(f"guilds/{guild.id}")
            for folder in required_dir_list:
                if not os.path.exists(f"guilds/{guild.id}/{folder}"):
                    os.mkdir(f"guilds/{guild.id}/{folder}")
            for module in bot.modules:
                module = bot.modules[module]
                if not os.path.exists(f"guilds/{guild.id}/{module.path}"):
                    os.mkdir(f"guilds/{guild.id}/{module.path}")

        #Load all extensions
        for extension in extensions:
            try:
                bot.load_extension(extension)
                print(extension +' has been loaded!')
            except Exception as e:
                print(f'Failed to load extension {extension}.', file=sys.stderr)
                traceback.print_exc()
    print('------')
    print(f'Bathbot is fully ready!')
    if not discord.opus.is_loaded():
            discord.opus.load_opus('libopus.so')
            print('Opus has been loaded!')


@bot.check
async def guild_only_commands(ctx):
    return ctx.guild != None

'''@bot.command(name='load',hidden=True)
async def cog_load(bot, ctx, *, cog: str):
    """Command which Loads a Module.
    Remember to use dot path. e.g: cogs.owner"""
    try:
        bot.load_extension('cogs.'+cog)
    except Exception as e:
        await ctx.send(f'**ERROR:** {type(e).__name__} - {e}')
    else:
        await ctx.send('**Success: **cogs.'+cog+' has been loaded!')

@bot.command(name='unload',hidden=True)
async def cog_unload(ctx, *, cog: str):
    """Command which Unloads a Module.
    Remember to use dot path. e.g: cogs.owner"""
    if ctx.message.author.id != owner:
        await ctx.send(config.permission)
        return
    else:
        try:
            bot.unload_extension('cogs.'+cog)
        except Exception as e:
            await ctx.send(f'**ERROR:** {type(e).__name__} - {e}')
        else:
            await ctx.send('**Success:** cogs.'+cog+' has been unloaded!')

@bot.command(name='reload', hidden=True)
async def cog_reload(ctx, *, cog: str):
    """Command which Reloads a Module.
    Remember to use dot path. e.g: cogs.owner"""
    try:
        bot.reload_extension('cogs.'+cog)
    except Exception as e:
        await ctx.send(f'**Error:** {type(e).__name__} - {e}')
    else:
        await ctx.send('**Success:** cogs.'+cog+' has been reloaded!')'''


bot.run(bot_token.TOKEN)
