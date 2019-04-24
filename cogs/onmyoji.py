from __future__ import print_function
import discord
import json
from discord.ext import commands
import os.path
from googleapiclient.discovery import build
from googleapiclient.http import *
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2 import service_account
import io
import csv
import config
import re
import pyexcel as pye
import random

permission = 'You do not have permission to use this command.'
owner_list = config.owner_list
editor_list = config.editor_list

recommend = re.compile(r'recommend',re.IGNORECASE)

with open('lists/stats.json') as file:
    stats_json = json.loads(file.read())

number_dict = {'1':'First', '2':'Second', '3':'Third', '4':'Fourth', '5':'Fifth', '6':'Sixth', '7':'Seventh',1:'First', 2:'Second', 3:'Third', 4:'Fourth', 5:'Fifth', 6:'Sixth', 7:'Seventh'}

def bold(text):
    '''Returns the Discord bolded version of input text.'''
    if text:
        return f'**{text}**'
    else:
        return text

def lower_and_underscore(text):
    """Lowers entire string and replaces all whitespace with underscores."""
    return text.lower().replace(' ', '_')

def generate_random_color():
    return random.randint(0, 0xFFFFFF)

def bracket_check(arg):
    if "<" in arg or ">" in arg:
        return "Please do not include brackets in your command uses. They are to demonstrate that terms are optional, or what terms can be used, for that specific command."
    else:
        return None

class DriveAPI:
    """Manages the Google Drive API Auth and retreiving the CSV database."""
    SERVICE_ACCOUNT_FILE = 'bbt_credentials.json'
    credentials = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=config.SCOPES_DRIVE_READONLY)
    drive_service = build('drive', 'v3', credentials = credentials)

    @classmethod
    def get_gdrive_sheet_database(cls):
        file_id = config.bounty_file_id
        request = cls.drive_service.files().export_media(fileId=file_id, mimeType='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        buffer_file = io.BytesIO()
        downloader = MediaIoBaseDownload(buffer_file, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
            print ("Download %d%%." % int(status.progress() * 100))
        with open (config.bbt_xlsx_file, 'wb') as f:
            f.write(buffer_file.getvalue())

    @classmethod
    def generate_csv_databases(cls):
        """Generate the CSV files from the given XLSX file obtained from Gdrive."""
       # book = pye.get_book(file_name=config.bbt_xlsx_file)
        #Convert Onmyoguide DB
        pye.save_as(file_name = config.bbt_xlsx_file, sheet_name="Bounty List", dest_file_name=config.onmyoguide_csv_db_file)
        #Convert BBT DB
        pye.save_as(file_name = config.bbt_xlsx_file, sheet_name="Data Logging", dest_file_name=config.bbt_csv_db_file)
        #Convert Shikigami Full List
        pye.save_as(file_name = config.bbt_xlsx_file, sheet_name="Shikigami List", dest_file_name=config.bbt_csv_shikigami_list_file)

class DatabaseGeneration:
    # Opens and creates the onmyoguide bounty db
    with open(config.onmyoguide_csv_db_file, newline='') as bounties:
        bounty_reader = csv.reader(bounties)
        for n in range(0, 3):
            next(bounty_reader) #skips the first 3 rows because its headers + message + example
        onmyoguide_database = [row for row in bounty_reader]
    # Opens the BBT-made database for all stages with all their contents.
    with open(config.bbt_csv_db_file, newline='') as bbt_db:
        user_db_reader = csv.reader(bbt_db)
        for i in range(0,6):
            next(user_db_reader)
        user_db = [row for row in user_db_reader]

    @classmethod
    def generate_user_shikigami_locations(cls, shiki_name):
        user_database_filtered_locations = []
        for row in cls.user_db:
            if shiki_name.lower() in row[2].lower():
                contains = row[2].split('\n')
                temp_list = []
                temp_list.append(row[0])
                temp_list.append(row[1])
                for each in contains:
                    if shiki_name.lower() in each.lower():
                        temp_list.append(each)
                        break
                user_database_filtered_locations.append(temp_list)
        return user_database_filtered_locations

class Embeds:
    def shard_trading_embed(self, user):
        need_list = '\n'.join([self.shard_split_variable(arg, 'bold') for arg in self.shard_trading_db[str(user.id)]['need']])
        have_list = '\n'.join([self.shard_split_variable(arg, 'bold') for arg in self.shard_trading_db[str(user.id)]['have']])
        nick = user.name if not user.nick else user.nick
        trading_status = 'available' if  self.check_trading_status(user.id) else 'unavailable'
        try:
            if self.shard_trading_db[str(user.id)]['notes']:
                embed = discord.Embed(title=f"{nick}'s Shard Trading List", 
                    colour=discord.Colour(generate_random_color()), 
                    description=f"__**Notes:**__ {self.shard_trading_db[str(user.id)]['notes']}\n\n{nick} is **{trading_status}** for trading.")
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

    def shiki_bounty_embed(self, shiki):
        color = generate_random_color()
        icon = discord.File(self.shikigami_class[shiki].icon, filename = self.shikigami_class[shiki].icon_name)
        embed = discord.Embed(title=f"__**{self.shikigami_class[shiki].name}**__", colour=discord.Colour(color), description=f"{self.shikigami_class[shiki].name}'s hints are:")
        embed.set_thumbnail(url=f"attachment://{self.shikigami_class[shiki].icon_name}")
        embed.add_field(name="OnmyoGuide Bounty Locations (Probably Outdated):", value=self.location_finder(shiki))

        if "None" not in self.shikigami_class[shiki].user_database_locations:
            all_locations = []
            count = 0
            for main in self.shikigami_class[shiki].user_database_locations:
                if count == 5:
                    break
                sub_locs = ', '.join(main[1])
                all_locations.append(f'{bold(main[0])} - {sub_locs}')
                count+=1
            all_locations = '\n'.join(all_locations)
            embed.add_field(name="BBT-Databased Bounty Locations:", value=all_locations)
        else:
            embed.add_field(name="BBT-Databased Bounty Locations:", value='None found in database.')
        return embed, icon

class Shikigami:
    def __init__(self, input_name):
        self.name = input_name
        self.alias = self.hints = self.locations = self.icon_name = self.icon = None
        self.icon_name = f"{lower_and_underscore(self.name)}.png"
        self.icon = f"{config.shikigami_icon_location}/{self.icon_name}"
        if not os.path.isfile(self.icon):
            self.icon_name = config.unknown_icon_file_name
            self.icon = f'{config.shikigami_icon_location}/{self.icon_name}'
        for row in DatabaseGeneration.onmyoguide_database:
            #need to re-do, uses only shiki from onmyoguide
            shiki_name, alias, hints, locations = row[0], row[1], row[2], row[3]
            if input_name in shiki_name:
                self.alias = [other_name.lower() for other_name in alias.split('\n')]
                self.hints = hints
                self.locations = locations.split('\n')
                break
        user_database = DatabaseGeneration.generate_user_shikigami_locations(self.name)
        if len(user_database) != 0:
            self.user_database_locations = sorted(self.generate_user_database_locations(user_database))
        else:
            self.user_database_locations = 'None found in database.'
        if not self.alias: self.alias = ''
        if not self.hints: self.hints = ''
        if not self.locations: self.locations = 'None found in database.'

    def generate_user_database_locations(self, user_location_database):
        """Generates the BBT Database list of locations"""
        #If no locations, end and return none.
        if len(user_location_database)==0:
            return None
        main_sub_and_shiki_list = []
        for row in user_location_database:
            if "chapter" in row[0].lower():
                sub_loc_stage_name = ''.join(i for i in row[1] if not i.isdigit())
                if any(ch.isdigit() for ch in row[1]):
                    sub_loc_stage_number = number_dict[''.join(i for i in row[1] if i.isdigit())]
                    sub_loc_final = f'{sub_loc_stage_number} {sub_loc_stage_name}'
                else:
                    sub_loc_final = f'{sub_loc_stage_name} '
                amount = ''.join(i for i in row[2] if i.isdigit())
                new_row = [row[0], f'{sub_loc_final}has {amount}']
            else:
                sub_loc_stage_name = row[1]
                amount = ''.join(i for i in row[2] if i.isdigit())
                new_row = [row[0], f'{sub_loc_stage_name} has {amount}']
            main_sub_and_shiki_list.append(new_row)
        final_result = []
        for row in main_sub_and_shiki_list:
            sub_locale = []
            location = row[0]
            for again in main_sub_and_shiki_list:
                if location == again[0]:
                    sub_locale.append(again[1])
            for row in main_sub_and_shiki_list:
                if row[0] == location:
                    main_sub_and_shiki_list.remove(row)
            final_result.append([location, sub_locale])
        return final_result


class Onmyoji(commands.Cog, Embeds):
    def __init__(self, bot):
        self.bot = bot
        try:
            self.shikigami_class = self.create_classes()
        except FileNotFoundError:
            DriveAPI.get_gdrive_sheet_database()
            DriveAPI.generate_csv_databases()
            self.shikigami_class = self.create_classes()
        self.shard_load_json()

    async def has_permission(ctx):
        return ctx.author.id in owner_list or ctx.author.id in editor_list

    def create_classes(self):
        """Creates all the Shikigami classes with each of their vairables in a dictionary."""
        # Opens and creates the shikigami list from the full list of shikigami
        with open(config.bbt_csv_shikigami_list_file, newline='') as shiki_list_csv:
            shiki_list_reader = csv.reader(shiki_list_csv)
            next(shiki_list_reader) #skips header
            shikigami_full_list = [row[0] for row in shiki_list_reader]
        return {shiki.lower(): Shikigami(shiki) for shiki in shikigami_full_list if "frog" not in shiki.lower()}

    def location_finder(self, shiki):
        if 'None' in self.shikigami_class[shiki].locations:
            return "None found in database."
        locations_base = [location for location in self.shikigami_class[shiki].locations]
        for location in locations_base:
            match_recommend = recommend.search(location)
            if match_recommend:
                locations_base[locations_base.index(location)] = bold(location)
        locations_onmyoguide = '\n'.join(locations_base)
        return locations_onmyoguide

    @commands.command()
    async def shikistats(self, ctx, *search):
        name = ' '.join([term.lower() for term in search])
        result = stats_json.get(name)
        if not result:
            fuzzy_name = [key for key in stats_json.keys() if name in key]
            if fuzzy_name:
                result = stats_json.get(fuzzy_name[0])
        if result:
            await ctx.send(f"""The stats for {name.title()} at level 40 are:
            **ATK:** _{result['attack']}_
            **HP:** _{result['health']}_
            **DEF:** _{result['defense']}_
            **SPD:** _{result['speed']}_
            **CRIT:** _{result['crit']}_
            **CDMG:** _{result['crit dmg']}_
            **EHIT:** _{result['eff hit']}_
            **ERES:** _{result['eff res']}_""")
            return
        await ctx.send(f'Couldn\'t find stats for {name.title()}')

    @commands.command(name='database', aliases=['googledoc', 'link', 'share'])
    @commands.check(has_permission)
    async def get_shared_doc_link(self, ctx):
        '''If Officer, returns the link for the database.'''
        if ctx.channel.id != config.officer_chat_id:
            await ctx.send('This command cannot be used in this channel.')
        else:
            await ctx.send(f'Here is the link for the Onmyoji database:\n{config.database_google_link}')

    @get_shared_doc_link.error
    async def get_shared_doc_link_error(self, ctx, error):
        if isinstance(error, commands.CheckFailure):
            await ctx.send("You do not have permission to uuse this command.")

    @commands.command(name='database_update', aliases=['update', 'download'])
    async def download_shikigami_update_excel(self, ctx):
        '''If Officer, updates the bot's local database file.'''
        await ctx.send("Now updating... Please wait while BathBot pulls the latest database.")
        DriveAPI.get_gdrive_sheet_database()
        DriveAPI.generate_csv_databases()
        self.create_classes()
        await ctx.send("The Shikigami bounty list database has been successfully updated!")

    @download_shikigami_update_excel.error
    async def download_shikigami_update_error(self, ctx, error):
        if isinstance(error, commands.CheckFailure):
            await ctx.send("You do not have permission to update the database file.\nPlease tag an @Officer to have them update it.")

    @commands.command()
    async def bounty(self, ctx, *search):
        if not search:
            await ctx.send('Search term cannot be blank, try again.')
            return
        search = ' '.join([term.lower() for term in search])
        for shiki in self.shikigami_class.keys():
            if search in shiki:
                shiki_embed, shiki_icon = self.shiki_bounty_embed(shiki)
                await ctx.send(file=shiki_icon, embed=shiki_embed)
                return
            if search in self.shikigami_class[shiki].hints.lower():
                shiki_embed, shiki_icon = self.shiki_bounty_embed(shiki)
                await ctx.send(file=shiki_icon, embed=shiki_embed)
                return
            if search in self.shikigami_class[shiki].alias:                
                shiki_embed, shiki_icon = self.shiki_bounty_embed(shiki)
                await ctx.send(file=shiki_icon, embed=shiki_embed)
                return
        await ctx.send("For all my bath powers, I could not find your term, or something went wrong.")

    @commands.command()
    async def tengu(self, ctx):
        """hurrhurrhurr"""
        await ctx.send(file=discord.File('./images/tengu.jpg'))

#=====================Shard Trading===========================

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
            return numbers, shiki
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
    async def shard_print_list_user(self, ctx):
        """
        Prints the users current status, notes, and both have/need lists of shards, all in a fancy little embed.
        """
        if not self.shard_trading_db[str(ctx.author.id)]['need'] or not self.shard_trading_db[str(ctx.author.id)]['have']:
            return await ctx.send("You must have both a 'need' and a 'have' list before you use this command.")
        embed = self.shard_trading_embed(ctx.author)
        await ctx.send(embed=embed)

    def shard_set_list(self, ctx, args, list_name):
        if not args:
            try: 
                shard_list = '\n'.join(self.shard_print_list(str(ctx.message.author.id), list_name))
                return f"Shards you **{list_name}**: ```\n{shard_list}```"
            except KeyError:
                return f'You do not have a {list_name} list yet! Use `&shard` to generate your entry first!'
        if bracket_check(args):
            return bracket_check(args)
        if "clear" in args:
            self.shard_trading_db[str(ctx.message.author.id)][list_name] = ''
            return f"Your {list_name} list has been cleared. Note that you will not be able to use `&shard list` until both lists have entires."
        arg_list = args.split("\n")
        for shiki in arg_list:
            numbers, shiki = self.shard_split_variable(shiki, 'split')
            if "frog" not in shiki.lower().strip():
                if shiki.lower().strip() not in self.shikigami_class.keys():
                    return f"The following shikigami is not present in the master Shikigami database: \n**{shiki}**\nSpelling is important, else searches won't work. Please try again."
        self.shard_load_json()
        try: 
            self.shard_trading_db[str(ctx.message.author.id)][list_name] = arg_list
        except KeyError:
            self.shard_trading_db[str(ctx.message.author.id)] = {}
            self.shard_trading_db[str(ctx.message.author.id)][list_name] = arg_list
        self.shard_file_writeout()
        return None

    @shard.command(name="need")
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

    @shard.command(name="have")
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

    @shard.command(name="status")
    async def shard_set_trading_status(self, ctx, *arg):
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
        if bracket_check(arg):
            return await ctx.send(bracket_check(arg))
        self.shard_load_json()
        try:
            temp = self.shard_trading_db[str(ctx.author.id)]['status']
        except KeyError:
            self.shard_trading_db[str(ctx.author.id)]['status'] = True
            self.shard_file_writeout();
            return await ctx.send(f"{ctx.author.mention} is now available to be searched for trading.")
        if not arg:
            trading_status = 'available' if  self.check_trading_status(ctx.author.id) else 'unavailable'
            return await ctx.send(f"{ctx.author.mention} is currently {trading_status} to be searched for trading.")
        else:
            if "on" in arg:
                self.shard_trading_db[str(ctx.author.id)]['status'] = True
                self.shard_file_writeout();
                return await ctx.send(f"{ctx.author.mention} is now available to be searched for trading.")
            elif "off" in arg:
                self.shard_trading_db[str(ctx.author.id)]['status'] = False
                self.shard_file_writeout();
                return await ctx.send(f"{ctx.author.mention} is unavailable to be searched for trading.")

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
Use `&search @user` where user is one of the ones listed above to check which shards each of you need/have!
""")
        other_user_raw = ' '.join(other_user_raw)
        if bracket_check(other_user_raw):
            return await ctx.send(bracket_check(other_user_raw))
        for member in ctx.guild.members:
            if "@" in other_user_raw:
                other_user = ''.join(i for i in other_user_raw if i.isdigit())
                break
            else:
                try:
                    if other_user_raw.lower().strip() in member.nick.lower():
                        other_user = str(member.id)
                        break
                except (TypeError, AttributeError):
                    if other_user_raw.lower().strip() in member.name.lower():
                        other_user = str(member.id)
                        break
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
            you_need_they_have = ', '.join(you_need_they_have)
            you_have_they_need = ', '.join(you_have_they_need)
            if not ctx.guild.get_member(int(other_user)).nick:
                searched_user = ctx.guild.get_member(int(other_user)).name
            else:
                searched_user = ctx.guild.get_member(int(other_user)).nick
            await ctx.send(f"""
__Good news everyone!__
You and {searched_user} have shards that can be exchanged!
Shards you **need** that {searched_user} has:
```
{you_need_they_have}
```
Shards you **have** that {searched_user} needs:
```
{you_have_they_need}
```
""")
            return
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
Reusing the above commands will overwrite lists. Adding/removing individually is currently not supported.
Spelling is important and mispelled shikigami will not be accepted. Number placement does not matter.

__Afterwards, the following commands can be used:__
If the command has <> code brackets, it means that command accepts a term. Some commands work differently with and without terms. Make sure to read each segment carefully. The code brackets <> are to not be used during the actual command usage.


**&shard <have/need> clear**
    Clears that specific list.
    e.g. `&shard have clear`

**&shard list**
    Displays your shard lists.

**&shard status <on/off>**
    No term: Returns current status
    On: Sets status to "on", enabling users to search for you.
    Off: Sets status to "off", disabling users to search for you.

**&shard notes <notes>**
    No term: Disables your notes entry.
    Notes provided: Sets your notes when using `&shard list` to the message given.
    e.g. `&shard notes 1:1 Trades only`

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
#=====================Shard Trading===========================

        

def setup(bot):
    bot.add_cog(Onmyoji(bot))

