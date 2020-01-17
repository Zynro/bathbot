import modules.ffxiv.models.constants as CONST


class Parse:
    def __init__(self, parse_dict):
        for k in parse_dict.keys():
            i = k.lower()
            if i == "charactername":
                i = "name"
            elif k.lower() == "encountername":
                i = "fight"
            elif k.lower() == "spec":
                i = "job"
            elif k.lower() == "ilvlkeyorpatch":
                i = "patch"
            setattr(self, i, parse_dict[k])
        self.job = CONST.job_dict[self.job.lower()]

    def __call__(self):
        return
