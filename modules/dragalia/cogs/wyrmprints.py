import discord
from discord.ext import commands
import random
import sys
import config
import traceback
import requests
import aiohttp
import os
import json
import string
from fuzzywuzzy import fuzz

WYRMPRINT_URL = "http://phoenixfieryn.com/dragalia/wp-guide-data.json"

def generate_random_color():
    return random.randint(0, 0xFFFFFF)

def lev_dist_similar(a, b):
    return fuzz.partial_ratio(a.lower(), b.lower())

class Adventurer:
    def __init__(self, character_dict):
        self.name = character_dict['name']
        self.rarity = character_dict['rarity']
        self.limited = character_dict['limited']
        try:
            self.shortcut = character_dict['shortcut']
        except KeyError:
            pass
        image = "".join([c.lower() for c in self.name if c in string.ascii_letters])
        self.image = f"http://phoenixfieryn.com/img/dragalia/characters/{image}/i1.png"
        self.comboes = self.generate_comboes_list(character_dict['combination'])

    def generate_comboes_list(self, combo_dict):
        for each in combo_dict.keys():
            val = 0
            for desc in combo_dict[each]:
                combo_dict[each][val] = " + ".join(desc)
                val += 1
        return combo_dict

class Wyrmprints(commands.Cog, Adventurer):
    def __init__(self, bot):
        self.bot = bot
        print_db = {}
        self.path_to_print_json_file = f'{self.bot.modules["dragalia"].path}/lists/print_db.json'
        json_file = requests.get(WYRMPRINT_URL).json()
        print_db_raw = json_file['characters']
        print_db = self.rename_dict_keys(print_db_raw)
        with open (self.path_to_print_json_file, 'w') as file:
            json.dump(print_db, file, indent = 4)
        self.adventurer_db = self.create_classes(print_db)


    def rename_dict_keys(self, raw_db):
        print_db = {}
        for each in raw_db:
            entry_name = each['name'].lower()
            print_db[entry_name] = each
            name_string = each['name'].split(" ")
            if len(name_string) > 1:
                first_letter = name_string[0][0].lower()
                shortcut = first_letter + name_string[1].lower()
                print_db[entry_name]['shortcut'] = shortcut
        return print_db

    async def async_rename_dict_keys(self, raw_db):
        print_db = {}
        for each in raw_db:
            print_db[each['name'].lower()] = each
        return print_db

    def create_classes(self, input_db):
        adventurer_db = {}
        for character in input_db:
            adventurer_db[input_db[character]['name'].lower()] = Adventurer(input_db[character])
        return adventurer_db

    async def async_create_classes(self, input_db):
        adventurer_db = {}
        for character in input_db:
            adventurer_db[input_db[character]['name'].lower()] = Adventurer(input_db[character])
        return adventurer_db

    async def cog_check(self, ctx):
        return ctx.guild.id in self.bot.module_access["dragalia"]

    async def character_print_json_dump(self, json_info):
        with open(self.path_to_print_json_file, 'w') as file:
            json.dump(json_info, file, indent = 4)

    async def pull_json_file_from_source(self):
        async with aiohttp.ClientSession() as session:
            async with session.get(WYRMPRINT_URL) as response:
                json_file = await response.json()
                print_db = await self.async_rename_dict_keys(json_file['characters'])
                await self.character_print_json_dump(print_db)
                self.adventurer_db = await self.async_create_classes(print_db)

    async def character_validate(self, char_input):
        char_input = char_input.lower()
        char_result_list = []
        high_score = 0
        for char in self.adventurer_db:
            char = self.adventurer_db[char]
            if char_input == char.name.lower():
                return [char]
            try:
                if char_input == char.shortcut:
                    return [char]
            except AttributeError:
                pass
            temp_score = lev_dist_similar(char_input, char.name.lower())
            if temp_score > high_score:
                high_score = temp_score
        for char in self.adventurer_db:
            char = self.adventurer_db[char]
            score = lev_dist_similar(char_input, char.name.lower())
            if high_score - 5 <= score <= high_score + 5:
                char_result_list.append(char)
        return list(set(char_result_list))

    async def return_character_embed(self, character):
        embed = discord.Embed(title=f"__**{character.name}**__",
                    colour=discord.Colour(generate_random_color()))
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
                                colour=discord.Colour(generate_random_color()),
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
