import discord
from discord.ext import commands
import random


def generate_rand_color():
    return random.randint(0, 0xFFFFFF)


def roll_dice(amount: int, dice: int):
    return [random.randint(1, dice) for x in range(1, amount + 1)]


class Dice(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="roll")
    async def roll(self, ctx, *, string):
        final_rolls = []
        roll_list = string.split("+")
        for each in roll_list:
            dice_split = each.split("d")
            amount = int(dice_split[0].strip())
            dice = int(dice_split[1].strip())
            final_rolls.append(roll_dice(amount, dice))

        embed = discord.Embed(
            title=f"**`{string}`**", description=f" ", color=generate_rand_color()
        )
        for index, each in enumerate(final_rolls):
            total = sum(each)
            embed.add_field(
                name=f"**__{roll_list[index]}__**",
                value=f"{', '.join([str(x) for x in each])}\n" f"Total: **{total}**",
                inline=False,
            )
        final_total = sum([i for sub in final_rolls for i in sub])
        embed.add_field(name="**__Final Total__**", value=final_total, inline=False)
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Dice(bot))
