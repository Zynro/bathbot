class Skill:
    def __init__(self, skill_list):
        for k, v in skill_list[0]:
            if k == "levels":
                continue
            setattr(self, k, skill_list[0][v])
        self.levels = {}
        for row in skill_list:
            level = skill["level"]
            self.levels[level] = {}
            self.levels[level]["desc"] = skill["description"]
            self.levels[level]["sp_cost"] = skill["sp_cost"]

    def __call__(self):
        return self.name
