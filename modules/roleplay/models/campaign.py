import random
from discord import Embed, Colour


def generate_rand_color():
    return random.randint(0, 0xFFFFFF)


class Campaign:
    def __init__(self, pnp):
        return

    def roll_dice(amount: int, dice: int = 6):
        return [random.randint(1, dice) for x in range(1, amount + 1)]

    @staticmethod
    def get_pnp_list():
        return pnp_list.keys()


class Mutant(Campaign):
    def __init__(self):
        return

    def dice(self, string):
        rolls = []
        roll_list = string.split("+")
        for each in roll_list:
            if "d" in each:
                dice_split = each.split("d")
                amount = int(dice_split[0].strip())
                dice = int(dice_split[1].strip())
                rolls.append(self.roll_dice(amount, dice))
            else:
                rolls.append(self.roll_dice(int(each)))
        return rolls


pnp_list = {"mutant": Mutant()}
