class Skill:
    def __init__(self, skill_list):
        skill = skill_list[0]
        self.internal_name = skill["internal_name"]
        self.name = skill["name"]
        self.image = skill["image"]
        self.owner = skill["owner"]
        self.i_frames = skill["i_frames"]
        self.levels = {}
        for row in skill_list:
            level = skill["level"]
            self.levels[level] = {}
            self.levels[level]["desc"] = skill["description"]
            self.levels[level]["sp_cost"] = skill["sp_cost"]

    def __call__(self):
        return self.name
