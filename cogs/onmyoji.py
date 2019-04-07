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
    return f'**{text}**'

def lower_and_underscore(text):
    """Lowers entire string and replaces all whitespace with underscores."""
    return text.lower().replace(' ', '_')

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
        self.name = input_name
        self.alias = self.hints = self.locations = self.icon_name = self.icon = None
        self.icon_name = f"{lower_and_underscore(self.name)}.png"
        self.icon = f"{config.shikigami_icon_location}/{self.icon_name}"
        for row in onmyoguide_db:
            #need to re-do, uses only shiki from onmyoguide
            shiki_name, alias, hints, locations = row[0], row[1], row[2], row[3]
            if input_name in shiki_name:
                self.alias = [other_name.lower() for other_name in alias.split('\n')]
                self.hints = hints
                self.locations = locations.split('\n')
                break

        bbt_database_raw_locations = []
        for row in bbt_db:
            if self.name.lower() in row[2].lower():
                contains = row[2].split('\n')
                temp_list = []
                temp_list.append(row[0])
                temp_list.append(row[1])
                for each in contains:
                    if self.name.lower() in each.lower():
                        temp_list.append(each)
                        break
                bbt_database_raw_locations.append(temp_list)
        if len(bbt_database_raw_locations) != 0:
            self.bbt_locations = sorted(self.generate_bbt_locations(bbt_database_raw_locations))
        else:
            self.bbt_locations = 'None found in database.'
        if not self.alias: self.alias=''
        if not self.hints: self.hints=''
        if not self.locations: self.locations='None found in database.'

    def generate_bbt_locations(self, bbt_database_raw_locations):
        """Generates the BBT Database list of locations"""
        #If no locations, end and return none.
        if len(bbt_database_raw_locations)==0:
            return None
        main_sub_and_shiki_list = []
        for row in bbt_database_raw_locations:
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
            shikigami_full_list = [row[0] for row in shiki_list_reader]
        #Opens the BBT-made database for all stages with all their contents.
        with open(config.bbt_csv_db_file, newline='') as bbt_db:
            bbt_db_reader = csv.reader(bbt_db)
            for i in range(0,6):
                next(bbt_db_reader)
            bbt_db = [row for row in bbt_db_reader]
        self.shikigami_class = {shiki.lower(): Shikigami(shiki, bounty_list, bbt_db) for shiki in shikigami_full_list}

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

    def shiki_bounty_embed(self, shiki):
        color = random.randint(0, 0xFFFFFF)
        icon = discord.File(self.shikigami_class[shiki].icon, filename = self.shikigami_class[shiki].icon_name)

        embed = discord.Embed(title=f"__**{self.shikigami_class[shiki].name}**__", colour=discord.Colour(color), description="Here are the bounty locations for this Shikigami:")
        embed.set_thumbnail(url=f"attachment://{self.shikigami_class[shiki].icon_name}")

        embed.add_field(name="OnmyoGuide Bounty Locations (Probably Outdated):", value=self.location_finder(shiki))

        if "None" not in self.shikigami_class[shiki].bbt_locations:
            all_locations = []
            for main in self.shikigami_class[shiki].bbt_locations:
                sub_locs = ', '.join(main[1])
                all_locations.append(f'{bold(main[0])} - {sub_locs}')
            all_locations = '\n'.join(all_locations)
            embed.add_field(name="BBT-Databased Bounty Locations:", value=all_locations)
        else:
            embed.add_field(name="BBT-Databased Bounty Locations:", value='None found in database.')
        return embed, icon

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
        

def setup(bot):
    bot.add_cog(Onmyoji(bot))

