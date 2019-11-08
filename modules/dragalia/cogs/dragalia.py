import discord
from discord.ext import commands
import random
import aiosqlite
import sqlite3
from fuzzywuzzy import fuzz
from modules.dragalia.models.adventurer import Adventurer
from modules.dragalia.models.scrape_update import Update as ScrapeUpdate
from modules.dragalia.models.dps import DPS
import modules.dragalia.models.constants as CONSTANTS
import asyncio

DPS_URL_60 = "https://b1ueb1ues.github.io/dl-sim/60/data_kr.csv"
DPS_URL_120 = "https://b1ueb1ues.github.io/dl-sim/120/data_kr.csv"
DPS_URL_180 = "https://b1ueb1ues.github.io/dl-sim/180/data_kr.csv"

dragalia_elements = ["flame", "water", "wind", "light", "shadow"]
elements_images = {
    "flame": "https://b1ueb1ues.github.io//dl-sim/pic/element/flame.png",
    "water": "https://b1ueb1ues.github.io//dl-sim/pic/element/water.png",
    "wind": "https://b1ueb1ues.github.io//dl-sim/pic/element/wind.png",
    "light": "https://b1ueb1ues.github.io//dl-sim/pic/element/light.png",
    "shadow": "https://b1ueb1ues.github.io//dl-sim/pic/element/shadow.png",
    "all": "https://icon-library.net/images/muscle-icon-png/muscle-icon-png-24.jpg",
}


def generate_rand_color():
    return random.randint(0, 0xFFFFFF)


async def lev_dist_similar(a, b):
    return fuzz.partial_ratio(a.lower(), b.lower())


def strip_all(input_str):
    return "".join([x for x in input_str if x.isalpha()])


class Dragalia(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.module = self.bot.modules["dragalia"]

        self.MASTER_DB = f"{self.module.path}/lists/master.db"
        self.update = ScrapeUpdate(self.MASTER_DB)
        self.update.full_update()
        self.adven_db = self.create_names()
        self.dps_db_path = f"{self.module.path}/lists/optimal_dps_data"
        self.dps_csv = DPS.get_src_csv(self.dps_db_path)
        self.dps_db = DPS.build_dps_db(self.dps_csv)
        self.rank_db = DPS.build_rank_db(self.dps_db)

        # self.dps_rankings = self.create_rankings()
        # for character, value in self.adven_db.items():
        # self.adven_db[character].update_rank(self.dps_rankings)

        # pp = pprint.PrettyPrinter(indent=1)
        # pp.pprint(self.rank_db)
        # pp.pprint(self.adven_db["marth"].__dict__)

    async def cog_check(self, ctx):
        return ctx.guild.id in self.bot.module_access["dragalia"]

    def create_names(self):
        conn = sqlite3.connect(self.MASTER_DB)
        c = conn.cursor()
        try:
            c.execute("SELECT * from Adventurers LIMIT 1")
        except sqlite3.OperationalError:
            self.update.scrape(conn)
        try:
            c.execute("SELECT * from Skills LIMIT 1")
        except sqlite3.OperationalError:
            self.update.scrape(conn)
        c.row_factory = sqlite3.Row
        query = c.execute("SELECT * FROM Adventurers")
        results = query.fetchall()
        conn.close()
        adven_classes = {}
        for each in results:
            adven_classes[each["internal_name"]] = Adventurer(
                {"name": each["name"], "internal_name": each["internal_name"]}
            )
        return adven_classes

    async def async_create_names(self):
        async with aiosqlite.connect(self.MASTER_DB) as db:
            db.row_factory = aiosqlite.Row
            query = await db.execute("SELECT Internal_Name FROM Adventurers")
            results = query.fetchall()
        adven_classes = {}
        for each in results:
            adven_classes[each["internal_name"]] = {}
        return adven_classes

    async def query_adv(self, query):
        try:
            query = query.internal_name
        except AttributeError:
            pass
        try:
            adventurer = self.adven_db[query].element
            return self.adven_db[query]
        except (KeyError, AttributeError):
            adventurer = await self.generate_adven_class(query)
        return adventurer

    async def generate_adven_class(self, name):
        async with aiosqlite.connect(self.MASTER_DB) as db:
            db.row_factory = aiosqlite.Row
            c = await db.execute(
                "SELECT * FROM Adventurers WHERE Internal_Name=?", (name,)
            )
            adven_row = await c.fetchone()
            internal_name = adven_row["internal_name"]
            c = await db.execute(
                "SELECT * FROM Skills WHERE Owner=?", (adven_row["name"],)
            )
            skills = await c.fetchall()
            dps_dict = self.dps_db[internal_name]
            adventurer = self.adven_db[internal_name] = Adventurer(
                adven_row, skills, dps_dict, self.rank_db
            )
        return adventurer

    async def adven_validate(self, adven_input):
        adven_input = adven_input.lower()
        adven_results = []
        high_score_name = 0
        high_score_i_name = 0
        for adven in self.adven_db.keys():
            adven = self.adven_db[adven]
            temp_score_name = await lev_dist_similar(adven_input, adven.name.lower())
            temp_score_i_name = await lev_dist_similar(
                adven_input, adven.internal_name.lower()
            )
            if temp_score_name == 100 or temp_score_i_name == 100:
                return [adven.internal_name]
            if temp_score_name > high_score_name:
                high_score_name = temp_score_name
            if temp_score_i_name > high_score_i_name:
                high_score_i_name = temp_score_i_name
        for adven in self.adven_db.keys():
            adven = self.adven_db[adven]
            name_score = await lev_dist_similar(adven_input, adven.name.lower())
            i_name_score = await lev_dist_similar(
                adven_input, adven.internal_name.lower()
            )
            if high_score_name - 5 <= name_score <= high_score_name + 5:
                adven_results.append(adven.internal_name)
            if high_score_i_name - 5 <= i_name_score <= high_score_i_name + 5:
                adven_results.append(adven.internal_name)
        return list(set(adven_results))

    async def return_multiple_results(self, multiple_results):
        char_result_list = []
        for each in multiple_results:
            char_result_list.append(each.internal_name)
        char_result_list = "\n".join(char_result_list)
        embed = discord.Embed(
            title="I found multiple results for your search:",
            colour=discord.Colour(generate_rand_color()),
            description=char_result_list,
        )
        embed.set_footer(text="Try your search again" " with a adventurer specified.")
        return embed

    async def proccess_parse_change(self, parse, embed, reaction, user):
        if reaction.emoji == CONSTANTS.emoji["up_arrow"]:
            if "60" in embed.description:
                parse = "120"
                await reaction.remove(user)
                await reaction.message.add_reaction(CONSTANTS.emoji["down_arrow"])
            elif "120" in embed.description:
                parse = "180"
                await reaction.remove(user)
                await reaction.remove(self.bot.user)

        elif reaction.emoji == CONSTANTS.emoji["down_arrow"]:
            if "180" in embed.description:
                parse = "120"
                await reaction.remove(user)
                await reaction.message.add_reaction(CONSTANTS.emoji["up_arrow"])
            if "120" in embed.description:
                parse = "60"
                await reaction.remove(user)
                await reaction.remove(self.bot.user)
        return parse

    @commands.group(aliases=["drag", "d"])
    async def dragalia(self, ctx):
        """
        The Dragalia Lost command group.

        Aliases:
            [drag/d]
        Subcommands:
            [dps]
                Retreive DPS Simulator data for a single character for parses
                of 60, 120, and 180 seconds.
            [rank/ranking/rankings]
                Retreive a list of top ten Adventurers based on the DPS
                Simulator for an element, or overall.
        """
        if not ctx.invoked_subcommand:
            return

    @dragalia.command()
    async def query(self, ctx, data=None, *, character: str = None):
        if not data:
            return await ctx.send("Need query type.")
        if data == "1":
            adven = await self.query_adv(character)
            # pp = pprint.PrettyPrinter(indent=1)
            # pp.pprint(self.adven_db["zardin"].__dict__)
            return await ctx.send(embed=adven.dps.embed())
        elif data == "2":
            adven = await self.query_adv(character)
            return await ctx.send(embed=adven.embed())

    @dragalia.command()
    async def dps(self, ctx, *, character: str = None):
        """
        Retreive DPS Simulator data for a single character for parses of 60,
        120, and 180 seconds.

        Usage:
            &[drag/d] dps <character>
        """
        if not character:
            return await ctx.send("A character must be entered to search the database.")
        character = character.lower().strip()
        matched_list = await self.adven_validate(character)
        if matched_list:
            if len(matched_list) > 1:
                return await ctx.send(
                    embed=await self.return_multiple_results(matched_list)
                )
            else:
                parse = "180"
                adven = await self.query_adv(matched_list[0])
                message = await ctx.send(embed=adven.dps.embed(parse))
                await message.add_reaction(CONSTANTS.emoji["down_arrow"])

                def check_response(reaction, user):
                    return (
                        (
                            reaction.emoji == CONSTANTS.emoji["up_arrow"]
                            or reaction.emoji == CONSTANTS.emoji["down_arrow"]
                        )
                        and user != self.bot.user
                        and message.id == reaction.message.id
                    )

                while True:
                    try:
                        reaction, user = await self.bot.wait_for(
                            "reaction_add", timeout=120.0, check=check_response
                        )
                    except asyncio.TimeoutError:
                        return
                    else:
                        embed = reaction.message.embeds[0]
                        parse = await self.proccess_parse_change(
                            parse, embed, reaction, user
                        )
                        await reaction.message.edit(embed=adven.dps.embed(parse))

        else:
            return await ctx.send(
                "Either no adventurer was found, or an error occured."
            )

    async def return_rankings_embed(self, element, parse):
        if element:
            for each in dragalia_elements:
                if element.lower().strip() in each:
                    element = each
                    embed = discord.Embed(
                        title=(f"**{element.title()} Top 10 Rankings**"),
                        description=f"*Parse: {parse} Seconds*",
                        colour=discord.Colour(generate_rand_color()),
                    )
                    break
        else:
            element = "all"
            embed = discord.Embed(
                title=f"**All Elements Top 10 Rankings**",
                description=f"*Parse: {parse} Seconds*",
                colour=discord.Colour(generate_rand_color()),
            )
        name_string = ""
        dps_string = ""
        x = 1
        for entry in self.dps_rankings[parse][element]:
            if x == 11:
                break
            char = self.adventurer_db[entry]
            name = f"{x}. {char.internal_name}"
            name_string += f"{name}\n"
            dps_string += f"{char.parse[parse].dps}\n"
            x += 1
        embed.add_field(name=f"**Adventurer**", value=name_string, inline=True)
        embed.add_field(name=f"**DPS**", value=dps_string, inline=True)
        embed.set_thumbnail(url=elements_images[element])
        embed.set_footer(
            text=("Use the up/down arrows to increase or decrease parse time.")
        )
        return embed

    @dragalia.command(name="rankings", aliases=["rank", "ranks", "ranking"])
    async def rankings(self, ctx, element=None):
        """
        Retreive a list of top ten Adventurers based on the DPS Simulator for
        an element, or overall.

        Usage:
            &[drag/d] [rank/ranking/rankings] <element>

        Element can be any element, or 'all' for overall top 10 list.
        """
        parse = "180"
        embed = await self.return_rankings_embed(element=element, parse=parse)
        message = await ctx.send(embed=embed)
        await message.add_reaction(CONSTANTS.emoji.down_arrow)

        def check_response(reaction, user):
            return (
                (
                    reaction.emoji == CONSTANTS.emoji.up_arrow
                    or reaction.emoji == CONSTANTS.emoji.down_arrow
                )
                and user != self.bot.user
                and message.id == reaction.message.id
            )

        while True:
            try:
                reaction, user = await self.bot.wait_for(
                    "reaction_add", timeout=120.0, check=check_response
                )
            except asyncio.TimeoutError:
                return
            else:
                embed = reaction.message.embeds[0]
                parse = await self.proccess_parse_change(parse, embed, reaction, user)
                element = reaction.message.embeds[0].title.split(" ")[0]
                element = strip_all(element.lower().strip())
                if element not in dragalia_elements:
                    element = None
                await reaction.message.edit(
                    embed=await self.return_rankings_embed(element=element, parse=parse)
                )

    @dragalia.command(
        name="print-get", aliases=["printdownload", "print-update", "update"]
    )
    @commands.cooldown(rate=1, per=60.00, type=commands.BucketType.default)
    async def update_draglia_data(self, ctx):
        await ctx.send(
            "Bathbot is now retreiving the DPS Simulator numbers"
            " from source, please wait..."
        )
        try:
            char_dict = self.build_adven_db(
                await self.async_get_src_csv(self.path_to_csv_file)
            )
            self.adventurer_db = self.create_classes(char_dict)
            self.dps_rankings = self.create_rankings()
            for character, value in self.adventurer_db.items():
                self.adventurer_db[character].update_rank(self.dps_rankings)
        except Exception as e:
            print(e)
            return await ctx.send(f"Update failed: {e}")
        await ctx.send("Update complete!")
        return


def setup(bot):
    bot.add_cog(Dragalia(bot))
