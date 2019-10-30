from modules.dragalia.models.dps import DPS
from modules.dragalia.models.skill import Skill


class Adventurer:
    def __init__(self, adven_dict, skills, dps_dict):
        for k in adven_dict.keys():
            setattr(self, k, adven_dict[k])
        skill_1 = [x for x in skills if x == self.skill_1]
        skill_2 = [x for x in skills if x == self.skill_2]
        self.skill_1 = Skill(skill_1)
        self.skill_2 = Skill(skill_2)
        self.dps = DPS(self, dps_dict)
