from __future__ import print_function
import os.path
from googleapiclient.discovery import build
from googleapiclient.http import *
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2 import service_account
import io
import csv
import discord
import json
from discord.ext import commands
import config

SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
SERVICE_ACCOUNT_FILE = 'bbt_credentials.json'

credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)

drive_service = build('drive', 'v3', credentials = credentials)

class Test(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def csvtest(self, ctx):
        file_id = config.bounty_file_id
        request = drive_service.files().export_media(fileId=file_id,
                                                     mimeType='text/csv')

        buffer_file = io.BytesIO()
        downloader = MediaIoBaseDownload(buffer_file, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
            print ("Download %d%%." % int(status.progress() * 100))
        with open ('lists/onmyo.csv', 'wb') as f:
            f.write(buffer_file.getvalue())

        with open('lists/onmyo.csv', newline='') as file:
            reader = csv.reader(file)
            for row in reader:
                await ctx.send(row)
                return

def setup(bot):
    bot.add_cog(Test(bot))