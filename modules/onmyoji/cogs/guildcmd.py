from discord.ext import commands
from discord import File
import json
import os.path
import io
import config
import requests
import shutil

permission = 'You do not have permission to use this command.'
owner_list = config.owner_list
editor_list = config.editor_list

def get_ext(path):
    return os.path.splitext(path)[1].strip().lower()

def get_user_id(user):
    return int("".join([x for x in user if x.isdigit()]))

class GuildCmd(commands.Cog):
    def __init__(self, bot):
        try:
            os.makedirs("./images/guild")
        except FileExistsError:
            pass
        self.guild_json_load()
        self.bot = bot

    async def cog_check(self, ctx):
        return ctx.guild.id in self.bot.module_access["onmyoji"]

    async def has_permission(ctx):
        return ctx.author.id in owner_list or ctx.author.id in editor_list

    def guild_leader_check(ctx):
        return ctx.guild.owner.id == ctx.author.id or ctx.author.id in owner_list

    def guild_json_load(self):
        try:
            with open(f'{config.list_path}/guild_info.json', 'r') as guild_file:
                self.guild_info = json.loads(guild_file.read())
        except FileNotFoundError:
            with open(f'{config.list_path}/guild_info.json', 'w') as guild_file:
                self.guild_info = {}
                self.guild_info["schedule"] = {}
                self.guild_info["schedule"]["message"] = None
                self.guild_info["schedule"]["file_path"] = None
                json.dump(self.guild_info, guild_file, indent=4)
                print('New Guild Info Json file generated!')

    def guild_json_writeout(self):
        with open(f'{config.list_path}/guild_info.json', 'w+') as guild_file:
            json.dump(self.guild_info, guild_file, indent=4)
            return

    @commands.group()
    async def schedule(self, ctx):
        self.guild_json_load()
        if not ctx.invoked_subcommand:
            try:
                message = self.guild_info["schedule"]["message"]
            except KeyError:
                message = None
            try:
                image = self.guild_info["schedule"]["file_path"]
            except KeyError:
                image = None
            if not message and not image:
                return await ctx.send("No schedule is set.\nTo set an image, use `&schedule image <link to image>`.\nTo set an accompanying message, use `&schedule message <message>`\nYou can set both or just one.")
            if not message:
                return await ctx.send(file = File(self.guild_info["schedule"]["file_path"]))
            if not image:
                return await ctx.send(self.guild_info["schedule"]["message"])
            return await ctx.send(self.guild_info["schedule"]["message"], file = File(self.guild_info["schedule"]["file_path"]))

    @schedule.command(name = "image")
    @commands.check(guild_leader_check)
    async def schedule_set_image(self, ctx, *, arg=None):
        guild_img_path = f"./images/guild"
        try:
            schedule_image_file = self.guild_info["schedule"]["file_path"]
        except KeyError:
            for file in os.listdir(guild_img_path):
                if "schedule" in file:
                    try:
                        guild_img_path = self.guild_info["schedule"]["file_path"] = f"{guild_img_path}/{file}"
                    except KeyError:
                        self.guild_info["schedule"] = {} 
                        guild_img_path = self.guild_info["schedule"]["file_path"] = f"{guild_img_path}/{file}"
                        self.guild_json_writeout()
                    break
        if not arg:
            try:
                await ctx.send("The schedule image is currently:", file = File(schedule_image_file))
                return
            except:
                await ctx.send("There is no current schedule image. Re-use the command with a link to the image to set one. Can be any format.\ne.g. `&schedule image https://link.com/to_image.jpeg`")
                return
        elif "clear" in arg:
            self.guild_info["schedule"]["file_path"] = None
            await ctx.send("Schedule image cleared.")
        else:
            ext = get_ext(arg)
            try:
                r = requests.get(arg, stream=True)
                if r.status_code == 200:
                    print(f"{guild_img_path}/schedule{ext}")
                    with open(f"{guild_img_path}/schedule{ext}", 'wb') as f:
                        r.raw.decode_content = True
                        shutil.copyfileobj(r.raw, f)
                        self.guild_info["schedule"]["file_path"] = f"{guild_img_path}/schedule{ext}"
                        await ctx.send("The schedule image is now:", file = File(self.guild_info["schedule"]["file_path"]))
            except Exception as e:
                await ctx.send(f"An error occured: {e}")
        self.guild_json_writeout()

    @schedule_set_image.error
    async def schedule_set_image_error(self, ctx, error):
        if isinstance(error, commands.CheckFailure):
            await ctx.send("You do not have permission to uuse this command.")

    @schedule.command(name = "message")
    @commands.check(guild_leader_check)
    async def schedule_set_message(self, ctx, *, arg=None):
        if not arg:
            try:
                await ctx.send(f'Your current message is currently: {self.guild_info["schedule"]["message"]}')
            except KeyError:
                await ctx.send("You currently have no schedule message set. Reuse the command with a message to set one.\ne.g. `&schedule message This is a message.`")
            return
        elif "clear" in arg:
            self.guild_info["schedule"]["message"] = None
            await ctx.send("Schedule message cleared.")
        else:
            try:
                self.guild_info["schedule"]["message"] = arg
            except KeyError:
                self.guild_info["schedule"] = {}
                self.guild_info["schedule"]["message"] = arg
            await ctx.send(f"Your current schedule message is now set to: {arg}")
        self.guild_json_writeout()

    @schedule_set_message.error
    async def schedule_set_message_error(self, ctx, error):
        if isinstance(error, commands.CheckFailure):
            await ctx.send("You do not have permission to uuse this command.")

    @commands.command(name='newmem')
    async def new_member(self, ctx, member=None, nickname=None):
        new_member_channel = self.bot.get_channel(387464477173481472)
        #guild_role = ctx.guild.get_role(config.new_member_role_id)
        #new_member_channel = self.bot.get_channel(config.new_member_channel_id)
        if not member or not nickname or "@" not in member:
            
            await ctx.send("Both a @user and their nickname is required. Please try the command again with both inputs.")
            return
        new_member = ctx.guild.get_member(get_user_id(member))
        if not new_member:
            await ctx.send(f"User {member} not found.")
            return
        if ctx.channel is not new_member_channel:
            return
        await new_member.edit(nick=nickname)
        await ctx.send(f"Success! {new_member}'s nickname is now {new_member.nick}!")


def setup(bot):
    bot.add_cog(GuildCmd(bot))