import aiosqlite as sql
import asyncio
import aiohttp
from bs4 import BeautifulSoup

MAIN_URL = "https://dragalialost.gamepedia.com/"
ADVEN_LIST_URL = "https://dragalialost.gamepedia.com/Adventurer_List"

elements = {
    "Icon Element Flame.png": "Flame",
    "Icon Element Water.png": "Water",
    "Icon Element Wind.png": "Wind",
    "Icon Element Light.png": "Light",
    "Icon Element Shadow.png": "Shadow",
}
weapons = {
    "Icon Weapon Sword.png": "Sword",
    "Icon Weapon Blade.png": "Blade",
    "Icon Weapon Dagger.png": "Dagger",
    "Icon Weapon Axe.png": "Axe",
    "Icon Weapon Lance.png": "Lance",
    "Icon Weapon Bow.png": "Bow",
    "Icon Weapon Wand.png": "Wand",
    "Icon Weapon Staff.png": "Staff",
}
unit_types = {
    "Icon Type Row Attack.png": "Attack",
    "Icon Type Row Defense.png": "Defense",
    "Icon Type Row Healing.png": "Healing",
    "Icon Type Row Support.png": "Support",
}
rarities = {
    "Icon Rarity Row 1.png": 1,
    "Icon Rarity Row 2.png": 2,
    "Icon Rarity Row 3.png": 3,
    "Icon Rarity Row 4.png": 4,
    "Icon Rarity Row 5.png": 5,
}

sql_adven_input = """
INSERT INTO Adventurers
(Name, Title, Max_HP, Max_STR, Type, Rarity, Element, Weapon, Max_CoAb, Skill_1,
    Skill_2, Ability_1, Ability_2, Ability_3, Internal_Name, Shortcuts)
VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
"""

sql_adven_update = """
UPDATE Adventurers
SET Title=?, Max_HP=?, Max_STR=?, Type=?, Rarity=?, Element=?, Weapon=?,
Max_CoAb=?, Skill_1=?, Skill_2=?, Ability_1=?, Ability_2=?, Ability_3=?, Internal_Name=?
"""


def shorten_name(name):
    split = name.split(" ")
    if len(split) == 1:
        return name.lower()
    return f"{split[0][0].lower()}{split[1].lower()}"


async def fetch(session, URL):
    async with session.get(URL) as response:
        return await response.text()


async def create_names(session, db):
    resp = await fetch(session, ADVEN_LIST_URL)
    soup = BeautifulSoup(resp, "html.parser")
    for each in soup.find_all("tr", class_="character-grid-entry grid-entry"):
        td_list = each.find_all("td")

        name = td_list[1].select("a[title]")[0]["title"]
        internal_name = shorten_name(name)

        """rarity = td_list[2].find_all("div")[0].get_text()
        element = td_list[3].find("div").get_text()
        weapon = td_list[4].find("div").get_text()
        a_type = unit_types[td_list[5].select("img[alt]")[0]["alt"]]
        max_hp = td_list[6].get_text()
        max_str = td_list[7].get_text()
        print(f"Adding Character: {name}")"""

        cursor = await db.execute(
            "SELECT Name FROM Adventurers WHERE name = ?", (name,)
        )
        result = await cursor.fetchone()
        if result is None:
            await db.execute(
                sql_adven_input,
                (
                    name,
                    "?",
                    "?",
                    "?",
                    "?",
                    "?",
                    "?",
                    "?",
                    "?",
                    "?",
                    "?",
                    "?",
                    "?",
                    "?",
                    internal_name,
                    "?",
                ),
            )
    await db.commit()


async def update_db(session, db):
    full_list = await db.execute("SELECT * FROM Adventurers")
    full_list = await full_list.fetchall()
    for row in full_list:
        name = row[0]
        resp = await fetch(session, f"{MAIN_URL}{name}")
        soup = BeautifulSoup(resp, "html.parser")
        p = soup.find(class_="panel-heading")
        title = p.find_all("div")[0].get_text()
        element = elements[p.select("img[alt]")[0]["alt"]]
        weapon = weapons[p.select("img[alt]")[1]["alt"]]
        max_hp = soup.find(id="adv-hp").get_text()
        max_str = soup.find(id="adv-str").get_text()
        defense = soup.find(class_="dd-description").get_text()  # use for loop to find
        print(
            f"""
            {name}
            {title}
            {element}
            {weapon}
            {max_hp}
            {max_str}
            {defense}
            """
        )
        break


async def main():
    async with aiohttp.ClientSession() as session:
        async with sql.connect("master.db") as db:
            await create_names(session, db)
            await update_db(session, db)


if __name__ == "__main__":
    asyncio.run(main())
