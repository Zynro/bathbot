from modules.dragalia.models.dps import DPS


class Adventurer:
    def __init__(self, adven_db, skills, dps_dict):
        self.name = adven_db["name"]
        self.image = adven_db["image"]
        self.internal_name = adven_db["internal_name"]
        self.title = adven_db["title"]
        self.max_hp = adven_db["max_hp"]
        self.max_str = adven_db["max_str"]
        self.defense = adven_db["defense"]
        self.unit_type = adven_db["type"]
        self.rarity = adven_db["rarity"]
        self.element = adven_db["element"]
        self.weapon = adven_db["weapon"]
        self.max_coab = adven_db["max_coab"]
        self.skill_1 = skills[0]
        self.skill_2 = skills[1]
        self.ability_1 = adven_db["ability_1"]
        self.ability_2 = adven_db["ability_2"]
        self.ability_3 = adven_db["ability_3"]
        self.availability = adven_db["availability"]
        self.obtained = adven_db["obtained"]
        self.release = adven_db["release"]
        self.dps = DPS(self, dps_dict)
