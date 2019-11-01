import aiosqlite as async_sql
import sqlite3
import aiohttp
import requests
from bs4 import BeautifulSoup

MAIN_URL = "https://dragalialost.gamepedia.com/"
ADVEN_LIST_URL = "https://dragalialost.gamepedia.com/Adventurer_List"

MASTER_DB = "master.db"

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
CREATE TABLE Adventurers(Name text,
            Image text,
            Internal_Name text PRIMARY KEY,
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


def fetch(URL):
    resp = requests.get(URL)
    return resp.text


async def async_fetch(session, URL):
    async with session.get(URL) as response:
        return await response.text()


def fill_names(conn):
    resp = fetch(ADVEN_LIST_URL)
    soup = BeautifulSoup(resp, "html.parser")
    for each in soup.find_all("tr", class_="character-grid-entry grid-entry"):
        td_list = each.find_all("td")

        name = td_list[1].select("a[title]")[0]["title"]
        image = td_list[0].select("img[src]")[0]["src"]
        internal_name = shorten_name(name)

        c = conn.cursor()
        c.execute("SELECT Name FROM Adventurers WHERE name = ?", (name,))
        result = c.fetchone()
        if result is None:
            c.execute(
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
    conn.commit()


def parse_adventurer(resp):
    adven = {}
    soup = BeautifulSoup(resp, "html.parser")
    p = soup.find(class_="panel-heading")
    adven["title"] = p.find_all("div")[0].get_text()
    adven["element"] = elements[p.select("img[alt]")[0]["alt"]]
    adven["weapon"] = weapons[p.select("img[alt]")[1]["alt"]]
    adven["max_hp"] = soup.find(id="adv-hp").get_text()
    adven["max_str"] = soup.find(id="adv-str").get_text()
    divs = soup.find(style="flex-grow:1;text-align:center")
    divs = divs.find_all(style="width:100%")
    adven["defense"] = divs[6].find(class_="dd-description").get_text()
    adven["adv_type"] = unit_types[divs[7].select("img[alt]")[0]["alt"]]
    adven["rarity"] = rarities[divs[10].select("img[alt]")[0]["alt"]]

    skill_sections = soup.find_all(class_="skill-section")

    all_skills = skill_sections[0].find_all(class_="skill-table skill-levels")
    adven["skill_1"] = all_skills[0].find("th").select("a[title]")[0]["title"]
    adven["skill_2"] = all_skills[1].find("th").select("a[title]")[0]["title"]

    max_coab = skill_sections[1].find("th").select("a[title]")[0]["title"]
    value = skill_sections[1].find(title="Lv5").get_text()
    adven["max_coab"] = f"{max_coab}: {value.split('(')[0]}"

    adven["abilities"] = {1: None, 2: None, 3: None}
    all_abilities = skill_sections[2].find_all(class_="skill-table skill-levels")
    for i, each in enumerate(all_abilities):
        ability_title = each.find("th").select("a[title]")[0]["title"]
        ability_value = each.find_all(class_="tabbertab")
        try:
            ability_value = ability_value[1].find("p").get_text().split("(")[0]
        except IndexError:
            ability_value = ability_value[0].find("p").get_text().split("(")[0]
        adven["abilities"][i + 1] = f"{ability_title}: {ability_value}"

    adven["obtained"] = divs[-3].find(class_="dd-description").get_text()
    adven["release"] = divs[-2].find(class_="dd-description").get_text()
    adven["avail"] = divs[-1].find(class_="dd-description").get_text()
    return adven


def parse_skill(resp, skill):
    s_soup = BeautifulSoup(resp, "html.parser")
    skill["image"] = s_soup.find(class_="tabbertab").select("img[src]")[0]["src"]
    skill["i_frames"] = s_soup.find_all(class_="dd-description")[-3].get_text()
    skill["owner"] = s_soup.find("li").select("a[title]")[0]["title"]
    all_levels = s_soup.find(class_="skill-levels skill-details")
    all_levels = all_levels.find_all(class_="tabbertab")
    skill["levels"] = {}
    for i in range(1, len(all_levels) + 1):
        skill_div = all_levels[i - 1]
        skill["levels"][i] = {"internal_name": "", "desc": "", "sp_cost": ""}
        y = True
        for br in skill_div.find_all("br"):
            if y is True:
                br.replace_with("\n")
                y = False
            else:
                y = True
                continue
        skill["levels"][i]["desc"] = (
            skill_div.find_all("div")[1].get_text().replace("\\'", "'")
        )
        sp_cost = skill_div.find_all(class_="dd-description")
        skill["levels"][i]["sp_cost"] = sp_cost[0].get_text()
        skill["levels"][i]["internal_name"] = f"{skill['name']}_{i}"
    return skill


def update_advs(conn, force=False):
    cursor = conn.cursor()
    full_list = cursor.execute("SELECT * FROM Adventurers")
    full_list = full_list.fetchall()
    for row in full_list:
        adven = {}
        name = row[0]
        update = False
        for entry in row[:-1]:
            if entry == "?" or not entry:
                update = True
            else:
                pass
        if not update and not force:
            # print(f"{name} already entered. Passing adventurer...")
            continue
        print(f"=====Updating: {name}=====")
        resp = fetch(f"{MAIN_URL}{name}")
        adven = parse_adventurer(resp)
        cursor.execute(
            sql_adven_update,
            (
                adven["title"],
                adven["max_hp"],
                adven["max_str"],
                adven["defense"],
                adven["adv_type"],
                adven["rarity"],
                adven["element"],
                adven["weapon"],
                adven["max_coab"],
                adven["skill_1"],
                adven["skill_2"],
                adven["abilities"][1],
                adven["abilities"][2],
                adven["abilities"][3],
                adven["avail"],
                adven["obtained"],
                adven["release"],
                name,
            ),
        )
        conn.commit()
        print(f"++++Updated!++++")


def update_skills(conn, force=False):
    cursor = conn.cursor()
    full_skill_list = cursor.execute("SELECT * FROM Skills")
    full_skill_list = full_skill_list.fetchall()
    full_adven_list = cursor.execute("SELECT * FROM Adventurers")
    full_adven_list = full_adven_list.fetchall()
    skill_update = {}
    for row in full_skill_list:
        name = row[1]
        if not full_skill_list:
            force = True
            break
        for entry in row[:-1]:
            if not entry or entry == "?":
                skill_update[name] = True
                break
            else:
                skill_update[name] = False

    for index in range(len(full_adven_list)):
        skills = {
            1: {"name": full_adven_list[index][12]},
            2: {"name": full_adven_list[index][13]},
        }
        for x in skills.keys():
            name = skills[x]["name"]
            try:
                update = skill_update[name]
            except KeyError:
                update = True
            if not update and not force:
                # print(f"    {name} already entered. Passing skill...")
                continue
            resp = fetch(f"{MAIN_URL}{skills[x]['name'].replace(' ', '_')}")
            skills[x].update(parse_skill(resp, skills[x]))
            skill = skills[x]
            for i in skill["levels"].keys():
                print(
                    (
                        f"    Updating: {skill['owner']}'s "
                        f"{skill['levels'][i]['internal_name']}"
                    )
                )
                cursor = cursor.execute(
                    "SELECT Name FROM Skills WHERE Internal_Name = ?",
                    (skill["levels"][i]["internal_name"],),
                )
                result = cursor.fetchone()
                if not result:
                    cursor.execute(
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
                    print("     New Skill Added!")
                else:
                    cursor.execute(
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
                    print("    Skill updated!")
                conn.commit()


async def async_fill_names(session, db):
    resp = await async_fetch(session, ADVEN_LIST_URL)
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


async def aysnc_update_advs(session, db, force=False):
    full_list = await db.execute("SELECT * FROM Adventurers")
    full_list = await full_list.fetchall()
    for row in full_list:
        adven = {}
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
        resp = await async_fetch(session, f"{MAIN_URL}{name}")
        adven = parse_adventurer(resp)
        await db.execute(
            sql_adven_update,
            (
                adven["title"],
                adven["max_hp"],
                adven["max_str"],
                adven["defense"],
                adven["adv_type"],
                adven["rarity"],
                adven["element"],
                adven["weapon"],
                adven["max_coab"],
                adven["skill_1"],
                adven["skill_2"],
                adven["abilities"][1],
                adven["abilities"][2],
                adven["abilities"][3],
                adven["avail"],
                adven["obtained"],
                adven["release"],
                name,
            ),
        )
        await db.commit()
        print(f"++++Updated!++++")


async def async_update_skills(session, db, force=False):
    full_skill_list = await db.execute("SELECT * FROM Skills")
    full_skill_list = await full_skill_list.fetchall()
    full_adven_list = await db.execute("SELECT * FROM Adventurers")
    full_adven_list = await full_adven_list.fetchall()
    skill_update = {}
    for row in full_skill_list:
        name = row[1]
        if not full_skill_list:
            force = True
            break
        for entry in row[:-1]:
            if not entry or entry == "?":
                skill_update[name] = True
                break
            else:
                skill_update[name] = False

    for index in range(len(full_adven_list)):
        skills = {
            1: {"name": full_adven_list[index][12]},
            2: {"name": full_adven_list[index][13]},
        }
        for x in skills.keys():
            name = skills[x]["name"]
            try:
                update = skill_update[name]
            except KeyError:
                update = True
            if not update and not force:
                print(f"    {name} already entered. Passing skill...")
                continue
            resp = await async_fetch(
                session, f"{MAIN_URL}{skills[x]['name'].replace(' ', '_')}"
            )
            skills[x].update(parse_skill(resp, skills[x]))
            skill = skills[x]
            for i in skill["levels"].keys():
                print(
                    (
                        f"    Updating: {skill['owner']}'s "
                        f"{skill['levels'][i]['internal_name']}"
                    )
                )
                cursor = await db.execute(
                    "SELECT Name FROM Skills WHERE Internal_Name = ?",
                    (skill["levels"][i]["internal_name"],),
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


class Update:
    def __init__(self, db_file):
        self.db_file = db_file

    def full_update(self, force=False):
        with sqlite3.connect(self.db_file) as conn:
            c = conn.cursor()
            try:
                c.execute("SELECT * from Adventurers")
            except sqlite3.OperationalError:
                c.execute(sql_make_adv_table)
            try:
                c.execute("SELECT * from Skills")
            except sqlite3.OperationalError:
                c.execute(sql_make_skills_table)
            fill_names(conn)
            update_advs(conn, force)
            update_skills(conn, force)

    async def async_full_update(self, force=False):
        async with aiohttp.ClientSession() as session:
            async with async_sql.connect(self.db_file) as db:
                try:
                    await db.execute("SELECT * from Adventurers")
                except sqlite3.OperationalError:
                    await db.execute(sql_make_adv_table)
                try:
                    await db.execute("SELECT * from Skills")
                except sqlite3.OperationalError:
                    await db.execute(sql_make_skills_table)
                await async_fill_names(session, db)
                await aysnc_update_advs(session, db, force)
                await async_update_skills(session, db, force)

    def update(self, conn, data):
        if data == "adven":
            fill_names(conn)
            update_advs(conn)
        elif data == "skills":
            update_skills(conn)
