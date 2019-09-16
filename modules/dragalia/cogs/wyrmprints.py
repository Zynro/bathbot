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

class Adventurer:
    def __init__(self, character_dict):
        self.name = name
        self.dps = character_dict['dps']
        self.rarity = character_dict['rarity']
        self.element = character_dict['element']
        self.weapon = character_dict['weapon']
        self.str = character_dict['str']
        self.wyrmprints = character_dict['wyrmprints']
        self.dragon = character_dict['dragon']
        self.condition = character_dict['condition']
        self.comment = character_dict['comment']
        self.damage = character_dict['damage']
        self.image = f"https://b1ueb1ues.github.io/dl-sim/pic/character/{name}.png"
        return

"""class DPS:
    def __init__(self, dps_dict):
        self.dps = dps_dict[]"""

class Wyrmprints(commands.Cog, Adventurer):
    def __init__(self, bot):
        self.bot = bot
        char_db = {}
        self.path_to_csv_file = f'{self.bot.modules["dragalia"].path}/lists/optimal_dps_data'
        adventurer_dict = self.get_source_csv(self.path_to_csv_file)
        #self.adventurer_db = self.create_classes(adventurer_dict)

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
        for parse in response_dict.keys():
            del response_dict[parse][0]
            if parse == '180':
                parse = response_dict[parse]
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
                    if "_" in row[1]:
                        name = row[1].replace("_", "").lower().strip()
                        alt = True
                    else:
                        name = row[1].lower().strip()
                        alt = False
                    amulets = row[6].split("][")
                    wyrmprints = amulets[0].split("+")
                    wyrmprints = remove_brackets(" + ".join(wyrmprints).replace("_", " "))
                    dragon = remove_brackets(amulets[1])
                    full_char_dict[name] = {
                                              'name' : row[1],
                                              'dps': row[0],
                                              'rarity': row[2],
                                              'element': row[3],
                                              'weapon': row[4],
                                              'str': row[5],
                                              'wyrmprints': wyrmprints,
                                              'dragon' : dragon,
                                              'condition': row[7].replace("<", "").replace(">", ""),
                                              'comment': row[8],
                                              'alt' : alt
                                              }
        print(full_char_dict['marth'])
                

    def create_classes(self, input_db):
        adventurer_db = {}
        for character in input_db.keys():
            adventurer_db[character.lower()] = Adventurer(input_db[character])
        return adventurer_db

    async def async_create_classes(self, input_db):
        adventurer_db = {}
        for character in input_db.keys():
            adventurer_db[character.lower()] = Adventurer(input_db[character])
        return adventurer_db

    async def character_validate(self, char_input):
        char_input = char_input.lower()
        char_result_list = []
        high_score = 0
        for char in self.adventurer_db.keys():
            char = self.adventurer_db[char]
            if char_input == char.name.lower():
                return [char]
            try:
                if char_input == char.shortcut:
                    return [char]
            except AttributeError:
                pass
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
        embed = discord.Embed(title=f"__**{character.name}**__",
                    colour=discord.Colour(await generate_random_color()))
        embed.set_thumbnail(url=character.image)
        for combo in character.comboes.keys():
            embed.add_field(name = combo, value = "\n".join(character.comboes[combo]), inline = False)
        embed.set_footer(text = 'Data seem outdated? Run the "&print-get" command to pull new data.')
        return embed

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
        await self.build_adventurer_database(await self.async_get_source_csv(self.path_to_csv_file))
        return

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
        embed = await self.return_character_embed(character_dict_entry)
        return await ctx.send(embed)

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
