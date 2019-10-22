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
            Obtained text,
            Release text,
            Shortcuts text
            )
"""

sql_make_skills_table = """
CREATE TABLE Skills(Internal_Name text PRIMARY KEY,
            Name text,
            Image text,
            Owner text,
            Level integer,
            Description text,
            SP_Cost integer,
            I_Frames text
            )
"""

sql_adven_insert = """
INSERT INTO Adventurers
(Name, Image, Internal_Name, Title, Max_HP, Max_STR, Defense, Type, Rarity, Element,
    Weapon, Max_CoAb, Skill_1, Skill_2, Ability_1, Ability_2, Ability_3,
    Availability, Obtained, Release, Shortcuts)
VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
"""

sql_skill_insert = """
INSERT INTO Skills
(Internal_Name, Name, Image, Owner, Level, Description, SP_Cost, I_Frames)
VALUES (?,?,?,?,?,?,?,?)
"""

sql_adven_update = """
UPDATE Adventurers
SET Title=?, Max_HP=?, Max_STR=?, Defense=?, Type=?, Rarity=?, Element=?,
    Weapon=?, Max_CoAb=?, Skill_1=?, Skill_2=?,
    Ability_1=?, Ability_2=?, Ability_3=?, Availability=?, Obtained=?, Release=?
WHERE Name=?
"""

sql_skill_update = """
UPDATE Skills
SET Image=?, Owner=?, Level=?, Description=?, SP_Cost=?, I_Frames=?
WHERE Internal_Name=?
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
                    internal_name,
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
                    "?",
                    "?",
                    "?",
                    "?",
                    "?",
                ),
            )
    await db.commit()


async def update_advs(session, db, force=False):
    full_list = await db.execute("SELECT * FROM Adventurers")
    full_list = await full_list.fetchall()
    for row in full_list:
        name = row[0]
        update = False
        for entry in row[:-1]:
            if entry == "?" or not entry:
                update = True
            else:
                pass
        if not update and not force:
            print(f"{name} already entered. Passing adventurer...")
            continue
        print(f"=====Updating: {name}=====")
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
        rarity = rarities[divs[10].select("img[alt]")[0]["alt"]]

        skill_sections = soup.find_all(class_="skill-section")

        all_skills = skill_sections[0].find_all(class_="skill-table skill-levels")
        skill_1 = all_skills[0].find("th").select("a[title]")[0]["title"]
        skill_2 = all_skills[1].find("th").select("a[title]")[0]["title"]
        await update_skills(session, db, skill_1, skill_2, force)

        max_coab = skill_sections[1].find("th").select("a[title]")[0]["title"]
        value = skill_sections[1].find(title="Lv5").get_text()
        max_coab = f"{max_coab}: {value.split('(')[0]}"

        abilities = {1: None, 2: None, 3: None}
        all_abilities = skill_sections[2].find_all(class_="skill-table skill-levels")
        x = 1
        for each in all_abilities:
            ability_title = each.find("th").select("a[title]")[0]["title"]
            ability_value = each.find_all(class_="tabbertab")
            ability_value = ability_value[0].find("p").get_text().split("(")[0]
            abilities[x] = f"{ability_title}: {ability_value}"
            x += 1

        obtained = divs[-3].find(class_="dd-description").get_text()
        release = divs[-2].find(class_="dd-description").get_text()
        avail = divs[-1].find(class_="dd-description").get_text()

        await db.execute(
            sql_adven_update,
            (
                title,
                max_hp,
                max_str,
                defense,
                adv_type,
                rarity,
                element,
                weapon,
                max_coab,
                skill_1,
                skill_2,
                abilities[1],
                abilities[2],
                abilities[3],
                avail,
                obtained,
                release,
                name,
            ),
        )
        await db.commit()
        print(f"++++Updated!++++")


async def update_skills(session, db, skill_1, skill_2, force=False):
    full_list = await db.execute("SELECT * FROM Skills")
    full_list = await full_list.fetchall()
    if not full_list:
        update = True
    else:
        for row in full_list:
            name = row[0]
            for row in full_list:
                update = True
                for entry in row[:-1]:
                    if not entry or entry == "?":
                        update = True
                    else:
                        pass
    skills = {
        1: {"name": skill_1, "i_frames": "", "owner": "", "levels": {}},
        2: {"name": skill_2, "i_frames": "", "owner": "", "levels": {}},
    }
    x = 1
    for skill in skills.items():
        if not update and not force:
            print(f"    {name} already entered. Passing skill...")
            continue
        resp = await fetch(session, f"{MAIN_URL}{skills[x]['name'].replace(' ', '_')}")
        s_soup = BeautifulSoup(resp, "html.parser")
        skills[x]["image"] = s_soup.find(class_="tabbertab").select("img[src]")[0][
            "src"
        ]
        skills[x]["i_frames"] = s_soup.find_all(class_="dd-description")[-3].get_text()
        skills[x]["owner"] = s_soup.find("li").select("a[title]")[0]["title"]
        all_levels = s_soup.find(class_="skill-levels skill-details")
        all_levels = all_levels.find_all(class_="tabbertab")
        for i in range(1, len(all_levels) + 1):
            skill_div = all_levels[i - 1]
            skills[x]["levels"][i] = {"internal_name": "", "desc": "", "sp_cost": ""}
            y = True
            for br in skill_div.find_all("br"):
                if y is True:
                    br.replace_with("\n")
                    y = False
                else:
                    y = True
                    continue
            skills[x]["levels"][i]["desc"] = (
                skill_div.find_all("div")[1].get_text().replace("\\'", "'")
            )
            sp_cost = skill_div.find_all(class_="dd-description")
            skills[x]["levels"][i]["sp_cost"] = sp_cost[0].get_text()
            skills[x]["levels"][i]["internal_name"] = f"{skills[x]['name']}_{i}"
        x += 1
    x = 1
    for skill in skills.keys():
        skill = skills[skill]
        i = 1
        for skill_level in skill["levels"].values():
            print(f"    Updating: {skill_level['internal_name']}")
            cursor = await db.execute(
                "SELECT Name FROM Skills WHERE Internal_Name = ?",
                (skill_level["internal_name"],),
            )
            result = await cursor.fetchone()
            if not result:
                await db.execute(
                    sql_skill_insert,
                    (
                        skills[x]["levels"][i]["internal_name"],
                        skills[x]["name"],
                        skills[x]["image"],
                        skills[x]["owner"],
                        i,
                        skills[x]["levels"][i]["desc"],
                        skills[x]["levels"][i]["sp_cost"],
                        skills[x]["i_frames"],
                    ),
                )
            else:
                await db.execute(
                    sql_skill_update,
                    (
                        skills[x]["image"],
                        skills[x]["owner"],
                        i,
                        skills[x]["levels"][i]["desc"],
                        skills[x]["levels"][i]["sp_cost"],
                        skills[x]["i_frames"],
                        skills[x]["levels"][i]["internal_name"],
                    ),
                )
            await db.commit()
            print("    Updated!")
            i += 1
        x += 1


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
