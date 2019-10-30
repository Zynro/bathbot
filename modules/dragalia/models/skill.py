class Skill:
    def __init__(self, skill_list):
        for k in skill_list[0].keys():
            if k == "Level":
                continue
            setattr(self, k, skill_list[0][k])
        self.levels = {}
        for row in skill_list:
            level = row["Level"]
            self.levels[level] = {"desc": row["description"], "sp_cost": row["sp_cost"]}

    def __call__(self):
        return self.name
