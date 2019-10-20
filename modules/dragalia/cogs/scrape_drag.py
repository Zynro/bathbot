import aiosqlite as sql
import sqlite3
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

sql_make_adv_table = """
CREATE TABLE Adventurers(Name text PRIMARY KEY,
            Image text,
            Internal_Name text,
            Title text,
            Max_HP integer,
            Max_STR integer,
            Defense integer,
            Type text,
            Rarity integer,
            Element text,
            Weapon text,
            Max_CoAb text,
            Skill_1 text,
            Skill_2 text,
            Ability_1 text,
            Ability_2 text,
            Ability_3 text,
            Availability text,
            Release text,
            Shortcuts text
            )
"""

sql_make_skills_table = """
CREATE TABLE Skills(Name text PRIMARY KEY,
            Image text,
            Internal_Name text,
            Max_Level integer,
            SP_Cost integer,
            I_Frames text,
            Owners, text
            )
"""

sql_adven_insert = """
INSERT INTO Adventurers
(Name, Image, Internal_Name, Title, Max_HP, Max_STR, Type, Rarity, Element, Weapon, Max_CoAb, Skill_1, Skill_2, Ability_1, Ability_2, Ability_3, Availability, Release, Shortcuts)
VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
"""

sql_adven_update = """
UPDATE Adventurers
SET Title=?, Image=?, Internal_Name=?, Max_HP=?, Max_STR=?, Type=?, Rarity=?, Element=?, Weapon=?,
Max_CoAb=?, Skill_1=?, Skill_2=?, Ability_1=?, Ability_2=?, Ability_3=?, Availability=?, Release=?, Shortcuts=?
"""

sql_skill_insert = """
INSERT INTO Skills
(Name, Image, Internal_Name, Max_Level, SP_Cost, I_Frames, Owners)
"""

sql_skill_update = """
UPDATE Skills
SET Image=?, Internal_Name=?, Max_Level=?, SP_Cost=?, I_Frames=?, Owners=?)
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
                sql_adven_insert,
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
        divs = soup.find(style="flex-grow:1;text-align:center")
        divs = divs.find_all(style="width:100%")
        defense = divs[6].find(class_="dd-description").get_text()
        adv_type = unit_types[divs[7].select("img[alt]")[0]["alt"]]
        skill_sections = soup.find_all(class_="skill-section")
        skills = skill_sections[0].find_all(class_="skill-table skill-levels")
        skill_1 = skills[0].find("th").select("a[title]")[0]["title"]
        skill_2 = skills[1].find("th").select("a[title]")[0]["title"]
        max_coab = skill_sections[1].find("th").select("a[title]")[0]["title"]
        value = skill_sections[1].find(title="Lv5").get_text()
        max_coab = f"{max_coab}: {value.split('(')[0]}"

        abilities = {1: None, 2: None, 3: None}
        all_abilities = skill_sections[2].find_all(class_="skill-table skill-levels")
        x = 1
        for each in all_abilities:
            ability_title = each.find("th").select("a[title]")[0]["title"]
            print(ability_title)
            ability_value = each.find_all(class_="tabbertab")
            if not "Lv2" not in ability_value:
                ability_value = ability_value[0]
            else:
                ability_value = ability_value[1]
            ability_value = ability_value.find("p").get_text().split("(")[0]
            print(ability_value)
            abilities[x] = f"{ability_title}: {ability_value}"
            x += 1

        print(
            f"""
            {name}
            {title}
            {element}
            {weapon}
            {max_hp}
            {max_str}
            {defense}
            {adv_type}
            {skill_1}
            {skill_2}
            {max_coab}
            {abilities[1]}
            {abilities[2]}
            {abilities[3]}
            """
        )
        break


async def main():
    async with aiohttp.ClientSession() as session:
        async with sql.connect("master.db") as db:
            try:
                await db.execute("SELECT * from Adventurers")
            except sqlite3.OperationalError:
                await db.execute(sql_make_adv_table)
            await create_names(session, db)
            await update_db(session, db)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.close()
