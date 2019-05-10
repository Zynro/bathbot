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
from fuzzywuzzy import fuzz

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

def lev_dist_similar(a, b):
    return fuzz.partial_ratio(a.lower(), b.lower())

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
            if shiki_name.lower() == row[2].lower():
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
    def shiki_bounty_embed(self, shikigami_object):
        icon = discord.File(shikigami_object.icon, filename = shikigami_object.icon_name)
        if shikigami_object.hints:
            embed = discord.Embed(title=f"__**{shikigami_object.name}**__", 
                colour=discord.Colour(generate_random_color()), 
                description=f"Hints:\n*{shikigami_object.hints}*")
        else:
            embed = discord.Embed(title=f"__**{shikigami_object.name}**__", 
            colour=discord.Colour(generate_random_color()), 
            description=f"*No hints found*")
        embed.set_thumbnail(url=f"attachment://{shikigami_object.icon_name}")
        embed.add_field(name="OnmyoGuide Bounty Locations (Probably Outdated):", 
            value=self.location_finder(shikigami_object))

        if "None" not in shikigami_object.user_database_locations:
            all_locations = []
            count = 0
            for main in shikigami_object.user_database_locations:
                if count == 5:
                    break
                sub_locs = ', '.join(main[1])
                all_locations.append(f'{bold(main[0])} - {sub_locs}')
                count+=1
            all_locations = '\n'.join(all_locations)
            embed.add_field(name="BubbleTea Database Bounty Locations:", value=all_locations)
        else:
            #Re-add when Database is fully functional
            #embed.add_field(name="BBT-Databased Bounty Locations:", value='None found in database.')
            embed.add_field(name="BubbleTea Database Bounty Locations:", value='Temporarily disabled until the BubbleTea Shikigami Location Database is more populated.')
        return embed, icon

class ShikigamiClass:
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
            if input_name == shiki_name:
                self.alias = [other_name.lower() for other_name in alias.split('\n')]
                self.hints = ", ".join(hints.split("\n"))
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

    def shiki_validate(self, shiki_input, shikigami_db):
        """
        Given a search term of "shiki input" and the shikigami database, returns a list of Shikigami objects.
        If none are found, returns an empty list.
        """
        shikigami_result_list = []
        for shiki in shikigami_db['all']:
            shiki = shiki.lower()
            if shiki_input == shiki:
                return [shikigami_db[shiki]]
            if shiki_input in shikigami_db[shiki].hints.lower():
                shikigami_result_list.append(shikigami_db[shiki])
            if shiki_input in shiki:
                shikigami_result_list.append(shikigami_db[shiki])
            if shiki_input in shikigami_db[shiki].alias:
                shikigami_result_list.append(shikigami_db[shiki])
        if shikigami_result_list:
            return shikigami_result_list
        else:
            high_score = 0
            for shiki in shikigami_db['all']:
                temp_score = lev_dist_similar(shiki_input, shiki)
                if temp_score > high_score:
                    high_score = temp_score
            for shiki in shikigami_db['all']:
                score = lev_dist_similar(shiki_input, shiki)
                if high_score - 5 <= score <= high_score + 5:
                    shikigami_result_list.append(shikigami_db[shiki.lower()])
            return shikigami_result_list


class Shikigami(commands.Cog, Embeds, ShikigamiClass):
    def __init__(self, bot):
        self.bot = bot
        try:
            self.shikigami_db = self.create_classes()
            self.shikigami_db['all'] = self.shikigami_full_list
        except FileNotFoundError:
            DriveAPI.get_gdrive_sheet_database()
            DriveAPI.generate_csv_databases()
            self.shikigami_db = self.create_classes()
            self.shikigami_db['all'] = self.shikigami_full_list

    async def has_permission(ctx):
        return ctx.author.id in owner_list or ctx.author.id in editor_list

    def create_classes(self):
        """Creates all the Shikigami classes with each of their vairables in a dictionary."""
        # Opens and creates the shikigami list from the full list of shikigami
        with open(config.bbt_csv_shikigami_list_file, newline='') as shiki_list_csv:
            shiki_list_reader = csv.reader(shiki_list_csv)
            next(shiki_list_reader) #skips header
            self.shikigami_full_list = [row[0] for row in shiki_list_reader if "frog" not in row[0].lower()]
        return {shiki.lower(): ShikigamiClass(shiki) for shiki in self.shikigami_full_list if "frog" not in shiki.lower()}

    def location_finder(self, shikigami_object):
        if 'None' in shikigami_object.locations:
            return "None found in database."
        locations_base = [location for location in shikigami_object.locations]
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
    async def bounty(self, ctx, *,search=None):
        final_shikigami = []
        if not search:
            await ctx.send('Search term cannot be blank, try again.')
            return
        search = search.lower()
        final_shikigami = self.shiki_validate(search, self.shikigami_db)
        if final_shikigami:
            if len(final_shikigami) > 1:
                final_string = "\n".join([shiki.name for shiki in final_shikigami])
                return await ctx.send(f"*I found multiple matches for your search, please search again with one specified:*\n{final_string}")
            shiki_embed, shiki_icon = self.shiki_bounty_embed(final_shikigami[0])
            await ctx.send(file=shiki_icon, embed=shiki_embed)
            return
        else:
            await ctx.send("For all my bath powers, I could not find your term, or something went wrong.")

    @commands.command()
    async def tengu(self, ctx):
        """hurrhurrhurr"""
        await ctx.send(file=discord.File('./images/tengu.jpg'))

    @commands.command(name = "br")
    async def test_br(self, ctx, *, entry = None):
        for shiki_object in self.shiki_validate(entry, self.shikigami_db):
            await ctx.send(shiki_object.name)

def setup(bot):
    bot.add_cog(Shikigami(bot))

