from discord.ext import commands
from discord import File
import json
import os.path
import io
import config
import requests
import shutil
import tweepy

def twitter_auth(type):
    path_to_file = f"tokens/twitter_credentials.json"
    try:
        with open(path_to_file, 'r') as file:
            tweepy_auth={}
            tweepy_auth = json.loads(file.read())
    except FileNotFoundError:
        print("Credentials file not found")
        return
    if type == 1:
        auth = tweepy.OAuthHandler(tweepy_auth['consumer_token'], tweepy_auth['consumer_secret'])
        auth.set_access_token(tweepy_authaccess_token, tweepy_authaccess_secret)
    elif type == 2:
        auth = tweepy.AppAuthHandler(tweepy_auth['consumer_token'], tweepy_auth['consumer_secret'])
    return auth

def extract_id(tweet_id):
    tweet_id = tweet_id.split('/')
    tweet_id_extracted = ""
    for char in tweet_id[-1]:
        if char.isdigit():
            tweet_id_extracted += char
        else:
            break
    """print("=========================")
    print("=========================")
    print(tweet_id_extracted)
    print("=========================")
    print("=========================")"""
    tweet_id_extracted = int(tweet_id_extracted)
    return tweet_id_extracted

def get_ext(path):
    return os.path.splitext(path)[1].strip().lower()

def get_user_id(user):
    return int("".join([x for x in user if x.isdigit()]))

class GuildCmd(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.tweepy_api = tweepy.API(twitter_auth(2))

    async def cog_check(self, ctx):
        return ctx.guild.id in self.bot.module_access["twitter"]

    @commands.Cog.listener()
    async def on_message (self, message):
        if message.guild.id not in self.bot.module_access["twitter"]:
            return
        if "twitter" in message.content and "http" in message.content:
            tweet_id = extract_id(message.content)
            tweet = self.tweepy_api.get_status(tweet_id, tweet_mode = "extended")
            #print(tweet.extended_entities)
            tweet_list = []
            for each in tweet.extended_entities['media']:
                tweet_list.append(each['media_url'])
            if len(tweet_list) == 1:
                return
            tweet_list.pop(0)
            await message.channel.send('\n'.join(tweet_list))

    @commands.command(name="dump")
    async def tweet_dump(self, ctx, arg):
        path_to_file = "tweet_dump.json"
        tweet_id = extract_id(arg)
        tweet = self.tweepy_api.get_status(tweet_id, tweet_mode = "extended")
        #tweet = self.tweepy_api.get_status(tweet_id)
        print(tweet)
        with open(path_to_file, 'w') as shard_file:
            json.dump(tweet._json, shard_file, indent=4)     




def setup(bot):
    bot.add_cog(GuildCmd(bot))