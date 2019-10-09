def strip_tuple(input_tuple):
    input_tuple = input_tuple.replace("(", "")
    input_tuple = input_tuple.replace(")", "")
    input_tuple = input_tuple.replace("'", "")
    input_tuple = input_tuple.strip()
    return input_tuple


class Parse:
    def __init__(self, parse_dict):
        self.dps = strip_tuple(str(parse_dict["damage"]["dps"]))
        self.damage_types = parse_dict["damage"]["types"]
        self.condition = strip_tuple(str(parse_dict["condition"]))
        self.condition = self.condition.replace(",", "")
        self.comment = strip_tuple(str(parse_dict["comment"]))
        self.rank_element = None
        self.rank_overall = None

    def type_to_string(self):
        to_string_list = []
        for dmg_type in self.damage_types.keys():
            appending = f"{dmg_type}: {self.damage_types[dmg_type]}"
            to_string_list.append(appending)
        return "\n".join(to_string_list)
