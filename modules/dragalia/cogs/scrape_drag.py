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
            Owner, text
            )
"""

sql_adven_insert = """
INSERT INTO Adventurers
(Name, Image, Internal_Name, Title, Max_HP, Max_STR, Type, Rarity, Element, Weapon,
    Max_CoAb, Skill_1, Skill_2, Ability_1, Ability_2, Ability_3,
    Availability, Release, Shortcuts)
VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
"""

sql_adven_update = """
UPDATE Adventurers
SET Title=?, Image=?, Internal_Name=?, Max_HP=?, Max_STR=?, Type=?, Rarity=?, Element=?,
    Weapon=?, Max_CoAb=?, Skill_1=?, Skill_2=?,
    Ability_1=?, Ability_2=?, Ability_3=?, Availability=?, Release=?
"""

sql_skill_insert = """
INSERT INTO Skills
(Name, Image, Internal_Name, Max_Level, SP_Cost, I_Frames, Owner)
"""

sql_skill_update = """
UPDATE Skills
SET Image=?, Internal_Name=?, Max_Level=?, SP_Cost=?, I_Frames=?, Owner=?)
"""


def shorten_name(name):
    split = name.split(" ")
    if len(split) == 1:
        return name.lower()
    return f"{split[0][0].lower()}{split[1].lower()}"


async def fetch(session, URL):
    async with session.get(URL) as response:
        return await response.text()


async def create_dbs(session, db):
    resp = await fetch(session, ADVEN_LIST_URL)
    soup = BeautifulSoup(resp, "html.parser")
    for each in soup.find_all("tr", class_="character-grid-entry grid-entry"):
        td_list = each.find_all("td")

        name = td_list[1].select("a[title]")[0]["title"]
        image = td_list[0].select("img[src]")[0]["src"]
        internal_name = shorten_name(name)

        cursor = await db.execute(
            "SELECT Name FROM Adventurers WHERE name = ?", (name,)
        )
        result = await cursor.fetchone()
        if result is None:
            await db.execute(
                sql_adven_insert,
                (
                    name,
                    image,
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


async def update_advs(session, db):
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

        all_skills = skill_sections[0].find_all(class_="skill-table skill-levels")
        skill_1 = all_skills[0].find("th").select("a[title]")[0]["title"]
        skill_2 = all_skills[1].find("th").select("a[title]")[0]["title"]
        skills = await update_skills(
            session, db, skill_1, skill_2
        )  # REMOVE VAR ASSIGNMENT LATER

        max_coab = skill_sections[1].find("th").select("a[title]")[0]["title"]
        value = skill_sections[1].find(title="Lv5").get_text()
        max_coab = f"{max_coab}: {value.split('(')[0]}"

        abilities = {1: None, 2: None, 3: None}
        all_abilities = skill_sections[2].find_all(class_="skill-table skill-levels")
        x = 1
        for each in all_abilities:
            ability_title = each.find("th").select("a[title]")[0]["title"]
            ability_value = each.find_all(class_="tabbertab")
            if not "Lv2" not in ability_value:
                ability_value = ability_value[0]
            else:
                ability_value = ability_value[1]
            ability_value = ability_value.find("p").get_text().split("(")[0]
            abilities[x] = f"{ability_title}: {ability_value}"
            x += 1

        release = divs[16].find(class_="dd-description").get_text()
        avail = divs[17].find(class_="dd-description").get_text()

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
            {skills[1]['name']}
            {skills[1]['desc']}
            {skills[1]['sp_cost']}
            {skills[1]['i_frames']}
            {skills[1]['owner']}
            {skills[2]['name']}
            {skills[2]['desc']}
            {skills[2]['sp_cost']}
            {skills[2]['i_frames']}
            {skills[2]['owner']}
            {max_coab}
            {abilities[1]}
            {abilities[2]}
            {abilities[3]}
            {release}
            {avail}
            """
        )
        break


async def update_skills(session, db, skill_1, skill_2):
    skills = {
        1: {"name": skill_1, "desc": "", "sp_cost": "", "i_frames": "", "owner": ""},
        2: {"name": skill_2, "desc": "", "sp_cost": "", "i_frames": "", "owner": ""},
    }
    x = 1
    for skill in skills.items():
        resp = await fetch(session, f"{MAIN_URL}{skills[x]['name'].replace(' ', '_')}")
        skill_soup = BeautifulSoup(resp, "html.parser")
        all_levels = skill_soup.find(class_="skill-levels skill-details")
        skill = all_levels.find(title="Lv3")
        if not skill:
            skill = all_levels.find(title="Lv2")
        y = True
        for br in skill.find_all("br"):
            if y is True:
                br.replace_with("\n")
                y = False
            else:
                y = True
                continue
        skills[x]["desc"] = skill.find_all("div")[1].get_text().replace("\\'", "'")
        sp_cost = skill.find_all(class_="dd-description")
        skills[x]["sp_cost"] = sp_cost[0].get_text()
        skill_divs = skill_soup.find_all(class_="dd-description")
        skills[x]["i_frames"] = skill_divs[-3].get_text()
        skills[x]["owner"] = skill_soup.find("li").select("a[title]")[0]["title"]
        x += 1
    return skills  # REMOVE VAR ASSIGNMENT LATER


async def main():
    async with aiohttp.ClientSession() as session:
        async with sql.connect("master.db") as db:
            try:
                await db.execute("SELECT * from Adventurers")
            except sqlite3.OperationalError:
                await db.execute(sql_make_adv_table)
            try:
                await db.execute("SELECT * from Skills")
            except sqlite3.OperationalError:
                await db.execute(sql_make_skills_table)
            await create_dbs(session, db)
            await update_advs(session, db)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.close()
