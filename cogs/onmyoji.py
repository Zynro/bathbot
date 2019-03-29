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
import pandas as pd

permission = 'You do not have permission to use this command.'
owner_list = config.owner_list
editor_list = config.editor_list

recommend = re.compile(r'recommend',re.IGNORECASE)

with open('lists/stats.json') as file:
    stats_json = json.loads(file.read())

def bold(input):
    '''Returns the Discord bolded version of input text.'''
    return f'**{input}**'

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
        #Convert Onmyoguide DB
        data_xls = pd.read_excel(config.bbt_xlsx_file, 'Bounty List', index_col=None)
        data_xls.to_csv(config.onmyoguide_csv_db_file, encoding='utf-8', index=False)
        #Convert BBT DB
        data_xls = pd.read_excel(config.bbt_xlsx_file, 'Data Logging', index_col=None)
        data_xls.to_csv(config.bbt_csv_db_file, encoding='utf-8', index=False)
        #Convert Shikigami Full List
        data_xls = pd.read_excel(config.bbt_xlsx_file, 'Shikigami List', index_col=None)
        data_xls.to_csv(config.bbt_csv_shikigami_list_file, encoding='utf-8', index=False)

class Shikigami:
    def __init__(self, input_name, onmyoguide_db, bbt_db):
        for row in onmyoguide_db:
            shiki_name, alias, hints, locations = row[0], row[1], row[2], row[3]
            if input_name.lower() in shiki_name.lower():
                self.name = shiki_name
                self.alias = alias
                self.hints = hints
                self.locations = locations.split('\n')
                break
            elif input_name.lower() in alias.lower():
                self.name = shiki_name
                self.alias = alias
                self.hints = hints
                self.locations = locations
                break
            else:
                self.locations = "No data."
        #adds the bbt locations, currently this is a list of lists that each have 3 elements, the main location, the sublocation, and the contents of each.
        bbt_db_locations = [row for row in bbt_db if self.name.lower() in row[2].lower()]
        



class Onmyoji(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        try:
            self.create_classes()
        except FileNotFoundError:
            DriveAPI.get_gdrive_sheet_database()
            DriveAPI.generate_csv_databases()
            self.create_classes()

    async def has_permission(ctx):
        return ctx.author.id in owner_list or ctx.author.id in editor_list

    def create_classes(self):
        """Creates all the Shikigami classes with each of their vairables in a dictionary."""
        #Opens and creates the onmyoguide bounty db
        with open(config.onmyoguide_csv_db_file, newline='') as bounties:
            bounty_reader = csv.reader(bounties)
            for n in range(0, 3):
                next(bounty_reader) #skips the first 3 rows because its headers + message + example
            bounty_list = [row for row in bounty_reader]
        #Opens and creates the shikigami list from the full list of shikigami
        with open(config.bbt_csv_shikigami_list_file, newline='') as shiki_list_csv:
            shiki_list_reader = csv.reader(shiki_list_csv)
            next(shiki_list_reader) #skips header
            shiki_list = [row[0] for row in shiki_list_reader]
        #Opens the BBT-made database for all stages with all their contents.
        with open(config.bbt_csv_db_file, newline='') as bbt_db:
            bbt_db_reader = csv.reader(bbt_db)
            next(bbt_db_reader)
            bbt_db = [row for row in bbt_db_reader]
        self.shikigami_class = {row[0].lower(): Shikigami(row[0], bounty_list, bbt_db) for row in bounty_list}

    def shiki_found(self, shiki):
        """Returns a print message w/ the proper capitalized name of the Shikigami."""
        shiki_name = self.shikigami_class[shiki].name
        return f"I found the following Shikigami: **{shiki_name}**\nHere are their locations:\n--------------------"

    def location_finder(self, shiki):
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
    @commands.check(has_permission)
    async def download_shikigami_update(self, ctx):
        '''If Officer, updates the bot's local database file.'''
        await ctx.send("Now updating... Please wait while BathBot pulls the latest database.")
        DriveAPI.get_gdrive_sheet_database()
        await ctx.send("The Shikigami Bounty list has been successfully updated!")

    @commands.command()
    async def download_shikigami_update_excel(self, ctx):
        '''If Officer, updates the bot's local database file.'''
        await ctx.send("Now updating... Please wait while BathBot pulls the latest database.")
        DriveAPI.get_gdrive_sheet_database_excel()
        await ctx.send("The Shikigami Bounty list has been successfully updated!")

    @download_shikigami_update.error
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
                await ctx.send(self.shiki_found(shiki))
                await ctx.send(self.location_finder(shiki))
                return
            if search in self.shikigami_class[shiki].hints.lower():
                await ctx.send(self.shiki_found(shiki))
                await ctx.send(self.location_finder(shiki))
                return
            if search in self.shikigami_class[shiki].alias.lower():
                await ctx.send(self.shiki_found(shiki))
                await ctx.send(self.location_finder(shiki))
                return
        await ctx.send("For all my bath powers, I could not find your term, or something went wrong.")
        

def setup(bot):
    bot.add_cog(Onmyoji(bot))

