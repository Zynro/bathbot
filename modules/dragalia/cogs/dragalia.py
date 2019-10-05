import discord
from discord.ext import commands
import random
import csv
import config
import requests
import aiohttp
from fuzzywuzzy import fuzz
from modules.dragalia.models.adventurer import Adventurer

DPS_URL_60 = "https://b1ueb1ues.github.io/dl-sim/60/data_kr.csv"
DPS_URL_120 = "https://b1ueb1ues.github.io/dl-sim/120/data_kr.csv"
DPS_URL_180 = "https://b1ueb1ues.github.io/dl-sim/180/data_kr.csv"

dragalia_elements = ['flame', 'water', 'wind', 'light', 'shadow']
dragalia_elements_images = {'flame': 'https://b1ueb1ues.github.io//dl-sim/pic/element/flame.png',
                            'water': 'https://b1ueb1ues.github.io//dl-sim/pic/element/water.png',
                            'wind': 'https://b1ueb1ues.github.io//dl-sim/pic/element/wind.png',
                            'light': 'https://b1ueb1ues.github.io//dl-sim/pic/element/light.png',
                            'shadow': 'https://b1ueb1ues.github.io//dl-sim/pic/element/shadow.png',
                            'all': 'https://icon-library.net/images/muscle-icon-png/muscle-icon-png-24.jpg'}


def generate_random_color():
    return random.randint(0, 0xFFFFFF)


async def lev_dist_similar(a, b):
    return fuzz.partial_ratio(a.lower(), b.lower())


def remove_brackets(input_str):
    return input_str.replace("[", "").replace("]", "")


async def async_remove_brackets(input_str):
    return input_str.replace("[", "").replace("]", "")


def strip_all(input_str):
    return "".join([x for x in input_str if x.isalpha()])


class Dragalia(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.path_to_csv_file = f'{self.bot.modules["dragalia"].path}/lists/optimal_dps_data'
        char_dict = self.build_adventurer_database(self.get_source_csv(self.path_to_csv_file))
        self.adventurer_db = self.create_classes(char_dict)
        self.dps_rankings = self.create_rankings()
        for character, value in self.adventurer_db.items():
            self.adventurer_db[character].update_rank(self.dps_rankings)

    async def cog_check(self, ctx):
        return ctx.guild.id in self.bot.module_access["dragalia"]

    def get_source_csv(self, path):
        response_dict = {}
        response_dict['180'] = requests.get(DPS_URL_180).text
        response_dict['120'] = requests.get(DPS_URL_120).text
        response_dict['60'] = requests.get(DPS_URL_60).text
        for parse in response_dict.keys():
            path_to_file = f"{path}_{parse}.csv"
            with open(path_to_file, "w", newline="", encoding='utf-8') as file:
                writer = csv.writer(file)
                response_dict[parse] = response_dict[parse].split("\n")
                for row in response_dict[parse]:
                    row = row.split(',')
                    try:
                        var = row[1]
                    except IndexError:
                        continue
                    writer.writerow(row)
        return response_dict

    async def async_get_source_csv(self, path):
        response_dict = {}
        async with aiohttp.ClientSession() as session:
            async with session.get(DPS_URL_180) as response:
                response_dict['180'] = await response.text()
            async with session.get(DPS_URL_120) as response:
                response_dict['120'] = await response.text()
            async with session.get(DPS_URL_60) as response:
                response_dict['60'] = await response.text()
        for parse in response_dict.keys():
            path_to_file = f"{path}_{parse}.csv"
            with open(path_to_file, "w", newline="", encoding='utf-8') as file:
                writer = csv.writer(file)
                response_dict[parse] = response_dict[parse].split("\n")
                for row in response_dict[parse]:
                    row = row.split(',')
                    try:
                        var = row[1]
                    except IndexError:
                        continue
                    writer.writerow(row)
        return response_dict

    def build_adventurer_database(self, response_dict):
        full_char_dict = {}
        damage = {}
        for parse_value in response_dict.keys():
            del response_dict[parse_value][0]
            parse = response_dict[parse_value]
            for row in parse:
                row = row.split(",")
                #print(row)
                try:
                    var = row[1]
                except IndexError:
                    continue
                if "_c_" in row[1]:
                    continue
                if "Fleur" in row[1]:
                    del row[9]
                internal_name = row[1]
                if "_" in row[1]:
                    name = row[1].replace("_", "").lower().strip()
                    alt = True
                else:
                    name = row[1].lower().strip()
                    alt = False
                if parse_value == "180":
                    amulets = row[6].split("][")
                    wyrmprints = amulets[0].split("+")
                    wyrmprints = remove_brackets(" + ".join(wyrmprints).replace("_", " "))
                    dragon = remove_brackets(amulets[1])
                    full_char_dict[name] = {
                                              'name' : name,
                                              'internal_name' : internal_name,
                                              'rarity': row[2],
                                              'element': row[3],
                                              'weapon': row[4],
                                              'str': row[5],
                                              'wyrmprints': wyrmprints,
                                              'dragon' : dragon,
                                              'alt' : alt
                                              }
                    full_char_dict[name]['parse']= {}
                damage = {}
                damage_list = row[9:]
                damage['dps'] = row[0]
                damage['types'] = {}
                for damage_type in damage_list:
                    damage_type = damage_type.split(":")
                    damage_name = damage_type[0].replace("_", " ").title()
                    damage['types'][damage_name] = damage_type[1]
                full_char_dict[name]['parse'][parse_value] = {}
                full_char_dict[name]['parse'][parse_value]['damage'] = damage
                full_char_dict[name]['parse'][parse_value]['condition'] = row[7].replace("<", "").replace(">", ""),
                full_char_dict[name]['parse'][parse_value]['comment'] =  row[8]
        return full_char_dict

    def create_classes(self, input_db):
        return {character.lower(): Adventurer(input_db[character]) for character in input_db.keys()}

    def create_rankings(self):
        rankings_db = {}
        parses = ['180', '120', '60']
        for parse in parses:
            rankings_db[parse] = {}
            sorted_list = sorted(
                                [(
                                    self.adventurer_db[char].name,
                                    self.adventurer_db[char].parse[parse].dps
                                ) for char in self.adventurer_db.keys()
                                ],
                                key=lambda x: x[1],
                                reverse=True
                                )
            rankings_db[parse]['all'] = [entry[0] for entry in sorted_list]
            for element in dragalia_elements:
                sorted_list = sorted(
                                     [(
                                       self.adventurer_db[char].name,
                                       self.adventurer_db[char].parse[parse].dps
                                       )
                                      for char in self.adventurer_db.keys()
                                      if self.adventurer_db[char].element == element
                                      ],
                                     key=lambda x: x[1], reverse=True)
                rankings_db[parse][element] = [entry[0] for entry in sorted_list]
        return rankings_db

    async def character_validate(self, char_input):
        char_input = char_input.lower()
        char_result_list = []
        high_score = 0
        try:
            character = self.adventurer_db[char_input]
            return [character]
        except KeyError:
            pass
        for char in self.adventurer_db.keys():
            char = self.adventurer_db[char]
            if char_input == char.name.lower():
                return [char]
            temp_score = await lev_dist_similar(char_input, char.name.lower())
            if temp_score > high_score:
                high_score = temp_score
        for char in self.adventurer_db.keys():
            char = self.adventurer_db[char]
            score = await lev_dist_similar(char_input, char.name.lower())
            if high_score - 5 <= score <= high_score + 5:
                char_result_list.append(char)
        return list(set(char_result_list))

    async def return_character_embed(self, character, parse):
        embed = discord.Embed(title=f"__**{character.internal_name}**__",
                              description=f"*Parse: {parse} Seconds*",
                              colour=discord.Colour(generate_random_color()))
        return character.populate_embed(embed=embed, parse_value=parse)

    async def return_multiple_results_embed(self, multiple_results):
        char_result_list = []
        for each in multiple_results:
            char_result_list.append(each.internal_name)
        char_result_list = "\n".join(char_result_list)
        embed = discord.Embed(title="I found multiple results for your search:", 
                              colour=discord.Colour(generate_random_color()),
                              description=char_result_list)
        embed.set_footer(text="Try your search again with a adventurer specified.")
        return embed

    @commands.group(aliases=['drag', 'd'])
    async def dragalia(self, ctx):
        """
        The Dragalia Lost command group.

        Aliases:
            [drag/d]
        Subcommands:
            [dps]
                Retreive DPS Simulator data for a single character for parses of 60, 120, and 180 seconds.
            [rank/ranking/rankings]
                Retreive a list of top ten Adventurers based on the DPS Simulator for an element, or overall.
        """
        if not ctx.invoked_subcommand:
            return

    @dragalia.command()
    async def dps(self, ctx, *, character: str = None):
        """
        Retreive DPS Simulator data for a single character for parses of 60, 120, and 180 seconds.

        Usage:
            &[drag/d] dps <character>
        """
        if not character:
            return await ctx.send("A character must be entered to search the database.")
        character = character.lower()
        matched_list = await self.character_validate(character)
        if matched_list:
            if len(matched_list) > 1:
                return await ctx.send(embed=await self.return_multiple_results_embed(matched_list))
            else:
                parse = "60"
                message = await ctx.send(embed=await self.return_character_embed(matched_list[0], parse))
                await message.add_reaction('⬆')
        else:
            return await ctx.send("Errored.")

    async def return_rankings_embed(self, element, parse):
        if element:
            for each in dragalia_elements:
                if element.lower().strip() in each:
                    element = each
                    embed = discord.Embed(title=f"**{element.title()} Top 10 Rankings**",
                                          description=f"*Parse: {parse} Seconds*",
                                          colour=discord.Colour(generate_random_color()))
                    break
        else:
            element = 'all'
            embed = discord.Embed(title=f"**All Elements Top 10 Rankings**",
                                  description=f"*Parse: {parse} Seconds*",
                                  colour=discord.Colour(generate_random_color()))
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
        embed.set_thumbnail(url=dragalia_elements_images[element])
        return embed

    @dragalia.command(name="rankings", aliases=['rank', 'ranks', 'ranking'])
    async def rankings(self, ctx, element=None):
        """
        Retreive a list of top ten Adventurers based on the DPS Simulator for an element, or overall.

        Usage:
            &[drag/d] [rank/ranking/rankings] <element>

        Element can be any element, or 'all' for overall top 10 list.
        """
        embed = await self.return_rankings_embed(element=element, parse='60')
        message = await ctx.send(embed=embed)
        await message.add_reaction('⬆')

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if user == self.bot.user or not reaction.message.embeds:
            return
        if reaction.message.author != self.bot.user:
            return
        if "Parse" not in reaction.message.embeds[0].description:
            return
        up_arrow = "⬆"
        down_arrow = "⬇"
        embed = reaction.message.embeds[0]
        if reaction.emoji == up_arrow:
            if "60" in embed.description:
                parse = "120"
            elif "120" in embed.description:
                parse = "180"
        elif reaction.emoji == down_arrow:
            if "180" in embed.description:
                parse = "120"
            if "120" in embed.description:
                parse = "60"
        else:
            return
        if str(embed.author.name) == "Embed.Empty":
            check = embed.title
        else:
            check = emebed.author.name
            
        if "Adven" in check:
            adventurer = strip_all(embed.title).lower()
            character = self.adventurer_db[adventurer]
            await reaction.message.edit(embed=await self.return_character_embed(character, parse=parse))
        elif "Rank" in check:
            element = reaction.message.embeds[0].title.split(" ")[0]
            element = strip_all(element)
            await reaction.message.edit(embed=await self.return_rankings_embed(element=element, parse=parse))
        await reaction.message.clear_reactions()
        if parse == "60":
            await reaction.message.add_reaction(up_arrow)
        elif parse == "120":
            await reaction.message.add_reaction(down_arrow)
            await reaction.message.add_reaction(up_arrow)
        elif parse == "180":
            await reaction.message.add_reaction(down_arrow)

    @dragalia.command(name="print-get", aliases=['printdownload',
                                                 'print-update',
                                                 'update'])
    @commands.cooldown(rate=1, per=60.00, type=commands.BucketType.default)
    async def update_draglia_data(self, ctx):
        await ctx.send('Bathbot is now updating the recommend wyrmprint combinations from source, please wait...')
        try:
            char_dict = self.build_adventurer_database(await self.async_get_source_csv(self.path_to_csv_file))
            self.adventurer_db = self.create_classes(char_dict)
        except Exception as e:
            return await ctx.send(f"Update failed: {e}")
        await ctx.send('Update complete!')
        return

    @commands.command()
    async def trigger_embed(self, ctx, arg):
        """embed = discord.Embed(title = "Testing Embed edits.",
             colour = discord.Colour(generate_random_color()),
             description = "This is the first step.")
        message = await ctx.send(embed = embed)
        await ctx.send(message.embeds[0].title)"""
        await ctx.send(arg)


def setup(bot):
    bot.add_cog(Dragalia(bot))
