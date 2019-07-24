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
        auth.secure = True
        auth.set_access_token(tweepy_auth['access_token'], tweepy_auth['access_secret'])
    elif type == 2:
        print (tweepy_auth)
        return tweepy.AppAuthHandler(tweepy_auth['consumer_token'], tweepy_auth['consumer_secret'])

def get_ext(path):
    return os.path.splitext(path)[1].strip().lower()

def get_user_id(user):
    return int("".join([x for x in user if x.isdigit()]))

class GuildCmd(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        """
        path_to_file = f"tokens/twitter_credentials.json"
        try:
            with open(path_to_file, 'r') as file:
                tweepy_auth = json.loads(file.read())
        except FileNotFoundError:
            print("Credentials file not found")
            return
        auth = tweepy.OAuthHandler(tweepy_auth['consumer_token'], tweepy_auth['consumer_secret'])
        try:
            redirect_url = auth.get_authorization_url()
        except tweepy.TweepError:
            print('Error! Failed to get request token.')
        session.set('request_token', auth.request_token['oauth_token'])
        token = session.get('request_token')
        session.delete('request_token')
        auth.request_token = { 'oauth_token' : token,
                                 'oauth_token_secret' : verifier }

        try:
            auth.get_access_token(verifier)
        except tweepy.TweepError:
            print('Error! Failed to get access token.')"""
        auth = twitter_auth(1)
        api = tweepy.API(auth)
        for tweet in tweepy.Cursor(api.search, q='tweepy').items(10):
            print(tweet.text)
        for tweet in tweepy.api.statuses_lookup([759043035355312128]):
            print(tweet.text)



def setup(bot):
    bot.add_cog(GuildCmd(bot))