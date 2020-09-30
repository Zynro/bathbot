import random
import re
from discord import Embed
from systems.mutant import Mutant


class Campaign:
    def __init__(self):
        return

    def DICE(self, amount: int, dice: int):
        return [random.randint(1, dice) for x in range(1, amount + 1)]

    @staticmethod
    def get_pnp_list():
        return pnp_list.keys()


pnp_list = {"mutant": Mutant()}
