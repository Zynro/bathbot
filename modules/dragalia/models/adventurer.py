from modules.dragalia.models.dps import DPS


class Adventurer:
    def __init__(self, adven_dict, skills, dps_dict):
        for k in adven_dict.keys():
            setattr(self, k, adven_dict[k])
        for skill in skills:
            return
        self.dps = DPS(self, dps_dict)
