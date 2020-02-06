class Module:
    def __init__(self, name, path=None, cog_list=None, guild_access=None):
        self.name = name
        self.path = path
        self.cog_list = cog_list
        self.access = guild_access
        self.msg_lib = {}

    def add_msg(self, message):
        try:
            msg = int(message.id)
        except AttributeError:
            msg = int(message)
        self.msg_lib[msg] = {"id": msg}

    def del_msg(self, message):
        try:
            msg = int(message.id)
        except AttributeError:
            msg = int(message)
        del self.msg_lib[msg]

    async def fetch_msg(messageable, msg_id):
        return await messageable.fetch_message(int(msg_id))

    def set_vals(self, msg_id, vals):
        for k in vals.keys():
            try:
                key = k.lower()
                val = vals[k].lower()
            except Exception:
                val = vals[k]
            setattr(self, key, val)
