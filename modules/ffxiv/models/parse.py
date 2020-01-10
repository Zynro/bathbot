class Parse:
    def __init__(self, parse_dict):
        for k in parse_dict.keys():
            k = k.lower()
            setattr(self, k, parse_dict[k])
        return

    def __call__(self):
        return
