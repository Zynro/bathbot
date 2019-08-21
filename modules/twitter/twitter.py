from discord.ext import commands
from discord import File
import json
import os.path
import io
import config
import requests
import shutil
import tweepy
import aiohttp

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
    tweet_id = str(tweet_id)
    tweet_id_list = tweet_id.split('/')
    tweet_id_extracted = ""
    index = 0
    for each in tweet_id_list:
        if "status" in each:
            tweet_id = tweet_id_list[index+1]
            break
        else:
            index += 1 
            continue
    for char in tweet_id:
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

class Twitter(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.tweepy_api = tweepy.API(twitter_auth(2))

    async def cog_check(self, ctx):
        return ctx.guild.id in self.bot.module_access["twitter"]

    def check_tweet_for_embedded_links(self, tweet_link):
        tweet_id = extract_id(tweet_link)
        tweet = self.tweepy_api.get_status(tweet_id, tweet_mode = "extended")
        try:
            return_quote = tweet._json['quoted_status_permalink']['expanded']
            return return_quote
        except KeyError:
            return None

    def get_tweet(self, tweet_id):
        try:
            if "http" in tweet_id:
                tweet_id = extract_id(tweet_id)
        except TypeError:
            pass
        return self.tweepy_api.get_status(tweet_id, tweet_mode = "extended")

    def get_tweet_author(self, string):
        return self.get_tweet(extract_id(string)).user._json['screen_name']

    def get_media_urls(self, message):
        tweet = self.get_tweet(extract_id(message))
        tweet_list = []
        try:
            for each in tweet.extended_entities['media']:
                tweet_list.append(each['media_url'])
            if len(tweet_list) == 1:
                return
            tweet_list.pop(0)
            return '\n'.join(tweet_list)
        except AttributeError:
            return None

    @commands.Cog.listener()
    async def on_message (self, message):
        if message.author == self.bot.user:
            return
        if message.guild.id not in self.bot.module_access["twitter"]:
            return
        split = message.content.split(" ")
        true_url = None
        for each in split:
            if (("http" in each and "twitter" in each) or ("t.co" in each)):
                true_url = each
                break
            if "t.co" in split:
                async with aiohttp.ClientSession() as session:
                    async with session.get(split) as response:
                        true_url = str(response.url)
                        break
        if not true_url:
            return
        tweet = self.get_tweet(true_url)
        while True:
            tweet_id = tweet._json['id']
            media_urls = self.get_media_urls(tweet_id)
            if media_urls:
                await message.channel.send(media_urls)
            quote_url = self.check_tweet_for_embedded_links(tweet_id)
            if quote_url:
                await message.channel.send(quote_url)
                tweet = self.get_tweet(quote_url)
            else:
                break
                return

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
    bot.add_cog(Twitter(bot))