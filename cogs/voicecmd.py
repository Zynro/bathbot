import discord
from discord.ext import commands
import asyncio
import requests
import re
import sys
import io
import aiohttp
import time
from datetime import datetime, timedelta
import traceback
import config
import os
from os.path import isfile, join
import youtube_dl

ytre = re.compile(r'youtube',re.IGNORECASE)

youtube_dl.utils.bug_reports_message = lambda: ''

ytdl_format_options = {
	'extract-audio': True,
	'format': 'bestaudio',
	'outtmpl': '~/THEBATH/sfx/yt_dl/%(extractor)s-%(id)s-%(title)s.%(ext)s',
	'restrictfilenames': True,
	'noplaylist': True,
	'nocheckcertificate': True,
	'ignoreerrors': False,
	'logtostderr': False,
	'quiet': False,
	'no_warnings': True,
	'default_search': 'auto_warning',
	'source_address': '0.0.0.0', # ipv6 addresses cause issues sometimes
	'maxfilesize': '300mb',
	'no_overwrites': True
}

ffmpeg_options = {
	'before_options': '-nostdin',
	'options': '-vn'
}



ytdl = youtube_dl.YoutubeDL(ytdl_format_options)


class YTDLSource(discord.PCMVolumeTransformer):
	def __init__(self, source, *, data, volume=0.5):
		super().__init__(source, volume)
		self.data = data
		self.title = data.get('title')
		self.url = data.get('url')

	@classmethod
	async def from_url(cls, url, *, loop=None):
		loop = loop or asyncio.get_event_loop()
		data = await loop.run_in_executor(None, ytdl.extract_info, url)
		if 'entries' in data:
			# take first item from a playlist
			data = data['entries'][0]

		filename = ytdl.prepare_filename(data)
		return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)


class VoiceCmd(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.voice_states = {}
		self.voicething = None


	@commands.command(no_pm=True)
	async def join(self, ctx):
		"""Summons the bot to join your voice channel."""
		if ctx.voice_client is None:
			if ctx.author.voice.channel:
				await ctx.author.voice.channel.connect()
			else:
				return await ctx.send("User is not connected to a voice channel.")

	@commands.command()
	async def play(self, ctx, *, query):
		"""Plays a file from the local filesystem."""
		try:
			if ctx.voice_client is None:
				if ctx.author.voice.channel:
					await ctx.author.voice.channel.connect()
				else:
					return await ctx.send("User is not connected to a voice channel.")
			self.voicething = ctx.voice_client
			def afterdc(error):
				coro = self.voicething.disconnect()
				fut = asyncio.run_coroutine_threadsafe(coro, self.bot.loop)
				try:
					fut.result()
				except:
					print('I errored.')
					pass
			if ctx.voice_client.is_playing():
				ctx.voice_client.stop()
				await asyncio.sleep(1.0)
			source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio('sfx/'+query+'.mp3'), volume=0.5)
			ctx.voice_client.play(source, after=afterdc)
			#await ctx.send('Now playing: {}'.format(query))
	
		except AttributeError:
			if ctx.voice_client.is_playing():
				ctx.voice_client.resume()
			else:
				if ctx.voice_client is None:
					if ctx.author.voice.channel:
						await ctx.author.voice.channel.connect()
					else:
						return await ctx.send("User is not connected to a voice channel.")
				self.voicething = ctx.voice_client
				def afterdc(error):
					coro = self.voicething.disconnect()
					fut = asyncio.run_coroutine_threadsafe(coro, self.bot.loop)
					try:
						fut.result()
					except:
						print('I errored.')
						pass
				if ctx.voice_client.is_playing():
					ctx.voice_client.stop()
					await asyncio.sleep(1.0)
				source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio('sfx/'+query+'.mp3'), volume=0.5)
				ctx.voice_client.play(source, after=afterdc)

	@commands.command()
	async def playlib(self, ctx):
		#musicfiles = [f for f in os.walk('./sfx') if isfile(join('.\sfx', str(f)))]
		musicfiles = ""
		for r,d,f in os.walk('./sfx'):
			for file in f:
				temp = join('.\\sfx', str(file))
				musicfiles = musicfiles + "\n" + temp
		await ctx.send(musicfiles)

	@commands.command(hidden = True)
	async def play_direct_no_ext(self, ctx, *, query):
		"""Plays a file from the local filesystem."""
		matchyt = ytre.search(query)
		try:
			if ctx.voice_client is None:
				if ctx.author.voice.channel:
					await ctx.author.voice.channel.connect()
				else:
					return await ctx.send("User is not connected to a voice channel.")
			self.voicething = ctx.voice_client
			def afterdc(error):
				coro = self.voicething.disconnect()
				fut = asyncio.run_coroutine_threadsafe(coro, self.bot.loop)
				try:
					fut.result()
				except:
					print('I errored.')
					pass
			if ctx.voice_client.is_playing():
				ctx.voice_client.stop()
				await asyncio.sleep(1.0)
			if matchyt:
				volvar = 0.17
			else:
				volvar = 0.5
			source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(query), volume=volvar)
			ctx.voice_client.play(source, after=afterdc)
			#await ctx.send('Now playing: {}'.format(query))
	
		except AttributeError:
			if ctx.voice_client is None:
				if ctx.author.voice.channel:
					await ctx.author.voice.channel.connect()
				else:
					return await ctx.send("User is not connected to a voice channel.")
			self.voicething = ctx.voice_client
			def afterdc(error):
				coro = self.voicething.disconnect()
				fut = asyncio.run_coroutine_threadsafe(coro, self.bot.loop)
				try:
					fut.result()
				except:
					print('I errored.')
					pass
			if ctx.voice_client.is_playing():
				ctx.voice_client.stop()
				await asyncio.sleep(1.0)
			if matchyt:
				volvar = 0.17
			else:
				volvar = 0.5
			source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(query), volume=volvar)
			ctx.voice_client.play(source, after=afterdc)


	@commands.command()
	async def yt(self, ctx, *, url):
		"""Streams from a url (almost anything youtube_dl supports)"""
		try:
			if ctx.voice_client is None:
				if ctx.author.voice.channel:
					pass
					await ctx.author.voice.channel.connect()
				else:
					return await ctx.send("User is not connected to a voice channel.")
			if ctx.voice_client.is_playing():
				ctx.voice_client.stop()
			self.voicething = ctx.voice_client
			def afterdc(error):
				coro = self.voicething.disconnect()
				fut = asyncio.run_coroutine_threadsafe(coro, self.bot.loop)
				try:
					fut.result()
				except:
					print('I errored.')
					pass
			if url is None:
				return await ctx.send('No URL specified.')
			player = await YTDLSource.from_url(url, loop=self.bot.loop)
			source = discord.PCMVolumeTransformer(player, volume=0.25)
			ctx.voice_client.play(source, after=afterdc)
			await ctx.send('Now playing: {}'.format(player.title))

		except AttributeError:
			if ctx.voice_client is None:
				if ctx.author.voice.channel:
					await ctx.author.voice.channel.connect()
				else:
					return await ctx.send("User is not connected to a voice channel.")
			if ctx.voice_client.is_playing():
				ctx.voice_client.stop()
			self.voicething = ctx.voice_client
			def afterdc(error):
				coro = self.voicething.disconnect()
				fut = asyncio.run_coroutine_threadsafe(coro, self.bot.loop)
				try:
					fut.result()
				except:
					print('I errored.')
					pass
			if url is None:
				return await ctx.send('No URL specified.')
			player = await YTDLSource.from_url(url, loop=self.bot.loop)
			source = discord.PCMVolumeTransformer(player, volume=0.25)
			ctx.voice_client.play(source, after=afterdc)
			await ctx.send('Now playing: {}'.format(player.title))
	
	@commands.command(name='volume', aliases=['vol'])
	async def volume_change(self, ctx, vol: float):
		"""Changes the player's volume"""

		if ctx.voice_client is None:
			return await ctx.send("Not connected to a voice channel.")
		if ctx.voice_client.is_playing():
			volume = vol / 100
			ctx.voice_client.source.volume = volume
			await ctx.send("Changed volume to {}%".format(vol))
		else:
			await ctx.send('Nothing is playing.')


	@commands.command(name='stop', aliases=['st'])
	async def stop_playback(self, ctx):
		"""Stops and disconnects the bot from a voice channel."""
		if ctx.voice_client is None:
				await ctx.send('Nothing is playing.')
		else:
			if ctx.voice_client.is_playing():
				ctx.voice_client.stop()
			await ctx.voice_client.disconnect()
			

	@commands.command(name='pause', aliases=['p'])
	async def pause_playback(self, ctx):
		if ctx.voice_client is None:
				await ctx.send('Nothing is playing.')
		else:
			if ctx.voice_client.is_playing():
				ctx.voice_client.pause()

	@commands.command(name='resume', aliases=['r'])
	async def resume_playback(self, ctx):
		if ctx.voice_client is None:
				await ctx.send('Nothing is playing.')
		else:
			ctx.voice_client.resume()
		
	@commands.command(hidden = True)
	async def vtest(self, ctx, test: float):
		#await ctx.send(ctx.voice_client.source.volume)
		test = test/100
		await ctx.send('f= '+str(test))
		#await ctx.send('Float= '+float(test))



	
def setup(bot):
	bot.add_cog(VoiceCmd(bot)) 