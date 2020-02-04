import discord
from discord.ext import commands
import aiosqlite
import sqlite3
from fuzzywuzzy import fuzz
from modules.dragalia.models.adventurer import Adventurer
from modules.dragalia.models.wyrmprint import Wyrmprint
from modules.dragalia.models.scrape_update import Update as ScrapeUpdate
from modules.dragalia.models.dps import DPS

# from modules.dragalia.models.ranking import Ranking
import modules.dragalia.models.constants as CONST
import lib.misc_methods as MISC
import asyncio
import traceback
import json

dragalia_elements = {
    "flame": "flame",
    "fire": "flame",
    "water": "water",
    "wind": "wind",
    "light": "light",
    "shadow": "shadow",
    "dark": "shadow",
}
elements_images = {
    "flame": "https://b1ueb1ues.github.io//dl-sim/pic/element/flame.png",
    "water": "https://b1ueb1ues.github.io//dl-sim/pic/element/water.png",
    "wind": "https://b1ueb1ues.github.io//dl-sim/pic/element/wind.png",
    "light": "https://b1ueb1ues.github.io//dl-sim/pic/element/light.png",
    "shadow": "https://b1ueb1ues.github.io//dl-sim/pic/element/shadow.png",
    "all": "https://icon-library.net/images/muscle-icon-png/muscle-icon-png-24.jpg",
}


def lev_dist_similar(a, b):
    return fuzz.ratio(a.lower().strip(), b.lower().strip())


def lev_dist_partial(a, b):
    return fuzz.partial_ratio(a.lower().strip(), b.lower().strip())


def strip_all(input_str):
    return "".join([x for x in input_str if x.isalpha()])


class Dragalia(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.module = self.bot.modules["dragalia"]

        self.MASTER_DB = f"modules/{self.module.path}/lists/master.db"
        self.update = ScrapeUpdate(self.bot.session, self.MASTER_DB)
        self.update.full_update()

        self.dps_db_path = f"modules/{self.module.path}/lists/dps"
        self.dps_db = DPS.pull_csvs(self.dps_db_path)
        try:
            with open(f"modules/{self.module.path}/lists/dps_hash.json") as file:
                self.dps_hash = json.loads(file.read())
        except FileNotFoundError:
            self.dps_hash = DPS.update_master_hash()

        self.rank_db = DPS.gen_ranks(self.dps_db)

        self.adven_db = self.create_names("Adventurers")
        self.wp_db = self.create_names("Wyrmprints")

    async def cog_check(self, ctx):
        return ctx.guild.id in self.bot.module_access["dragalia"]

    async def dps_update_check(self, ctx):
        current = MISC.get_master_hash(CONST.REPO_URL)
        if self.dps_hash != current:
            embed = discord.Embed(
                title="There are updates available for the the DPS records.",
                description="Please wait while the updater is called...",
            )
            await ctx.send(embed=embed)
            command = self.bot.get_command("dragalia update")
            await ctx.invoke(command, tables="dps")
        return

    def create_names(self, table):
        with sqlite3.connect(self.MASTER_DB) as conn:
            c = conn.cursor()
            try:
                c.execute("SELECT * from Adventurers LIMIT 1")
            except sqlite3.OperationalError:
                self.update.full_update()
            try:
                c.execute("SELECT * from Skills LIMIT 1")
            except sqlite3.OperationalError:
                self.update.full_update()
            c.row_factory = sqlite3.Row
            query_string = f"SELECT * FROM {table}"
            query = c.execute(query_string)
            results = query.fetchall()
        return self.parse_name_results(table, results)

    async def async_create_names(self, table):
        async with aiosqlite.connect(self.MASTER_DB) as db:
            db.row_factory = aiosqlite.Row
            query_string = f"SELECT * FROM {table}"
            async with db.execute(query_string) as query:
                results = await query.fetchall()
        return self.parse_name_results(table, results)

    def parse_name_results(self, table, results):
        if table == "Adventurers":
            names = {
                each["internal_name"].lower(): Adventurer(
                    each["name"], each["internal_name"]
                )
                for each in results
            }
        elif table == "Wyrmprints":
            names = {each["name"].lower(): Wyrmprint(each["name"]) for each in results}
        return names

    async def query_dict(self, query, db):
        try:
            query = query.internal_name
        except AttributeError:
            query = query.name
        try:
            query.max_hp
        except (KeyError, AttributeError):
            result = await self.generate_queried_class(query, db)
        else:
            return db[query]
        return result

    async def generate_queried_class(self, name, db_dict):
        async with aiosqlite.connect(self.MASTER_DB) as db:
            db.row_factory = aiosqlite.Row
            if MISC.get_dict_type(db_dict, Adventurer):
                async with db.execute(
                    "SELECT * FROM Adventurers WHERE Internal_Name=?", (name,)
                ) as c:
                    adven_row = await c.fetchone()
                    internal_name = adven_row["internal_name"]
                async with db.execute(
                    "SELECT * FROM Skills WHERE Owner=?", (adven_row["name"],)
                ) as c:
                    skills = await c.fetchall()
                adven = self.adven_db[internal_name]
                adven.update(adven_row, skills, self.dps_db, self.rank_db)
                return adven
            elif MISC.get_dict_type(db_dict, Wyrmprint):
                async with db.execute(
                    "SELECT * FROM Wyrmprints WHERE Name=?", (name,)
                ) as c:
                    wp_row = await c.fetchone()
                wp = self.wp_db[wp_row["name"]]
                wp.update(wp_row)
                return wp

    async def validate_query(self, query, db):
        if '"' in query:
            query.replace('"', "")
            try:
                return db[query.lower().strip()]
            except KeyError:
                return None
        query.replace('"', "")
        query = query.lower()
        results = []
        high_score_name = 0
        high_score_i_name = 0
        for term in db.keys():
            term = db[term]
            if MISC.get_dict_type(db, Adventurer):
                temp_score_name = lev_dist_similar(query, term.name.lower())
            elif MISC.get_dict_type(db, Wyrmprint):
                temp_score_name = lev_dist_partial(query, term.name.lower())
            if temp_score_name > high_score_name:
                high_score_name = temp_score_name
            try:
                temp_score_i_name = lev_dist_similar(query, term.internal_name.lower())
                if temp_score_i_name > high_score_i_name:
                    high_score_i_name = temp_score_i_name
            except AttributeError:
                # If object has no internal name
                pass
        for term in db.keys():
            term = db[term]
            if MISC.get_dict_type(db, Adventurer):
                name_score = lev_dist_similar(query, term.name.lower())
            elif MISC.get_dict_type(db, Wyrmprint):
                name_score = lev_dist_partial(query, term.name.lower())
            try:
                if MISC.get_dict_type(db, Adventurer):
                    i_name_score = lev_dist_similar(query, term.internal_name.lower())
                elif MISC.get_dict_type(db, Wyrmprint):
                    i_name_score = lev_dist_partial(query, term.internal_name.lower())
            except AttributeError:
                # If object has no internal name
                i_name_score = None
            if high_score_name == 100 or high_score_i_name == 100:
                if i_name_score == 100:
                    return [term]
                if name_score == 100 or i_name_score == 100:
                    results.append(term)
            else:
                if high_score_name - 5 <= name_score <= high_score_name + 5:
                    results.append(term)
                if i_name_score:
                    if high_score_i_name - 5 <= i_name_score <= high_score_i_name + 5:
                        results.append(term)
        return list(set(results))

    async def return_multiple_results(self, multiple_results):
        char_result_list = []
        for each in multiple_results:
            temp = f"{each.name}"
            try:
                temp = f" / {each.internal_name}"
            except AttributeError:
                pass
            char_result_list.append(temp)
        char_result_list = "\n".join(char_result_list)
        embed = discord.Embed(
            title="I found multiple results for your search:",
            colour=discord.Colour(MISC.rand_color()),
            description=char_result_list,
        )
        embed.set_footer(text="Try your search again with a more exact name.")
        return embed

    async def proccess_parse_change(
        self, embed=None, reaction=None, user=None, parse=None
    ):
        message = reaction.message
        if reaction.emoji == CONST.emoji["up_arrow"]:
            await reaction.remove(user)
            if "60" in embed.description:
                parse = "120"
                await message.add_reaction(CONST.emoji["down_arrow"])
                return parse
            elif "120" in embed.description:
                parse = "180"
                await reaction.remove(self.bot.user)
                return parse

        elif reaction.emoji == CONST.emoji["down_arrow"]:
            await reaction.remove(user)
            if "180" in embed.description:
                parse = "120"
                await message.add_reaction(CONST.emoji["up_arrow"])
                return parse
            if "120" in embed.description:
                parse = "60"
                await reaction.remove(self.bot.user)
                return parse

        elif reaction.emoji == CONST.emoji["star"]:
            await reaction.remove(user)
            if "parse" in embed.description.lower():
                await message.remove_reaction(CONST.emoji["down_arrow"], self.bot.user)
                await message.remove_reaction(CONST.emoji["up_arrow"], self.bot.user)
                return "adv"
            else:
                await message.add_reaction(CONST.emoji["down_arrow"])
                return "180"

    async def adven_profile_process(self, ctx, message, adven, parse="180"):
        def check_response(reaction, user):
            return (
                (
                    reaction.emoji == CONST.emoji["up_arrow"]
                    or reaction.emoji == CONST.emoji["down_arrow"]
                    or reaction.emoji == CONST.emoji["star"]
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
                return await message.clear_reactions()
            else:
                embed = reaction.message.embeds[0]
                parse = await self.proccess_parse_change(
                    embed=embed, reaction=reaction, user=user, parse=parse
                )
                if parse == "adv":
                    await reaction.message.edit(embed=adven.embed())
                else:
                    await reaction.message.edit(embed=adven.dps.embed(parse, "none"))

    @commands.group(name="dragalia", aliases=["drag", "d"])
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

    @dragalia.command(name="adv", aliases=["a", "adven"])
    async def adventurer_lookup(self, ctx, *, adven: str = None):
        if not adven:
            return await ctx.send("An query must be entered to search the database.")
        adven = adven.lower().strip()
        matched_list = await self.validate_query(adven, self.adven_db)
        if matched_list:
            if len(matched_list) > 1:
                return await ctx.send(
                    embed=await self.return_multiple_results(matched_list)
                )
            else:
                adven = await self.query_dict(matched_list[0], self.adven_db)
                message = await ctx.send(embed=adven.embed())
                await message.add_reaction(CONST.emoji["star"])
                await self.adven_profile_process(ctx, message, adven)
        else:
            return await ctx.send(
                f"Either the adventurer {adven} was not found, or an error occured."
            )

    @dragalia.command(name="wp")
    async def wyrmprint_lookup(self, ctx, *, wp):
        if not wp:
            return await ctx.send("An query must be entered to search the database.")
        wp = wp.lower().strip()
        matched_list = await self.validate_query(wp, self.wp_db)
        if matched_list:
            if len(matched_list) > 1:
                return await ctx.send(
                    embed=await self.return_multiple_results(matched_list)
                )
            else:
                wp = await self.query_dict(matched_list[0], self.wp_db)
                return await ctx.send(embed=wp.embed())
                """
                await message.add_reaction(CONST.emoji["star"])
                await self.adven_profile_process(ctx, message, adven)
                """
        else:
            return await ctx.send(
                f"Either the wyrmprint {wp} was not found, or an error occured."
            )
        return

    @dragalia.command()
    async def dps(self, ctx, *, adven: str = None):
        """
        Retreive DPS Simulator data for a single character for parses of 60,
        120, and 180 seconds.

        Usage:
            &[drag/d] dps <character>
        """
        coabs = "none"
        if not adven:
            return await ctx.send(
                "An adventurer must be entered to search the database."
            )

        await self.dps_update_check(ctx)

        adven = adven.lower().strip()
        matched_list = await self.validate_query(adven, self.adven_db)
        if matched_list:
            if len(matched_list) > 1:
                return await ctx.send(
                    embed=await self.return_multiple_results(matched_list)
                )
            else:
                parse = "180"
                adven = await self.query_dict(matched_list[0], self.adven_db)
                # print(adven.element)
                print(adven.dps.parse["180"]["krdb"].dps)
                try:
                    adven.dps
                except AttributeError:
                    embed = discord.Embed(
                        title=f"__**Healers do not have DPS records.**__",
                        description=f"A good wyrmprint combination"
                        " is **Give Me Your Wou"
                        "nded** and **Pipe Down**.\n\nOther alternatives include"
                        ":\nJewels of the Sun, and "
                        "United by Vision\n\nKeep in mind healers require "
                        "**Skill Haste** and **Recovery Potency** as "
                        "their primary stats.\n\n"
                        "As a note, Heinwald is the only healer with a DPS profile.",
                        colour=MISC.rand_color(),
                    )
                    embed.set_footer()
                    return await ctx.send(embed=embed)
                message = await ctx.send(
                    embed=self.adven_db["marth"].dps.embed(parse, coabs)
                )
                if "error" in message.embeds[0].title.lower():
                    return
                await message.add_reaction(CONST.emoji["star"])
                await message.add_reaction(CONST.emoji["down_arrow"])
                await self.adven_profile_process(ctx, message, adven)
        else:
            return await ctx.send(
                f"Either the adventurer {adven} was not found, or an error occured."
            )

    async def return_rankings_embed(self, element, parse):
        rank_amt = 10
        if element:
            for each in dragalia_elements.keys():
                if element.lower().strip() in each:
                    element = dragalia_elements[each]
                    embed = discord.Embed(
                        title=(f"**{element.title()} Top {rank_amt} Rankings**"),
                        description=f"*Parse: {parse} Seconds*",
                        colour=discord.Colour(CONST.elements_colors[element]),
                    )
                    break
        else:
            element = "all"
            embed = discord.Embed(
                title=f"**All Elements Top {rank_amt} Rankings**",
                description=f"*Parse: {parse} Seconds*",
                colour=discord.Colour(MISC.rand_color()),
            )
        name_string = ""
        dps_string = ""
        for x, entry in enumerate(self.rank_db[parse][element]):
            if x == rank_amt:
                break
            adven = self.adven_db[entry]
            name = f"{x+1}. {adven.name}"
            adven = await self.query_dict(adven, self.adven_db)
            if element == "all":
                name_string += (
                    f"{CONST.d_emoji[adven.element.lower()]}"
                    f"{CONST.d_emoji[adven.weapon.lower()]}{name}\n"
                )
            else:
                name_string += f"{CONST.d_emoji[adven.weapon.lower()]}{name}\n"
            dps_string += f"{adven.dps.parse[parse].dps}\n"
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
        await self.dps_update_check(ctx)
        parse = "180"
        embed = await self.return_rankings_embed(element=element, parse=parse)
        message = await ctx.send(embed=embed)
        await message.add_reaction(CONST.emoji["down_arrow"])

        def check_response(reaction, user):
            return (
                (
                    reaction.emoji == CONST.emoji["up_arrow"]
                    or reaction.emoji == CONST.emoji["down_arrow"]
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
                    embed=embed, reaction=reaction, user=user, parse=parse
                )
                element = reaction.message.embeds[0].title.split(" ")[0]
                element = strip_all(element.lower().strip())
                if element not in dragalia_elements:
                    element = None
                await reaction.message.edit(
                    embed=await self.return_rankings_embed(element=element, parse=parse)
                )

    @dragalia.command(name="update")
    @commands.cooldown(rate=1, per=30.00, type=commands.BucketType.default)
    async def update_draglia_data(self, ctx, *, tables=None):
        force = dps = False
        if tables:
            if "force" in tables.lower():
                force = True
                tables = tables.replace("force", "")
                tables = tables.strip()
            if "dps" in tables.lower():
                dps = True
                tables = tables.replace("dps", "")
                tables = tables.strip()
            tables = tables.split(" ")
            await ctx.send("Beginning update...")
            try:
                updated = await self.update.update(tables=tables, force=force)
            except Exception as e:
                traceback.print_exc()
                return await ctx.send(f"Update failed: {e}")
        else:
            await ctx.send("**Now updating Adventurer, Skill, Wyrmprint entries...**")
            try:
                updated = await self.update.async_full_update(force=force)
            except Exception as e:
                traceback.print_exc()
                return await ctx.send(f"Update failed: {e}")

        self.adven_db = await self.async_create_names("Adventurers")
        self.wp_db = await self.async_create_names("Wyrmprints")
        if updated:
            await ctx.send(f"__Updates successful!__")
        if "adv" in updated:
            await ctx.send(f"\n{updated['adv']} new Adventurers.")
        if "wp" in updated:
            await ctx.send(f"\n{updated['wp']} new Wyrmprints.")

        if dps:
            if DPS.check_version():
                await ctx.send("Updating DPS entries...")
                try:
                    self.dps_db = DPS.build_dps_db(
                        await DPS.async_pull_csvs(self.bot.session, self.dps_db_path)
                    )
                    self.rank_db = DPS.gen_ranks(self.dps_db)
                    self.dps_hash = DPS.update_master_hash()
                    await ctx.send("__DPS update complete!__")
                except Exception as e:
                    traceback.print_exc()
                    return await ctx.send(f"Update failed: {e}")
            else:
                await ctx.send("DPS records are up to date.")
        return

    @update_draglia_data.error
    async def update_draglia_data_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send("This command is currently on cooldown.")


def setup(bot):
    bot.add_cog(Dragalia(bot))
