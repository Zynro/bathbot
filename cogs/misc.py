from discord import Embed, Colour
from discord.ext import commands
import lib.misc_methods as MISC

CREDIT_CAT_URL = (
    "https://www.nerdwallet.com/blog/credit-cards/"
    "current-credit-card-bonus-categories/"
)


def scrape_categories():
    """
    Parses html from master link for credit card
    categories, returns dict of category pairs.
    """
    return


class Misc(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.session = bot.session

    async def generate_categories(self, ctx):
        """
        Accesses a list of categories for credit cards, parses, and returns
        a dict of each credit card's categories.
        """
        return

    @commands.command(name="chase", aliases=["freedom"])
    async def get_chase_freedom_cats(self, ctx):
        URL = "https://creditcards.chase.com/freedom-credit-cards/home"
        LINK_URL = "https://creditcards.chase.com/freedom-credit-cards/merchants#"

        resp = await MISC.async_fetch_text(self.session, URL)
        soup = MISC.bs4_parse_html(resp)

        soup_list = soup.find_all(class_="col-sm-4 col-xs-12 text-center no-gutter")
        # soup_list = [i.select("img[alt]")[0]["alt"] for i in soup_list]
        soup_list = [i.find("h2") for i in soup_list]
        result = [
            i.find("a").get_text().replace("opens in a new window ", "")
            for i in soup_list
        ]
        # result = [str.title(i.lower().replace("icon", "").strip()) for i in soup_list]
        activate = soup.find(class_="col-sm-12 col-xs-12 text-center")
        activate = soup.strong.contents[0]

        embed = Embed(
            title="Chase Freedom Current Quarterly Categories",
            description=f"__Activate By:__\n**{activate}**",
            colour=Colour(0x0853AE),
        )
        result = [
            f"[{i}]({LINK_URL}{''.join([x for x in i if x.isalpha()])})" for i in result
        ]
        embed.add_field(name="**__Current Categories:__**", value="\n".join(result))
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Misc(bot))
