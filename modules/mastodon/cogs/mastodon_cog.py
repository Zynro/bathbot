from discord.ext import commands
from discord import File
import config
from mastodon import Mastodon
import pickle

default_mastodon_url = 'https://mastodon.social'
MODULE_LISTS_DIR = 'modules/mastodon/lists/mastodon_list_pickle'

async def extract_id(toot_id):
    toot_id = str(toot_id)
    toot_id_list = toot_id.split('/')
    toot_id = toot_id_list[-1]
    toot_id_extracted = ""
    for char in toot_id:
        if char.isdigit():
            toot_id_extracted += char
        else:
            break
    toot_id_extracted = int(toot_id_extracted)
    return toot_id_extracted

class MastodonCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        try:
            self.mastodon_node_list = self.unpickle_node_list()
        except FileNotFoundError:
            with open(MODULE_LISTS_DIR, 'wb') as file:
                self.mastodon_node_list = [default_mastodon_url]
                pickle.dump(self.mastodon_node_list, file)

    async def cog_check(self, ctx):
        return ctx.guild.id in self.bot.module_access["mastodon"]

    def pickle_node_list(self, node_list):
        with open(MODULE_LISTS_DIR, 'wb') as file:
            pickle.dump(self.mastodon_node_list, file)

    def unpickle_node_list(self):
        with open (MODULE_LISTS_DIR, 'rb') as file:
            return pickle.load(file)

    async def create_mastodon_api_instance(self, url, create_type = 'check'):
        if create_type == 'try':
            return Mastodon(
                            client_id = 'tokens/bathbot_mastodon.secret',
                            api_base_url = url,
                            request_timeout = 5
                            )
        if url in self.mastodon_node_list:
            return Mastodon(
                            client_id = 'tokens/bathbot_mastodon.secret',
                            api_base_url = url,
                            request_timeout = 5
                            )
        else:
            return None

    async def get_toot(self, toot_id, mastodon_instance = None):
        if mastodon_instance == None:
            return None
        try:
            if "http" in toot_id:
                toot_id = extract_id(toot_id)
        except TypeError:
            pass
        return mastodon_instance.status(toot_id)

    async def get_media_urls(self, toot_id, mastodon_instance):
        try:
            media_list = []
            for media in (await self.get_toot(toot_id, mastodon_instance))['media_attachments']:
                if media['type'] == "image":
                    media_list.append(media['url'])
            if len(media_list) == 1:
                return None
            else:
                del media_list[0]
                return "\n".join(media_list)
        except AttributeError:
            return None
        except IndexError:
            return None

    @commands.Cog.listener()
    async def on_message (self, message):
        if message.author == self.bot.user:
            return
        if message.guild.id not in self.bot.module_access["mastodon"] or "http" not in message.content:
            return
        http_split = message.content.split(" ")
        for each in http_split:
            if "http" in each:
                toot_url = each
                break
        split_list = toot_url.split('/')
        node_url = None
        for each in self.mastodon_node_list:
            if split_list[2] in each:
                node_url = each
                break
        if not node_url:
            return
        else:
            mastodon_instance = await self.create_mastodon_api_instance(node_url)
            toot_id = await extract_id(toot_url)
            if not toot_id:
                return
            media_string = await self.get_media_urls(toot_id, mastodon_instance)
            if not media_string:
                return
            await message.channel.send(media_string)

    @commands.group()
    async def mastodon(self, ctx):
        if not ctx.invoked_subcommand:
            if ctx.author.id == config.cowner:
                node_list = ", ".join(self.mastodon_node_list)
                return await ctx.send(f"Current nodes on Mastodon list:\n{node_list}")

    @mastodon.command(name = 'add')
    @commands.is_owner()
    async def add_node_to_mastodon_node_list(self, ctx, node_url = None):
        if not node_url or "http" not in node_url:
            return await ctx.send("Must have a proper node url.")
        try:
            mastodon = await self.create_mastodon_api_instance(node_url, create_type = 'try')
            mastodon_instance = mastodon.instance()
        except Exception as e:
            return await ctx.send(f"An error occured. Maybe the URL is not a Mastodon instance?\n{e}")
        if node_url not in self.mastodon_node_list:
            self.mastodon_node_list.append(node_url)
            self.pickle_node_list(self.mastodon_node_list)
            return await ctx.send("Instance successfully added to Mastodon Node List!")
        else:
            return await ctx.send("Node already exists in list.")

    @mastodon.command(name = 'remove')
    @commands.is_owner()
    async def remove_node_from_mastodon_node_list(self, ctx, node_url = None):
        if not node_url:
            return await ctx.send("Must specify Node URL to remove.")
        found_url = None
        for node in self.mastodon_node_list:
            if node_url in node:
                found_url = node
                break
        if not found_url:
            return await ctx.send("URL not found in node list.")
        else:
            self.mastodon_node_list.remove(found_url)
            self.pickle_node_list(self.mastodon_node_list)
            return await ctx.send(f'"{found_url}" has been removed from the Mastodon Node List.')

    @mastodon.command(name = 'list')
    async def return_mastodon_node_list(self, ctx):
        node_list = []
        for each in self.mastodon_node_list:
            each = f"<{each}>"
            node_list.append(each)
        node_list = '\n'.join(node_list)
        return await ctx.send(f"Current Mastodon Node List:\n{node_list}")

def setup(bot):
    bot.add_cog(MastodonCog(bot))