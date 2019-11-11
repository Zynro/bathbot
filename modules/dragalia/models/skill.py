class Skill:
    def __init__(self, skill_list):
        for k in skill_list[0].keys():
            if k == "Level":
                continue
            setattr(self, k.lower(), skill_list[0][k])
        self.levels = {}
        for row in skill_list:
            level = row["Level"]
            self.levels[level] = {"desc": row["description"], "sp_cost": row["sp_cost"]}

    def __call__(self):
        return self.name

    def adven_embed(self):
        try:
            level = self.levels[3]
            level = 3
        except KeyError:
            level = self.levels[2]
            level = 2
        embed_title = (
            f"{self.name} [SP: {self.levels[level]['sp_cost']}] "
            f"[i-Frames: {self.i_frames}]"
        )
        embed_value = self.levels[level]["desc"]
        return [embed_title, embed_value]
