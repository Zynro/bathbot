class Skill:
    def __init__(self, skill_db):
        self.internal_name = skill_db["internal_name"]
        self.name = skill_db["name"]
        self.image = skill_db["image"]
        self.owner = skill_db["owner"]
        self.i_frames = skill_db["i_frames"]
        self.levels = {}
        for level in skill_db["levels"]:
            self.levels[level] = {}
            self.levels[level]["desc"] = level["description"]
            self.levels[level]["sp_cost"] = level["sp_cost"]

    def get_title(self):
        return self.name

    def get_stats(self):
        stats = f""
