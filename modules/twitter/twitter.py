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

class GuildCmd(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.tweepy_api = tweepy.API(twitter_auth(2))

    async def cog_check(self, ctx):
        return ctx.guild.id in self.bot.module_access["twitter"]

    def check_tweet_for_embedded_links(self, tweet_link):
        tweet_id = extract_id(tweet_link)
        tweet = self.tweepy_api.get_status(tweet_id, tweet_mode = "extended")
        for each in tweet._json['entities']['urls']:
            print(each)
            if 'http' in each['expanded_url'] and 'twitter' in each['expanded_url']:
                return each['expanded_url']
        return None

    def get_tweet(self, tweet_id):
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
            return

    @commands.Cog.listener()
    async def on_message (self, message):
        if message.author == self.bot.user:
            return
        if message.guild.id not in self.bot.module_access["twitter"]:
            return
        split = message.content.split(" ")
        for each in split:
            if ("http" in each and "twitter" in each) or ("t.co" in each):
                split = each
                print(split)
        if "t.co" in split:
            async with aiohttp.ClientSession() as session:
                async with session.get(split) as response:
                    true_url = str(response.url)
                    if "twitter" in true_url and "http" in true_url:
                        tweet_id = extract_id(true_url)
                        tweet_author = self.get_tweet_author(true_url)
                        true_url = f"http://twitter.com/{tweet_author}/status/{tweet_id}"
                        embedded_link = self.check_tweet_for_embedded_links(true_url)
                        await message.channel.send(true_url)
                        if self.get_media_urls(true_url):
                            await message.channel.send(self.get_media_urls(true_url)) 
                        if embedded_link:
                            return await message.channel.send(embedded_link)
                    else:
                        return
        if "twitter" in split and "http" in split:
            result_message = self.get_media_urls(split)
            embedded_link = self.check_tweet_for_embedded_links(split)
            if result_message:
                await message.channel.send(result_message)
            if embedded_link:
                await message.channel.send(embedded_link)
            return
            """if not result_message and not embedded_link:
                return
            elif not embedded_link:
                return await message.channel.send(result_message)
            elif not result_message:
                return await message.channel.send(embedded_link)
            else:
                await message.channel.send(result_message)
                await message.channel.send(embedded_link)"""

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