import discord
from discord.ext import commands
import aiosqlite
import sqlite3
from fuzzywuzzy import fuzz
from modules.dragalia.models.adventurer import Adventurer
from modules.dragalia.models.scrape_update import Update as ScrapeUpdate
from modules.dragalia.models.dps import DPS
import modules.dragalia.models.constants as CONSTANTS
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


async def lev_dist_similar(a, b):
    return fuzz.ratio(a.lower().strip(), b.lower().strip())


def strip_all(input_str):
    return "".join([x for x in input_str if x.isalpha()])


def get_master_hash(repo):
    versions = str(MISC.git_sub("ls-remote", repo))
    return versions.split("\\n")[-2].split("\\")[0]


class Dragalia(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.module = self.bot.modules["dragalia"]

        self.MASTER_DB = f"modules/{self.module.path}/lists/master.db"
        self.update = ScrapeUpdate(self.MASTER_DB)
        self.update.full_update()
        self.dps_db_path = f"modules/{self.module.path}/lists/optimal_dps_data"
        self.dps_csv = DPS.get_src_csv(self.dps_db_path)
        self.dps_db = DPS.build_dps_db(self.dps_csv)
        with open(f"modules/{self.module.path}/lists/dps_hash.json") as file:
            self.dps_hash = json.loads(file.read())

        self.rank_db = DPS.build_rank_db(self.dps_db)
        self.adven_db = self.create_names()

    async def cog_check(self, ctx):
        return ctx.guild.id in self.bot.module_access["dragalia"]

    def create_names(self):
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
            query = c.execute("SELECT * FROM Adventurers")
            results = query.fetchall()
            adven_classes = {}
            for each in results:
                adven_classes[each["internal_name"]] = Adventurer(
                    {"name": each["name"], "internal_name": each["internal_name"]}
                )
        return adven_classes

    async def async_create_names(self):
        async with aiosqlite.connect(self.MASTER_DB) as db:
            db.row_factory = aiosqlite.Row
            query = await db.execute("SELECT * FROM Adventurers")
            results = await query.fetchall()
        adven_classes = {}
        for each in results:
            adven_classes[each["internal_name"]] = Adventurer(
                {"name": each["name"], "internal_name": each["internal_name"]}
            )
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
        try:
            name = name.internal_name
        except AttributeError:
            pass
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
            adventurer = self.adven_db[internal_name] = Adventurer(
                adven_row, skills, self.dps_db, self.rank_db
            )
        return adventurer

    async def adven_validate(self, adven_input):
        if '"' in adven_input:
            adven_input.replace('"', "")
            try:
                return self.adven_db[adven_input.lower().strip()]
            except KeyError:
                return None
        adven_input.replace('"', "")
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
            if high_score_name == 100 or high_score_i_name == 100:
                if i_name_score == 100:
                    return [adven]
                if name_score == 100 or i_name_score == 100:
                    adven_results.append(adven)
            else:
                if high_score_name - 5 <= name_score <= high_score_name + 5:
                    adven_results.append(adven)
                if high_score_i_name - 5 <= i_name_score <= high_score_i_name + 5:
                    adven_results.append(adven)
        return list(set(adven_results))

    async def return_multiple_results(self, multiple_results):
        char_result_list = []
        for each in multiple_results:
            char_result_list.append(f"{each.name} / {each.internal_name}")
        char_result_list = "\n".join(char_result_list)
        embed = discord.Embed(
            title="I found multiple results for your search:",
            colour=discord.Colour(MISC.generate_random_color()),
            description=char_result_list,
        )
        embed.set_footer(text="Try your search again" " with a adventurer specified.")
        return embed

    async def proccess_parse_change(
        self, embed=None, reaction=None, user=None, parse=None
    ):
        message = reaction.message
        if reaction.emoji == CONSTANTS.emoji["up_arrow"]:
            await reaction.remove(user)
            if "60" in embed.description:
                parse = "120"
                await message.add_reaction(CONSTANTS.emoji["down_arrow"])
                return parse
            elif "120" in embed.description:
                parse = "180"
                await reaction.remove(self.bot.user)
                return parse

        elif reaction.emoji == CONSTANTS.emoji["down_arrow"]:
            await reaction.remove(user)
            if "180" in embed.description:
                parse = "120"
                await message.add_reaction(CONSTANTS.emoji["up_arrow"])
                return parse
            if "120" in embed.description:
                parse = "60"
                await reaction.remove(self.bot.user)
                return parse

        elif reaction.emoji == CONSTANTS.emoji["star"]:
            await reaction.remove(user)
            if "parse" in embed.description.lower():
                await message.remove_reaction(
                    CONSTANTS.emoji["down_arrow"], self.bot.user
                )
                await message.remove_reaction(
                    CONSTANTS.emoji["up_arrow"], self.bot.user
                )
                return "adv"
            else:
                await message.add_reaction(CONSTANTS.emoji["down_arrow"])
                return "180"

    async def adven_profile_process(self, ctx, message, adven, parse="180"):
        def check_response(reaction, user):
            return (
                (
                    reaction.emoji == CONSTANTS.emoji["up_arrow"]
                    or reaction.emoji == CONSTANTS.emoji["down_arrow"]
                    or reaction.emoji == CONSTANTS.emoji["star"]
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
                if parse == "adv":
                    await reaction.message.edit(embed=adven.embed())
                else:
                    await reaction.message.edit(embed=adven.dps.embed(parse))

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
        matched_list = await self.adven_validate(adven)
        if matched_list:
            if len(matched_list) > 1:
                return await ctx.send(
                    embed=await self.return_multiple_results(matched_list)
                )
            else:
                adven = await self.query_adv(matched_list[0])
                message = await ctx.send(embed=adven.embed())
                await message.add_reaction(CONSTANTS.emoji["star"])
                await self.adven_profile_process(ctx, message, adven)
        else:
            return await ctx.send(
                f"Either the adventurer {adven} was not found, or an error occured."
            )

    @dragalia.command()
    async def dps(self, ctx, *, adven: str = None):
        """
        Retreive DPS Simulator data for a single character for parses of 60,
        120, and 180 seconds.

        Usage:
            &[drag/d] dps <character>
        """
        if not adven:
            return await ctx.send(
                "An adventurer must be entered to search the database."
            )

        current = MISC.get_master_hash(CONSTANTS.REPO_URL)
        if self.dps_hash != current:
            embed = discord.Embed(
                title="There are updates available for the the DPS records.",
                description="Please wait while the updater is called...",
            )
            await ctx.send(embed=embed)
            command = self.bot.get_command("dragalia update")
            await ctx.invoke(command, tables="dps")

        adven = adven.lower().strip()
        matched_list = await self.adven_validate(adven)
        if matched_list:
            if len(matched_list) > 1:
                return await ctx.send(
                    embed=await self.return_multiple_results(matched_list)
                )
            else:
                parse = "180"
                adven = await self.query_adv(matched_list[0])
                if adven.weapon == "Staff":
                    embed = discord.Embed(
                        title=f"__**Healers do not have DPS records.**__",
                        description=f"A good wyrmprint combinatio"
                        " is **Give Me Your Wou"
                        "nded** and **Pipe Down**.\n\nOther alternatives include"
                        ":\nGive Me Your Wounded, Pipe Down, Jewels of the Sun, "
                        "United by Vision\n\nKeep in mind healers require "
                        "**Skill Haste** and **Recovery Potency** as "
                        "their primary stats.",
                        colour=MISC.generate_random_color(),
                    )
                    return await ctx.send(embed=embed)
                message = await ctx.send(embed=adven.dps.embed(parse))
                if "error" in message.embeds[0].title.lower():
                    return
                await message.add_reaction(CONSTANTS.emoji["star"])
                await message.add_reaction(CONSTANTS.emoji["down_arrow"])
                await self.adven_profile_process(ctx, message, adven)
        else:
            return await ctx.send(
                f"Either the adventurer {adven} was not found, or an error occured."
            )

    async def return_rankings_embed(self, element, parse):
        if element:
            for each in dragalia_elements.keys():
                if element.lower().strip() in each:
                    element = dragalia_elements[each]
                    embed = discord.Embed(
                        title=(f"**{element.title()} Top 10 Rankings**"),
                        description=f"*Parse: {parse} Seconds*",
                        colour=discord.Colour(CONSTANTS.elements_colors[element]),
                    )
                    break
        else:
            element = "all"
            embed = discord.Embed(
                title=f"**All Elements Top 10 Rankings**",
                description=f"*Parse: {parse} Seconds*",
                colour=discord.Colour(MISC.generate_random_color()),
            )
        name_string = ""
        dps_string = ""
        x = 1
        for entry in self.rank_db[parse][element]:
            if x == 11:
                break
            adven = self.adven_db[entry]
            name = f"{x}. {adven.name}"
            adven = await self.generate_adven_class(adven)
            name_string += f"{name}\n"
            dps_string += f"{adven.dps.parse[parse].dps}\n"
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
                    embed=embed, reaction=reaction, user=user, parse=parse
                )
                element = reaction.message.embeds[0].title.split(" ")[0]
                element = strip_all(element.lower().strip())
                if element not in dragalia_elements:
                    element = None
                await reaction.message.edit(
                    embed=await self.return_rankings_embed(element=element, parse=parse)
                )

    @dragalia.command(name="wp")
    async def wyrmprint(self, ctx, *, wp):
        return

    @dragalia.command(name="update")
    @commands.cooldown(rate=1, per=30.00, type=commands.BucketType.default)
    async def update_draglia_data(self, ctx, *, tables=None):
        force = False
        if tables:
            if "force" in tables.lower():
                force = True
            tables = tables.split(" ")
            await ctx.send("Now updating selected entries...")
            try:
                updated = await self.update.update(tables=tables, force=force)
            except Exception as e:
                traceback.print_exc()
                return await ctx.send(f"Update failed: {e}")
        else:
            await ctx.send("Now updating Adventurer, Skill, Wyrmprint entries...")
            try:
                updated = await self.update.async_full_update(force=force)
            except Exception as e:
                traceback.print_exc()
                return await ctx.send(f"Update failed: {e}")

        self.adven_db = await self.async_create_names()
        if updated:
            await ctx.send(f"__Updates successful!__")
        if "adv" in updated:
            await ctx.send(f"\n{updated['adv']} new Adventurers.")
        if "wp" in updated:
            await ctx.send(f"\n{updated['wp']} new Wyrmprints.")

        if not tables or "dps" in tables:
            await ctx.send("Updating DPS entries...")
            try:
                self.dps_db = DPS.build_dps_db(
                    await DPS.async_get_src_csv(self.dps_db_path)
                )
                self.rank_db = DPS.build_rank_db(self.dps_db)
                self.dps_hash = DPS.update_master_hash()
                await ctx.send("__DPS update complete!__")
            except Exception as e:
                traceback.print_exc()
                return await ctx.send(f"Update failed: {e}")
        return

    @update_draglia_data.error
    async def update_draglia_data_error(ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(
                "This command is currently on cooldown, please try again later."
            )


def setup(bot):
    bot.add_cog(Dragalia(bot))
