import discord
from discord.ext import commands
import asyncio
import requests
import re
import sys
import io
import aiohttp
import traceback
import config
import os
import youtube_dl

youtube_dl.utils.bug_reports_message = lambda: ''

ytdl_format_options = {
	'format': 'bestaudio/best',
	'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
	'restrictfilenames': True,
	'noplaylist': True,
	'nocheckcertificate': True,
	'ignoreerrors': False,
	'logtostderr': False,
	'quiet': True,
	'no_warnings': True,
	'default_search': 'auto',
	'source_address': '0.0.0.0' # ipv6 addresses cause issues sometimes
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


class VoiceEntry:
	def __init__(self, message, player):
		self.requester = message.author
		self.channel = message.channel
		self.player = player

class Voice(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.voice_states = {}
		self.voicething = None

	async def is_owner(ctx):
		return ctx.author.id == owner

	def my_after():
		#coro = ctx.voice_client.disconnect()
		coro = self.voicething.disconnect()
		fut = asyncio.run_coroutine_threadsafe(coro, client.loop)
		try:
			fut.result()
		except:
			pass

	def get_voice_state(self, server):
		state = self.voice_states.get(server.id)
		if state is None:
			state = VoiceState(self.bot)
			self.voice_states[server.id] = state

		return state

	async def create_voice_client(self, channel):
		voice = await self.bot.join_voice_channel(channel)
		state = self.get_voice_state(channel.server)
		state.voice = voice

	def __unload(self):
		for state in self.voice_states.values():
			try:
				state.audio_player.cancel()
				if state.voice:
					self.bot.loop.create_task(state.voice.disconnect())
			except:
				pass


#	@commands.command()
#	async def loadopus(self, ctx):
#		if not discord.opus.is_loaded():
#			discord.opus.load_opus('libopus.so')
#			await ctx.send("Done.")

	@commands.command(pass_context=True, no_pm=True)
	async def join(self, ctx):
		"""Summons the bot to join your voice channel."""
		if ctx.voice_client is None:
			if ctx.author.voice.channel:
				await ctx.author.voice.channel.connect()
			else:
				return await ctx.send("Not connected to a voice channel.")

	@commands.command()
	async def play(self, ctx, *, query):
		"""Plays a file from the local filesystem. Currently broken."""
		if ctx.voice_client is None:
			if ctx.author.voice.channel:
				await ctx.author.voice.channel.connect()
			else:
				return await ctx.send("Not connected to a voice channel.")
		if ctx.voice_client.is_playing():
			ctx.voice_client.stop()
		self.voicething = ctx.voice_client
		await ctx.send(self.voicething)
		source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio('sfx/'+query+'.mp3'))
		ctx.voice_client.play(source, after=Voice.my_after)
		Voice.my_after()
		#await ctx.send('Now playing: {}'.format(query))

	#@play.after_invoke
	#async def after_play_command(self, ctx):
	#	await ctx.voice_client.disconnect()


	@commands.command()
	async def yt(self, ctx, *, url):
		"""Streams from a url (almost anything youtube_dl supports)"""
		if ctx.voice_client is None:
			if ctx.author.voice.channel:
				await ctx.author.voice.channel.connect()
			else:
				return await ctx.send("Not connected to a voice channel.")
		if ctx.voice_client.is_playing():
			ctx.voice_client.stop()
		
		if url is None:
			return await ctx.send('No URL specified.')
		player = await YTDLSource.from_url(url, loop=self.bot.loop)
		ctx.voice_client.play(player, after=lambda e: print('Player error: %s' % e) if e else None)
		await ctx.send('Now playing: {}'.format(player.title))
	
	#@commands.command()
	#async def volume(self, ctx, volume: int):
	#	"""Changes the player's volume"""
	#	if ctx.voice_client is None:
	#		return await ctx.send("Not connected to a voice channel.")
	#	ctx.voice_client.source.volume = volume
	#	await ctx.send("Changed volume to {}%".format(volume))

	@commands.command()
	async def stop(self, ctx):
		"""Stops and disconnects the bot from voice"""
		ctx.voice_client.stop()
		await ctx.voice_client.disconnect()

def setup(bot):
	bot.add_cog(Voice(bot)) 