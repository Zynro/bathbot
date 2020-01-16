import lib.misc_methods as MISC
import modules.ffxiv.models.constants as CONST

API_URL = "https://xivapi.com"


def xiv_char_search(name, server=None, page=None):
    """
    Given a name, server (optional), and a page(optional),
    returns a XIV API endpoint URL for searching Characters.
    """
    string = f"{API_URL}/character/search?name={name}"
    if server:
        string += f"&server={server}"
    if page:
        string += f"&page={page}"
    return string


class XIVChar:
    """
    A class to contain specific characters and some assorted methods.
    """

    def __init__(self, name, char_id, server, thumbnail):
        self.name = name
        self.id = char_id
        self.thumbnail = thumbnail
        self.server = server.split("(")[0].strip()
        return

    @classmethod
    def parse_chars(cls, json_resp, name, server):
        char_results = []
        for char in json_resp:
            char_results.append(
                cls(char["Name"], char["ID"], char["Server"], char["Avatar"])
            )
        return char_results


class XIVAPI:
    def __init__(self, session):
        self.session = session

    async def api_get_results(self, url):
        """
        Gets all search results for a given url, checks all pages.
        """
        json_resp = await MISC.async_get_json(self.session, url)
        if json_resp["Pagination"]["Page"] > 1:
            for page in range(2, json_resp["Pagination"]["PageTotal"] + 1):
                next_page = await MISC.async_get_json(
                    self.session, f"{url}&page={page}"
                )
                json_resp["Results"].append(next_page)
        return json_resp["Results"]

    def xiv_get_chars(cls, name, server=None, page=None):
        json_resp = MISC.async_get_json(xiv_char_search(name, server, page))
        results = XIVChar.parse_chars(json_resp, name, server)
        return XIVChar()
