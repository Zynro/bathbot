from modules.dragalia.models.dps import DPS


class Adventurer:
    def __init__(self, adven_db, skills, dps_dict):
        for k in adven_db.keys():
            setattr(self, k, adven_db[k])
        self.dps = DPS(self, dps_dict)
