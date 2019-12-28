import random
import re
from discord import Embed


def rand_color():
    return random.randint(0, 0xFFFFFF)


non_alpha = "[^a-zA-Z0-9]"


class Campaign:
    def __init__(self):
        return

    def roll_dice(self, amount: int, dice: int):
        return [random.randint(1, dice) for x in range(1, amount + 1)]

    @staticmethod
    def get_pnp_list():
        return pnp_list.keys()


class Mutant(Campaign):
    def __init__(self):
        return

    def mutant_dice(self, roll_list):
        rolls = []
        for each in roll_list:
            if "d" in each:
                dice_split = each.split("d")
                amount = int(dice_split[0].strip())
                dice = int(dice_split[1].strip())
                rolls.append(self.roll_dice(amount, dice))
            else:
                rolls.append(self.roll_dice(int(each), 6))
        return rolls

    def dice(self, string, author):
        if author.nick:
            name = author.nick
        else:
            name = author.name
        checks = ["scrap", "artifact"]
        roll_list = re.split(non_alpha, string)
        if roll_list[0] in checks:
            checks = True
            input_string = f"{str.title('+'.join(roll_list))} Roll"
        else:
            checks = False
            input_string = "+".join(roll_list)
            results = self.mutant_dice(roll_list)
            roll_dict = {each: results[x] for x, each in enumerate(roll_list)}

        # Begin creating embed
        embed = Embed(
            title=f"**{name}** rolls:\n`{input_string}`",
            description=" ",
            color=author.colour,
        )
        if "d" in input_string:  # split by game mode later, temporary stopgap
            for index, each in enumerate(results):
                embed.add_field(
                    name=f"**__{roll_list[index]}__**",
                    value=f"{', '.join([str(x) for x in each])}",
                    inline=False,
                )
            flat = sum([item for sublist in results for item in sublist])
            embed.add_field(name="**__Totals:__**", value=f"Sum: {flat}", inline=False)
        elif checks:
            joined = "".join(str(x) for x in self.roll_dice(3, 6))
            embed.add_field(name=f"**__Result:__**", value=joined)
            roll_dict = None
        else:
            for index, each in enumerate(results):
                embed.add_field(
                    name=f"**__{roll_list[index]}d6__**",
                    value=f"{', '.join([str(x) for x in each])}",
                    inline=False,
                )
            flat = [item for sublist in results for item in sublist]
            successes = flat.count(6)
            failures = flat.count(1)
            embed.add_field(
                name="**__Totals:__**",
                value=f"Success: **{successes}**\nFailure: {failures}",
                inline=False,
            )
        return embed, roll_dict


pnp_list = {"mutant": Mutant()}
