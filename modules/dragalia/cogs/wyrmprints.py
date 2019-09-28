import discord
from discord.ext import commands
import random
import sys
import csv
import config
import traceback
import requests
import aiohttp
import os
import json
import string
from fuzzywuzzy import fuzz

DPS_URL_60 = "https://b1ueb1ues.github.io/dl-sim/60/data_kr.csv"
DPS_URL_120 = "https://b1ueb1ues.github.io/dl-sim/120/data_kr.csv"
DPS_URL_180 = "https://b1ueb1ues.github.io/dl-sim/180/data_kr.csv"

async def generate_random_color():
    return random.randint(0, 0xFFFFFF)

async def lev_dist_similar(a, b):
    return fuzz.partial_ratio(a.lower(), b.lower())

def remove_brackets(input_str):
    return input_str.replace("[", "").replace("]", "")

async def async_remove_brackets(input_str):
    return input_str.replace("[", "").replace("]", "")

def strip_tuple(input_tuple):
    input_tuple = input_tuple.replace("(", "")
    input_tuple = input_tuple.replace(")", "")
    input_tuple = input_tuple.replace("'", "")
    return input_tuple

def dps_emoji_generator(dps: str = None):
    number_emoji_dict = {'1': ":one:",
                         '2': ":two:",
                         '3': ":three:", 
                         '4': ":four:", 
                         '5': ":five:", 
                         '6': ":six:", 
                         '7': ":seven:", 
                         '8': ":eight:", 
                         '9': ":nine:", 
                         '0': ":zero:"}
    dps_string = ""
    for digit in dps:
        dps_string += number_emoji_dict[digit]
    return dps_string


class Parse:
    def __init__(self, parse_dict):
        self.dps = strip_tuple(str(parse_dict['damage']['dps']))
        self.damage_types = parse_dict['damage']['types']
        self.condition = strip_tuple(str(parse_dict['condition']))
        self.comment = strip_tuple(str(parse_dict['comment']))

    def type_to_string(self):
        to_string_list = []
        for dmg_type in self.damage_types.keys():
            appending = f"{dmg_type}: {self.damage_types[dmg_type]}"
            to_string_list.append(appending)
        return "\n".join(to_string_list)

class Adventurer:
    def __init__(self, character_dict):
        self.name = character_dict['name']
        self.internal_name = character_dict['internal_name']
        self.rarity = character_dict['rarity']
        self.element = character_dict['element']
        self.weapon = character_dict['weapon']
        self.str = character_dict['str']
        self.wyrmprints = character_dict['wyrmprints']
        self.dragon = character_dict['dragon']
        self.parse = {}
        self.parse['180'] = Parse(character_dict['parse']['180'])
        self.parse['120'] = Parse(character_dict['parse']['120'])
        self.parse['60'] = Parse(character_dict['parse']['60'])
        self.image = f"https://b1ueb1ues.github.io/dl-sim/pic/character/{self.internal_name}.png"
        self.alt = character_dict['alt']
        return

    def populate_embed(self, embed, parse):
        embed.set_thumbnail(url=self.image)
        embed.add_field(name = "__DPS:__", value = dps_emoji_generator(self.parse[parse].dps), inline = False)
        embed.add_field(name = "__Wyrmprints:__", value = self.wyrmprints, inline = False)
        embed.add_field(name = "__Damage Breakdown:__", value = self.parse[parse].type_to_string(), inline = False)
        embed.add_field(name = "__Condition:__", value = self.parse[parse].condition)
        embed.add_field(name = "__Comment:__", value = self.parse[parse].comment)
        embed.set_footer(text = 'Data seem outdated? Run the "&print-get" command to pull new data.')
        return embed

class Wyrmprints(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        char_db = {}
        self.path_to_csv_file = f'{self.bot.modules["dragalia"].path}/lists/optimal_dps_data'
        char_dict = self.build_adventurer_database(self.get_source_csv(self.path_to_csv_file))
        self.adventurer_db = self.create_classes(char_dict)

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
        adventurer_db = {}
        for character in input_db.keys():
            adventurer_db[character.lower()] = Adventurer(input_db[character])
        return adventurer_db

    async def character_validate(self, char_input):
        char_input = char_input.lower()
        char_result_list = []
        high_score = 0
        try:
            character = self.adventurer_db[char_input]
            return [character]
        except IndexError:
            pass
        for char in self.adventurer_db.keys():
            char = self.adventurer_db[char]
            if char_input == char.name.lower():
                return [char]
            temp_score = await lev_dist_similar(char_input, char.name.lower())
            if temp_score > high_score:
                high_score = temp_score
        for char in self.adventurer_db:
            char = self.adventurer_db[char]
            score = await lev_dist_similar(char_input, char.name.lower())
            if high_score - 5 <= score <= high_score + 5:
                char_result_list.append(char)
        return list(set(char_result_list))

    async def return_character_embed(self, character):
        embed = discord.Embed(title=f"__**{character.internal_name}**__",
                    colour=discord.Colour(await generate_random_color()))
        return character.populate_embed(parse = "180", embed = embed)

    async def return_multiple_results_embed(self, multiple_results):
        char_result_list = []
        for each in multiple_results:
            char_result_list.append(each.name)
        char_result_list = "\n".join(char_result_list)
        embed = discord.Embed(title="I found multiple results for your search:", 
                                colour=discord.Colour(await generate_random_color()),
                                description = char_result_list)
        embed.set_footer(text="Try your search again with a adventurer specified.")
        return embed

    @commands.command()
    async def wp(self, ctx, *, character: str = None):
        """
        """
        if not character:
            return await ctx.send("A character must be entered to search the database.")
        character = character.lower()
        matched_list = await self.character_validate(character)
        if matched_list:
            if len(matched_list) > 1:
                return await ctx.send(embed = await self.return_multiple_results_embed(matched_list))
            else:
                return await ctx.send(embed = await self.return_character_embed(matched_list[0]))
        else:
            return await ctx.send("Errored.")

    @commands.command(name="print-get", aliases=['printdownload', 'print-update'])
    @commands.cooldown(rate = 1, per = 60.00, type = commands.BucketType.default)
    async def get_json_print_source(self, ctx):
        await ctx.send('Bathbot is now updating the recommend wyrmprint combinations from source, please wait...')
        try:
            await self.pull_json_file_from_source()
        except Exception as e:
            return await ctx.send(f"Update failed: {e}")
        await ctx.send('Update complete!')
        return
        

def setup(bot):
    bot.add_cog(Wyrmprints(bot))
