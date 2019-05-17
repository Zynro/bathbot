from __future__ import print_function
import discord
import json
from discord.ext import commands
import os.path
import io
import config
import re
import random

permission = 'You do not have permission to use this command.'
owner_list = config.owner_list
editor_list = config.editor_list

recommend = re.compile(r'recommend',re.IGNORECASE)

def generate_random_color():
    return random.randint(0, 0xFFFFFF)

def bracket_check(arg):
    if "<" in arg or ">" in arg:
        return "Please do not include brackets in your command uses. They are to demonstrate that terms are optional, or what terms can be used, for that specific command."
    else:
        return None

def bold(text):
    '''Returns the Discord bolded version of input text.'''
    if text:
        return f'**{text}**'
    else:
        return text

class Embeds:
    def shard_trading_embed(self, user):
        user_id_string = str(user.id)
        need_list = '\n'.join([self.shard_split_variable(arg, 'bold') for arg in self.shard_trading_db[user_id_string]['need']])
        have_list = '\n'.join([self.shard_split_variable(arg, 'bold') for arg in self.shard_trading_db[user_id_string]['have']])
        nick = user.name if not user.nick else user.nick
        trading_status = 'available' if  self.check_trading_status(user_id_string) else 'unavailable'
        try:
            if self.shard_trading_db[user_id_string]['notes']:
                embed = discord.Embed(title=f"{nick}'s Shard Trading List", 
                    colour=discord.Colour(generate_random_color()), 
                    description=f"__**Notes:**__ {self.shard_trading_db[user_id_string]['notes']}\n\n{nick} is **{trading_status}** for trading.")
            else:
                embed = discord.Embed(title=f"{nick}'s Shard Trading List", colour=discord.Colour(generate_random_color()), description=f"{nick} is **{trading_status}** for trading.")  
        except KeyError:
            embed = discord.Embed(title=f"{nick}'s Shard Trading List", 
                colour=discord.Colour(generate_random_color()), 
                description=f"{nick} is **{trading_status}** for trading.")         
        embed.set_thumbnail(url=user.avatar_url)
        #embed.set_footer(text="Up-to-Date as of <<timestamp>>")
        embed.add_field(name="Needs these Shards:", value=need_list, inline=True)
        embed.add_field(name="Has these Shards:", value=have_list, inline=True)
        return embed

    def shard_trading_search_results_embed(self, user, other_user, you_have_they_need, you_need_they_have, search_type):
        thumbnail = random.choice(os.listdir("./images/shard-trading"))
        if search_type == "individual":
            icon = discord.File(f"./images/shard-trading/{thumbnail}", filename = thumbnail)
            embed = discord.Embed(title="*Good News Everyone!*", 
                colour=discord.Colour(generate_random_color()), 
                description=f"You and {other_user} have the following shards that can be traded!")

            embed.set_thumbnail(url=f"attachment://{thumbnail}")

            embed.add_field(name=f"{user}'s Shards:", value=you_have_they_need, inline=True)
            embed.add_field(name=f"{other_user}'s Shards", value=you_need_they_have, inline=True)
            #embed.add_field(name="Don't be shy", value="@them to set up a trade! ")
            return icon, embed

class Shard(commands.Cog, Embeds):
    def __init__(self, bot):
        self.bot = bot
        self.shard_load_json()
        self.Shikigami = self.bot.get_cog("Shikigami")
        self.shikigami_db = self.bot.get_cog("Shikigami").shikigami_db


    async def has_permission(ctx):
        return ctx.author.id in owner_list or ctx.author.id in editor_list


    def user_validation(self, ctx, other_user_raw):
        if "@" in other_user_raw:
            other_user = ''.join(i for i in other_user_raw if i.isdigit())
        for member in ctx.guild.members:
            try:
                if other_user_raw.lower().strip() in member.nick.lower():
                    other_user = str(member.id)
                    break
            except (TypeError, AttributeError):
                if other_user_raw.lower().strip() in member.name.lower():
                    other_user = str(member.id)
                    break
        return other_user

    def shard_load_json(self):
        """
        Loads the json shard database file. 
        Generates a new empty one if it does not exist.
        """
        try:
            try:
                with open(f'{config.list_path}/shard-trading-db.json', 'r') as shard_file:
                    self.shard_trading_db = json.loads(shard_file.read())
            except ValueError:
                self.shard_trading_db = {}
        except FileNotFoundError:
            with open(f'{config.list_path}/shard-trading-db.json', 'w') as shard_file:
                self.shard_trading_db = {}
                print('New Json file generated!')

    def shard_file_writeout(self):
        """Writes to Json shard database file."""
        with open(f'{config.list_path}/shard-trading-db.json', 'w+') as shard_file:
            json.dump(self.shard_trading_db, shard_file, indent=4)
        return

    def shard_split_variable(self, arg, op):
        """
        Splits the incoming '<Shiki> <Amount>' variable into its number and shiki components.
        """
        numbers = ''.join(b for b in arg if b.isdigit())
        shiki = ''.join(b for b in arg if not b.isdigit())
        if op == 'split':
            return numbers.strip(), shiki.strip()
        elif op == "bold":
            if numbers:
                return f"{bold(numbers)} {shiki}"
            else:
                return arg

    def shard_print_list(self, user, list_name):
        """
        Returns the entirety of the 'need' list of the given user in the format of
        <Amount> <Shiki>
        Each on a new line.
        """
        self.shard_load_json()
        if list_name == 'have':
            have_list = []
            for entry in self.shard_trading_db[user]['have']:
                if not entry:
                    continue
                numbers, shiki = self.shard_split_variable(entry, 'split')
                have_list.append(f"{numbers} {shiki}")
            return have_list
        elif list_name == 'need':
            need_list = []
            for entry in self.shard_trading_db[user]['need']:
                if not entry:
                    continue
                numbers, shiki = self.shard_split_variable(entry, 'split')
                need_list.append(f"{numbers} {shiki}")
            return need_list

    def shard_entry_init(self, ctx):
        """
        Initializes the dicitonary entry of the user in the shard trading database.
        """
        self.shard_trading_db[str(ctx.message.author.id)] = {'status': True, 'notes':'', 'have':'', 'need':''}
        self.shard_file_writeout()
        return

    @commands.group()
    async def shard(self, ctx):
        """
        Shard trading command group. Use the various commands to assign and initialize shard trading.
        Type &help shard <subcommand> where 'subcommand' is one of the subcommands listed below to receive more help on that subcommand.
        """
        if ctx.invoked_subcommand is None:
            if self.shard_trading_db.get(str(ctx.message.author.id)) is None:
                self.shard_entry_init(ctx)
            await ctx.send("""
__Welcome to BathBot's Shard Trading implementation!__

To recieve a full tutorial on every command available in this feature, use the following command, and I will send you an instructional message: 
`&shard help`

*If you're constantly seeing this message, it probably means you're using an improper subcommand. Any non-existing subcommand will return this message, every time.*

For more help, tag Zynro and he'll be happy to assist.
""")

    
    @shard.command(name='list',aliases=['print'])
    async def shard_print_list_user(self, ctx, *, target=None):
        """
        Prints the users current status, notes, and both have/need lists of shards, all in a fancy little embed.

        If used as-is, returns *your* list.
            &shard list
        If given a user's name, nickname, or @tag, returns their list if their trading status is available.
            &shard list zynro
        """
        self.shard_load_json()
        user_id = str(ctx.author.id) if not target else self.user_validation(ctx, target)
        user = ctx.author if not target else ctx.guild.get_member(int(user_id))
        if not target:
            try:
                temp = self.shard_trading_db[user_id]
            except KeyError:
                self.shard_entry_init
            if not self.shard_trading_db[user_id]['need'] or not self.shard_trading_db[user_id]['have']:
                return await ctx.send("You must have both a 'need' and a 'have' list before you use this command.")
        else:
            try:
                temp = self.shard_trading_db[user_id]
            except KeyError:
                return await ctx.send("That user has not used the shard command group before and has no lists.")
            if not self.shard_trading_db[user_id]['need'] or not self.shard_trading_db[user_id]['have']:
                return await ctx.send("That user must have both 'need' and 'have' lists before you can check their shards.")
        if self.shard_trading_db[user_id]['status'] == False:
            return await ctx.send("That user is currently not available for trading.")
        embed = self.shard_trading_embed(user)
        await ctx.send(embed=embed)

    def shard_set_list(self, ctx, args, list_name):
        if not args:
            try: 
                shard_list = '\n'.join(self.shard_print_list(str(ctx.message.author.id), list_name))
                if not shard_list:
                    return f"Your {list_name} list is currently empty."
                else:
                    return f"Shards you **{list_name}**: ```\n{shard_list}```"
            except KeyError:
                return f'You do not have a {list_name} list yet! Use `&shard` to generate your entry first!'
        if bracket_check(args):
            return bracket_check(args)
        arg_list = args.split("\n")
        arg_index = 0
        failed_list = []
        for shiki in arg_list:
            numbers, shiki = self.shard_split_variable(shiki, 'split')
            if "frog" not in shiki.lower().strip():
                if shiki.lower().strip() not in self.shikigami_db.keys():
                    failed_list.append(shiki)
            try:
                arg_list[arg_index] = f"{numbers} {self.shikigami_db[shiki.lower()].name}"
                arg_index += 1
            except KeyError:
                continue
        if failed_list:
            result = "The following shikigami are not present in the master Shikigami database:\n\n"
            for shiki in failed_list:
                result += f"**{shiki}**"
                guess = ", ".join([shiki.name for shiki in self.Shikigami.shiki_validate(shiki, self.shikigami_db)])
                result = f"{result}\n*Did you mean:* `{guess}`\n"
            result += "\nExact spelling is important, else searches won't work. Please try again."
            return result
        self.shard_load_json()
        try: 
            self.shard_trading_db[str(ctx.message.author.id)][list_name] = arg_list
        except KeyError:
            self.shard_trading_db[str(ctx.message.author.id)] = {}
            self.shard_trading_db[str(ctx.message.author.id)][list_name] = arg_list
        self.shard_file_writeout()
        return None

    def mod_shikigami_to_list(self, user, input_shiki, list_name, mod):
        self.shard_load_json()
        numbers, shiki = self.shard_split_variable(input_shiki.lower(), 'split')
        if mod == "add":
            shiki_list = self.Shikigami.shiki_validate(shiki, self.shikigami_db)
            if len(shiki_list)>1:
                fuzzy = ", ".join([shiki.name for shiki in shiki_list])
                return f"**{shiki}** does not exist in the master Shikigami list.\n\n*Did you mean:*\n`{fuzzy}`\n\nPlease try again with exact spelling."
            else:
                shiki = shiki_list[0].name.lower()
        shiki_class_name = self.shikigami_db[shiki].name if mod == "add" else None
        for entry in self.shard_trading_db[user][list_name]:
            if shiki.lower() in entry.lower():
                index_num = self.shard_trading_db[user][list_name].index(entry)
                entry_name = "".join(char.strip() for char in self.shard_trading_db[user][list_name][index_num] if not char.isdigit())
                if mod == "add":
                    self.shard_trading_db[user][list_name][index_num] = f"{numbers} {shiki_class_name}" if numbers else f"{shiki_class_name}"
                    self.shard_file_writeout()
                    return f"**{shiki_class_name}** already exists in your {list_name} list. The amount has been updated to __{numbers}__."
                if mod == "remove":
                    removed_item = self.shard_trading_db[user][list_name].pop(index_num)
                    self.shard_file_writeout()
                    if removed_item:
                        return f"**{entry_name}** has been removed from your __{list_name}__ list."
                    else:
                        return f"Removal failed, **{entry_name}** is not present in your __{list_name}__ list. "
        if mod == "add":
            if numbers:
                self.shard_trading_db[user][list_name].append(f"{numbers} {shiki_class_name}")
            else:
                self.shard_trading_db[user][list_name].append(shiki_class_name)
            self.shard_file_writeout()
            return f"You have added the entry: **{numbers} {shiki_class_name}** to your __{list_name}__ list."
        elif mod == "remove":
            return f"Removal failed, **{input_shiki}** is not present in your __{list_name}__ list. "

    @shard.group(name="need", invoke_without_command=True)
    async def shard_set_need(self,ctx,*,args=None):
        """
        Sets your current shard 'need' list, or changes it in the following ways.

        If given a list with each shikigami on a new line, sets it to that list.
        Keep in mind this will OVERWRITE your current list. Individual adding/removing is not supported.

        An example would be:
        ---------------------
        &shard need 
        Ootengu 5
        Miketsu 4
        Ibaraki Doji 3
        ---------------------

        If "clear" is used, clears your list entirely:
            &shard need clear
        If used as-is, returns your list:
            &shard need
        """
        return_message = self.shard_set_list(ctx, args, 'need')
        if return_message:
            return await ctx.send(return_message) 
        arg_string = '\n'.join(self.shard_trading_db[str(ctx.message.author.id)]['need'])
        trading_status = 'available' if self.check_trading_status(ctx.author.id) else 'unavailable'
        await ctx.send(f'The shards you need are now set to: ```\n{arg_string}```\nYou are currently {bold(trading_status)} for trading.')

    @shard_set_need.command(name="add", aliases=['set'])
    async def shard_set_need_add_replace(self, ctx, *, entry=None):
        if not entry:
            return await ctx.send("You must enter a Shikigami to add to the list!")
        entry = entry.lower().strip()
        numbers, shiki = self.shard_split_variable(entry, 'split')
        return_message = self.mod_shikigami_to_list(str(ctx.author.id), entry, "need", "add")
        return await ctx.send(return_message)

    @shard_set_need.command(name="remove")
    async def shard_set_need_remove(self, ctx, *, entry=None):
        if not entry:
            return await ctx.send("You must enter a Shikigami to add to the list!")
        entry = entry.lower().strip()
        numbers, shiki = self.shard_split_variable(entry, 'split')
        return_message = self.mod_shikigami_to_list(str(ctx.author.id), entry, "need", "remove")
        return await ctx.send(return_message)

    @shard_set_need.command(name="clear")
    async def shard_set_need_clear(self, ctx):
        self.shard_load_json()
        self.shard_trading_db[str(ctx.message.author.id)]["need"] = []
        self.shard_file_writeout()
        return await ctx.send("Your need list has been cleared. Note that you will not be able to use `&shard list` until both lists have entires.")


    @shard.group(name="have", invoke_without_command=True)
    async def shard_set_have(self,ctx,*,args=None):
        """
        Sets your current shard 'have' list, or changes it in the following ways.

        If given a list with each shikigami on a new line, sets it to that list.
        Keep in mind this will OVERWRITE your current list. Individual adding/removing is not supported.

        An example would be:
        ---------------------
        &shard have 
        Ootengu 5
        Miketsu 4
        Ibaraki Doji 3
        ---------------------

        If "clear" is used, clears your list entirely:
            &shard have clear
        If used as-is, returns your list:
            &shard have
            """
        return_message = self.shard_set_list(ctx, args, 'have')
        if return_message:
            return await ctx.send(return_message)
        arg_string = '\n'.join(self.shard_trading_db[str(ctx.message.author.id)]['have'])
        trading_status = 'available' if  self.check_trading_status(ctx.author.id) else 'unavailable'
        await ctx.send(f'The shards you have are now set to: ```\n{arg_string}```\nYou are currently {bold(trading_status)} for trading.')

    @shard_set_have.command(name="add", aliases=['set'])
    async def shard_set_have_add_replace(self, ctx, *, entry=None):
        if not entry:
            return await ctx.send("You must enter a Shikigami to add to the list!")
        entry = entry.lower().strip()
        numbers, shiki = self.shard_split_variable(entry, 'split')
        return_message = self.mod_shikigami_to_list(str(ctx.author.id), entry, "have", "add")
        return await ctx.send(return_message)

    @shard_set_have.command(name="remove")
    async def shard_set_have_remove(self, ctx, *, entry=None):
        if not entry:
            return await ctx.send("You must enter a Shikigami to add to the list!")
        entry = entry.lower().strip()
        numbers, shiki = self.shard_split_variable(entry, 'split')
        return_message = self.mod_shikigami_to_list(str(ctx.author.id), entry, "have", "remove")
        return await ctx.send(return_message)

    @shard_set_have.command(name="clear")
    async def shard_set_have_clear(self, ctx):
        self.shard_load_json()
        self.shard_trading_db[str(ctx.message.author.id)]["have"] = []
        self.shard_file_writeout()
        return await ctx.send("Your have list has been cleared. Note that you will not be able to use `&shard list` until both lists have entires.")

    @shard.command(name="notes")
    async def shard_set_notes(self, ctx, *notes):
        """
        Sets the user note for their shard trading database entry.
        Leave the field blank to disable, otherwise type in a note to set that note.

        Examples:
        ---------------
        Disabling notes:
        `shard notes`

        Setting Notes to "1:1 trades all":
        `&shard notes 1:1 trades all`
        ---------------
        """
        args = ' '.join(notes)
        if bracket_check(args):
            return await ctx.send(bracket_check(args))
        self.shard_load_json()
        if self.check_trading_status(ctx.author.id) == True:
            trading_status = "available"
        else:
            trading_status = "unavailable"
        if not args:
            self.shard_trading_db[str(ctx.author.id)]['notes'] = ''
            await ctx.send(f"Notes disabled.\nYou are currently {bold(trading_status)} for trading.")
            self.shard_file_writeout()
        else:
            self.shard_trading_db[str(ctx.author.id)]['notes'] = args
            await ctx.send(f"Your Shard Trading entry Notes have been set to:\n```{args}```\nYou are currently {bold(trading_status)} for trading.")
            self.shard_file_writeout()

    def check_trading_status(self, user):
        try:
            return self.shard_trading_db[str(user)]['status']
        except KeyError:
            self.shard_trading_db[str(user)]['status'] = True
            self.shard_file_writeout()
            return True

    @shard.group(name="status")
    async def shard_status(self, ctx):
        """
        Prints the current shard trading availability of the user.
        Give either the term 'on' or 'off' to set your status to that state.

        Example Usage:
        ---------------------
        Check current status:
            &shard status
        Turn status on:
            &shard status on
        Turn status off:
            &shard status off
        ---------------------
        """
        if ctx.invoked_subcommand is None:
            self.shard_load_json()
            try:
                temp = self.shard_trading_db[str(ctx.author.id)]['status']
            except KeyError:
                self.shard_trading_db[str(ctx.author.id)]['status'] = True
                self.shard_file_writeout();
                return await ctx.send(f"{ctx.author.mention} is now available to be searched for trading.")
            trading_status = 'available' if  self.check_trading_status(ctx.author.id) else 'unavailable'
            return await ctx.send(f"{ctx.author.mention} is currently {trading_status} to be searched for trading.")

    @shard_status.command(name="on")
    async def shard_status_set_on(self, ctx):
        self.shard_trading_db[str(ctx.author.id)]['status'] = True
        self.shard_file_writeout();
        return await ctx.send(f"{ctx.author.mention} is now available to be searched for trading.")

    @shard_status.command(name="off")
    async def shard_status_set_off(self, ctx):
        self.shard_trading_db[str(ctx.author.id)]['status'] = False
        self.shard_file_writeout();
        return await ctx.send(f"{ctx.author.mention} is now unavailable to be searched for trading.")

    def get_shiki_set(self, user, list_name):
        return set([''.join(i for i in value if not i.isdigit()).strip().lower() for value in self.shard_trading_db[user][list_name]])

    def compare_shard_db(self, main_user, other_user):
        try:
            if self.check_trading_status(main_user) == False or self.check_trading_status(other_user) == False:
                return None, None
            user1_have_list = self.get_shiki_set(main_user, 'have')
            user1_need_list = self.get_shiki_set(main_user, 'need')
            user2_have_list = self.get_shiki_set(other_user, 'have')
            user2_need_list = self.get_shiki_set(other_user, 'need')
            you_have_they_need = user1_have_list.intersection(user2_need_list)
            you_need_they_have = user1_need_list.intersection(user2_have_list)
            you_have_they_need = [shiki.capitalize() for shiki in you_have_they_need]
            you_need_they_have = [shiki.capitalize() for shiki in you_need_they_have]
        except KeyError:
            return None, None
        if len(you_have_they_need) == 0 and len(you_need_they_have) == 0:
            return None, None
        return you_have_they_need, you_need_they_have

    

    @shard.command(name="search")
    async def shard_search(self, ctx, *other_user_raw):
        """
        Compares shard trading lists with other users.
        Specifying no user searches the entire database.
            &shard search
        Specify a name, or an @user tag to compare to that single user:
            &shard search Zynro
        """
        self.shard_load_json()
        main_user = str(ctx.message.author.id)
        other_user = None
        if not other_user_raw:
            match_list = []
            for user in self.shard_trading_db:
                if user == main_user:
                    continue
                you_have_they_need, you_need_they_have = self.compare_shard_db(main_user, user)
                if not you_have_they_need:
                    continue
                if len(you_have_they_need) >= 1 and len(you_need_they_have) >= 1:
                    try:
                        if not ctx.guild.get_member(int(user)).nick:
                            match_list.append(ctx.guild.get_member(int(user)).name)
                        else:
                            match_list.append(ctx.guild.get_member(int(user)).nick)
                    except AttributeError:
                        continue
            if not match_list:
                return await ctx.send("I apologize, I was not able to find any other members that match shard needs and haves with you.")
            if len(match_list) == 1:
                match_string = match_list[0]
            else:
                match_string = '\n'.join(match_list)
            return await ctx.send(f"""
__Good news everyone!__
You and the following users have shards that can be traded:
**{match_string}**
Use `&search user` where user is one of the ones listed above to check which shards each of you need/have!
""")
        other_user_raw = ' '.join(other_user_raw)
        if "@" not in other_user_raw:
            if bracket_check(other_user_raw):
                return await ctx.send(bracket_check(other_user_raw))
        other_user = self.user_validation(ctx, other_user_raw)
        if not other_user:
            return await ctx.send("I could not find that user, or you typed an improper keyword.")
        you_have_they_need, you_need_they_have = self.compare_shard_db(main_user, other_user)
        if not you_have_they_need:
            await ctx.send("Either you or the user you're checking doesn't have entries in the shard database, or one of you isn't available for trading.")
            return
        if len(you_have_they_need) == 0 or len(you_need_they_have) == 0:
            await ctx.send(f"Unfortunately, based on your lists, you and {other_user_raw} do not have any shards that can be exchanged.")
            return
        else:
            you_need_they_have = '\n'.join(you_need_they_have)
            you_have_they_need = '\n'.join(you_have_they_need)
            other_user = ctx.guild.get_member(int(other_user))
            searched_user = other_user.name if not other_user.nick else other_user.nick
            primary_user = ctx.guild.get_member(int(main_user))
            primary_user = primary_user.name if not primary_user.nick else primary_user.nick
            icon, embed = self.shard_trading_search_results_embed(primary_user, searched_user, you_have_they_need, you_need_they_have, "individual")
            return await ctx.send(file=icon, embed=embed)
        return await ctx.send("I didn't understand what you meant, try again.")

    @shard.command(name="help")
    async def shard_help_text_spam(self, ctx):
        await ctx.send("I sent you an instructional message!")
        await ctx.author.send("""
__**Bathbot Shard Trading 101:**__
First, create both your 'need' and 'have' lists of shards. The commands for this are:
`&shard need <list>` 
and
`&shard have <list>`
Where <list> is the list of your shards, each on a new line.
__Example:__
```&shard need 
Orochi 50
Miketsu 13
16 Ootengu 
22 Yotohime``` 
Reusing the above commands will overwrite lists. To add/remove individual entries, look for those commands below.
Spelling is important and mispelled shikigami will not be accepted. Number placement does not matter.

__Afterwards, the following commands can be used:__
*If the command has <> code brackets, it means that command accepts a term. Some commands work differently with and without terms. Make sure to read each segment carefully. The code brackets <> are to not be used during the actual command usage.*

**&shard <have/need> clear**
    Clears that specific list.
    e.g. `&shard have clear`

**&shard <have/need> add <shikigami>**
    Sets the listed shikigami to your list. If the shikigami already exists in that list, updates that number, otherwise, adds it.
    e.g. `&shard have add Orochi 1`
    e.g. `&shard need add 38 Sakura`

**&shard <have/need> remove <shikigami>**
    Removes the specified shikigami from the specified list. This does not update the number, but deletes the entire entry.
    e.g. `&shard have remove Orochi`
    e.g. `&shard need remove Onikiri`

**&shard list <target>**
    Displays shard lists.
    No term: Returns your list.
    User Name, Nickname, or @tag: Returns that users' lists if their trading status is available.


**&shard status <on/off>**
    No term: Returns current status
    On: Sets status to "on", enabling users to search for you.
    Off: Sets status to "off", disabling users to search for you.

**&shard notes <notes>**
    No term: Disables your notes entry.
    Notes provided: Sets your notes when using `&shard list` to the message given.
    e.g. `&shard notes 1:1 Trades only`
    
""")
        await ctx.author.send("""
**&shard search <user>**
    No term: Searches entire database for shard trading matches
    User Name, Nickname, or @tag: Searches for matches between you and that user.
    e.g. `&shard search zynro`
    e.g. `&shard search @zynro`

**&shard help**
    Returns this message.

**&help shard**
    Returns the help statement for the shard command group, and lists all possible subcommands.

**&help shard <subcommand>**
    Returns the help for the specific subcommand,
    e.g. `&help shard need`

Note: These commands can ***ONLY*** be used in Bathbot's connected servers. Such as #fox-abuse in the BubbleTea Discord.
""")

def setup(bot):
    bot.add_cog(Shard(bot))

