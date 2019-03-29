from discord.ext import commands
import sys
import config
import traceback

permission = 'You do not have permission to use this command.'
owner_list = config.owner_list

class Admin(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
    
	async def cog_check(self, ctx):
		return ctx.author.id in owner_list

	# Hidden means it won't show up on the default help.
	@commands.command(name='load', hidden=True)
	async def cog_load(self, ctx, *, cog: str):
		"""Command which Loads a Module.
		Remember to use dot path. e.g: cogs.owner"""
		try:
			self.bot.load_extension('cogs.'+cog)
		except Exception as e:
			await ctx.send(f'**ERROR:** {type(e).__name__} - {e}')
			traceback.print_exc()
		else:
			await ctx.send('**Success: **cogs.'+cog+' has been loaded!')

	@cog_load.error
	async def cog_load_error(self, ctx, error):
		if isinstance(error, commands.CheckFailure):
			await ctx.send(permission)


	@commands.command(name='unload', hidden=True)
	async def cog_unload(self, ctx, *, cog: str):
		"""Command which Unloads a Module.
		Remember to use dot path. e.g: cogs.owner"""
		try:
			self.bot.unload_extension('cogs.'+cog)
		except Exception as e:
			await ctx.send(f'**ERROR:** {type(e).__name__} - {e}')
		else:
			await ctx.send('**Success:** cogs.'+cog+' has been unloaded!')

	@cog_unload.error
	async def cog_unload_error(self, ctx, error):
		if isinstance(error, commands.CheckFailure):
			await ctx.send(permission)

	@commands.command(name='reload', hidden=True)
	async def cog_reload(self, ctx, *, cog: str):
		"""Command which Reloads a Module.
		Remember to use dot path. e.g: cogs.owner"""
		try:
			self.bot.unload_extension('cogs.'+cog)
			self.bot.load_extension('cogs.'+cog)
		except Exception as e:
			await ctx.send(f'**Error:** {type(e).__name__} - {e}')
			traceback.print_exc()
		else:
			await ctx.send('**Success:** cogs.'+cog+' has been reloaded!')

	@cog_reload.error
	async def cog_reload_error(self, ctx, error):
		if isinstance(error, commands.CheckFailure):
			await ctx.send(permission)

	@commands.command(name='kill', hidden=True)
	async def kill_bot(self, ctx):
		'''Kills the bot. Only useable by Zynro.'''
		await ctx.send("Well, it's time to take a bath. See you soon! \nBathBot is now exiting.")
		sys.exit()

	@kill_bot.error
	async def kill_error(ctx, error):
		if isinstance(error, commands.CheckFailure):
			await ctx.send(permission)

	
			
def setup(bot):
    bot.add_cog(Admin(bot))