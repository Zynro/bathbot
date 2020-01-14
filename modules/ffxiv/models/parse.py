job_dict = {
    "warrior": "WAR",
    "paladin": "PLD",
    "gunbreaker": "GNB",
    "dragoon": "DRG",
    "monk": "MNK",
    "ninja": "NIN",
    "samurai": "SAM",
    "bard": "BRD",
    "machinist": "MCH",
    "black mage": "BLM",
    "summoner": "SMN",
    "white mage": "WHM",
    "scholar": "SCH",
    "astrologian": "AST",
    "dark knight": "DRK",
    "dancer": "DNC",
    "red mage": "RDM",
}


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
        self.job = job_dict[self.job.lower()]

    def __call__(self):
        return
