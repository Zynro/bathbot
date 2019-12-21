import discord
from discord.ext import commands
import config
from howlongtobeatpy import HowLongToBeat
import lib.misc_methods as MISC

hltb = HowLongToBeat
owner_list = config.owner_list


class Basic(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="purge", aliases=["prune", "wipe", "delete"])
    @commands.has_permissions(manage_messages=True)
    async def prune(self, ctx, amount: int = None):
        """
        Deletes the previous x amount of messages, including the prune command line.

        Parameters:
        amount (int): The amount of messages to prune
        """
        try:
            if not amount:
                return await ctx.send(
                    "You must enter an amount of messages to be deleted."
                )
            try:
                await ctx.channel.purge(limit=amount + 1)
            except Exception as e:
                await ctx.send(f"I failed to delete the messages.\n{e}")
        except TypeError:
            await ctx.send("Must be a whole number of an amount.")
        return

    @commands.command(name="hltb", aliases=["howlong"])
    async def how_long_to_beat(self, ctx, *, arg: str = None):
        """Searches the site How Long To Beat to see how long it takes to beat the game entered.

        Usage:
            &hltb game"""
        if not arg:
            await ctx.send("A game name must be entered.")
        results = await HowLongToBeat().async_search(arg)
        if not results:
            return await ctx.send(f"Game '{arg}' not found.")
        else:
            if len(results) > 0:
                game_result = max(results, key=lambda element: element.similarity)
                embed = discord.Embed(
                    title=f"HLTB: {game_result.game_name}",
                    colour=discord.Colour(MISC.generate_random_color()),
                    description=game_result.game_web_link,
                )
                embed.set_thumbnail(url=game_result.game_image_url)
                if game_result.gameplay_main_label:
                    embed.add_field(
                        name=game_result.gameplay_main_label,
                        value=f"{game_result.gameplay_main} Hours",
                        inline=False,
                    )
                if game_result.gameplay_main_extra_label:
                    embed.add_field(
                        name=game_result.gameplay_main_extra_label,
                        value=f"{game_result.gameplay_main_extra} Hours",
                        inline=False,
                    )
                if game_result.gameplay_completionist_label:
                    embed.add_field(
                        name=game_result.gameplay_completionist_label,
                        value=f"{game_result.gameplay_completionist} Hours",
                        inline=False,
                    )
                return await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Basic(bot))
