import discord
import json
from discord.ext import commands


with open('lists/bounty.json') as file:
    bounty_json = json.loads(file.read())

with open('lists/stats.json') as file:
    stats_json = json.loads(file.read())


class Onmyoji(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def shikistats(self, ctx, *search):
        name = ' '.join([term.lower() for term in search])
        result = stats_json.get(name)
        if not result:
            fuzzy_name = [key for key in stats_json.keys() if name in key]
            if fuzzy_name:
                result = stats_json.get(fuzzy_name[0])
        if result:
            await ctx.send(f"""The stats for {name.title()} at level 40 are:
            **ATK:** _{result['attack']}_
            **HP:** _{result['health']}_
            **DEF:** _{result['defense']}_
            **SPD:** _{result['speed']}_
            **CRIT:** _{result['crit']}_
            **CDMG:** _{result['crit dmg']}_
            **EHIT:** _{result['eff hit']}_
            **ERES:** _{result['eff res']}_""")
            return
        await ctx.send(f'Couldn\'t find stats for {name.title()}')

    @commands.command()    
    async def bounty(self, ctx, *search):
        search = ' '.join([term.lower() for term in search])
        for item in bounty_json:
            if (
                item['name'].lower() == search or
                search in [hint.lower() for hint in item['hints']]
                ):
                locations = '\n '.join([location for location in item["locations"]])
                await ctx.send(f'I found a result for: {item["name"]}\n You should go to:\n {locations}')
                return
        print(ctx)
        await ctx.send('I, for all of my bath powers, could not find that bounty.')

        

def setup(bot):
    bot.add_cog(Onmyoji(bot))

