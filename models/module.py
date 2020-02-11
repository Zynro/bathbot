def get_id(message):
    try:
        return int(message.id)
    except AttributeError:
        return int(message)


class Module:
    def __init__(self, name, path=None, cog_list=None, guild_access=None):
        self.name = name
        self.path = path
        self.cog_list = cog_list
        self.access = guild_access
        self.msg_lib = {}

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
        try:
            msg = int(message.id)
        except AttributeError:
            msg = int(message)
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
