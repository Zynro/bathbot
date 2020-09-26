import json


def get_id(message):
    try:
        return int(message.id)
    except AttributeError:
        return int(message)


def load_access(module):
    try:
        with open(f"tokens/module_access.json") as file:
            access = json.loads(file.read())
        return access[module]
    except (FileNotFoundError, IndexError):
        return None


def module_access_writeout(module, access_list):
    path_to_file = f"tokens/module_access.json"
    with open(f"tokens/module_access.json") as file:
        access_dict = json.loads(file.read())
    access_dict[module] = access_list
    with open(path_to_file, "w+") as file:
        json.dump(access_dict, file, indent=4)
    return


class Module:
    def __init__(self, name, path=None, cog_list=None):
        self.name = name.lower()
        self.path = path
        self.cog_list = cog_list
        self.access = load_access(self.name)
        self.msg_lib = {}

    def add_access(self, guild_id):
        if not self.access:
            self.access = [guild_id]
        else:
            self.access.append(guild_id)
        module_access_writeout(self.name, self.access)

    def remove_access(self, guild_id):
        self.access.remove(guild_id)
        module_access_writeout(self.name, self.access)

    def add_msg(self, message, **kwargs):
        msg_id = get_id(message)
        self.msg_lib[msg_id] = {"msg": message}
        for k in kwargs.keys():
            try:
                key = k.lower()
                val = kwargs[k].lower()
            except Exception:
                val = kwargs[k]
            self.msg_lib[msg_id][key] = val

    def del_msg(self, message):
        msg = get_id(message)
        del self.msg_lib[msg]

    async def fetch_msg(self, message):
        return await message.fetch_message(int(message.id))

    def set_msg_vals(self, message, **vals):
        msg_id = get_id(message)
        for k in vals.keys():
            try:
                key = k.lower()
                val = vals[k].lower()
            except Exception:
                val = vals[k]
            self.msg_lib[msg_id][key] = val

    def set_msg_val(self, message, key, val):
        msg_id = get_id(message)
        self.msg_lib[msg_id][key] = val
        return val
