from discord import Embed, Colour
import lib.misc_methods as MISC
import modules.ffxiv.models.constants as CONST

API_URL = "https://xivapi.com"
API_URL_SEARCH = "https://xivapi.com/search?string="


def xiv_url_gen(name, server=None, page=None):
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
    A class to contain specific characters and some related assorted methods.
    """

    def __init__(self, name, char_id, server, thumbnail):
        self.name = str.title(name)
        self.id = char_id
        self.thumbnail = thumbnail
        split = server.split("(")
        self.server = str.title(split[0].strip())
        self.region = CONST["".join([c for c in split[1] if c.isalpha()])]
        return

    @classmethod
    def parse_chars(cls, json_resp, name, server):
        char_results = []
        for char in json_resp:
            char_results.append(
                cls(char["Name"], char["ID"], char["Server"], char["Avatar"])
            )
        return char_results

    def to_string(self):
        return f"{self.name} @ {self.server}"


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

    def xiv_get_chars(self, name, server=None, page=None):
        url = xiv_url_gen(name, server, page)
        json_resp = MISC.async_get_json(self.session, url)
        results = XIVChar.parse_chars(json_resp, name, server)
        return results

    async def xiv_find_item(self, item):
        item = item.lower().strip()
        results = []
        json_result = await MISC.async_get_json(self.session, f"{API_URL_SEARCH}{item}")
        for each in json_result["Results"]:
            if each["UrlType"] == "Item":
                results.append((each["Name"], each["ID"]))
        return results

    async def universalis_embed(self, results):
        embed = Embed(
            title=f"FFXIV Universalis Marketboard", colour=Colour(MISC.rand_color())
        )
        if len(results) == 0:
            embed.add_field(
                name="__Error:__", value=f"No results were found for the search term."
            )
            return embed
        elif len(results) > 1 < 20:
            results = "\n".join([x[0] for x in results])
            embed.add_field(name="**Multiple Results Found**:", value=results)
            embed.set_footer(text="Try searching again with a more specific term.")
            return embed
        else:
            embed.add_field(
                name="**Error:**",
                value=f"There are either too much results"
                " to display, or an unknown error has occured.",
            )
            return embed
