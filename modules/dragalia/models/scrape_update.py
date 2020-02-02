import aiosqlite as async_sql
import sqlite3
import requests
from bs4 import BeautifulSoup
import lib.misc_methods as MISC
import modules.dragalia.models.constants as CONSTANTS

MAIN_URL = "https://dragalialost.gamepedia.com/"
ADVEN_LIST_URL = "https://dragalialost.gamepedia.com/Adventurer_List"
WYRMPRINT_LIST_URL = "https://dragalialost.gamepedia.com/Category:Wyrmprints"

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

exceptions = {"the prince": "Euden", "gala prince": "Gala Euden"}

###################
# Table Creations #
###################

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
            Obtained text,
            Release text,
            Availability text,
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

sql_make_wyrmprints_table = """
CREATE TABLE Wyrmprints(Name text PRIMARY KEY,
            Thumbnail text,
            Image text,
            Max_HP integer,
            Max_STR integer,
            Rarity text,
            Ability_1 text,
            Ability_2 text,
            Ability_3 text,
            Obtained text,
            Release text,
            Availability text,
            Shortcuts text
            )
            """

###############
# SQL Inserts #
###############
# These originally pull the informaiton from the list view, some additional info is
# also pulled but otherwise it will be pulled from each individual print's page.

sql_adven_insert = """
INSERT INTO Adventurers
(Name, Image, Internal_Name, Title, Max_HP, Max_STR, Defense, Type, Rarity, Element,
    Weapon, Max_CoAb, Skill_1, Skill_2, Ability_1, Ability_2, Ability_3,
    Obtained, Release, Availability, Shortcuts)
VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
"""

sql_skill_insert = """
INSERT INTO Skills
(Internal_Name, Name, Image, Owner, Level, Description, SP_Cost, I_Frames)
VALUES (?,?,?,?,?,?,?,?)
"""

sql_wp_insert = """
INSERT INTO Wyrmprints
(Name, Thumbnail, Image, Max_HP, Max_STR, Rarity, Ability_1, Ability_2,
    Ability_3, Obtained, Release, Availability, Shortcuts)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
"""

###############
# SQL Updates #
###############
# Finishes filling out the informaiton per print from before, ignoring already existing
# information.

sql_adven_update = """
UPDATE Adventurers
SET Title=?, Max_HP=?, Max_STR=?, Defense=?, Type=?, Rarity=?, Element=?,
    Weapon=?, Max_CoAb=?, Skill_1=?, Skill_2=?,
    Ability_1=?, Ability_2=?, Ability_3=?, Obtained=?, Release=?, Availability=?
WHERE Name=?
"""

sql_skill_update = """
UPDATE Skills
SET Image=?, Owner=?, Level=?, Description=?, SP_Cost=?, I_Frames=?
WHERE Internal_Name=?
"""

sql_wp_update = """
UPDATE Wyrmprints
SET Thumbnail=?, Image=?, Max_HP=?, Max_STR=?, Rarity=?, Ability_1=?,
    Ability_2=?, Ability_3=?, Obtained=?, Release=?, Availability=?
WHERE Name=?
"""


def shorten_name(name):
    split = name.split(" ")
    for each in CONSTANTS.alts:
        if split[0].lower().strip() == each.strip().lower():
            return f"{split[0][0].lower()}{split[1].lower()}"
    else:
        return name.lower().replace(" ", "")


def fetch(URL):
    resp = requests.get(URL)
    return resp.text


def fill_adv_names(conn):
    resp = fetch(ADVEN_LIST_URL)
    soup = BeautifulSoup(resp, "html.parser")
    for each in soup.find_all("tr", class_="character-grid-entry grid-entry"):
        td_list = each.find_all("td")

        name = td_list[1].select("a[title]")[0]["title"]
        if name.lower() in [x.lower() for x in exceptions.keys()]:
            name = exceptions[name.lower()]
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


def fill_wp_names(conn):
    # this does stuff
    resp = fetch(WYRMPRINT_LIST_URL)
    for name in parse_wp_names(resp):
        c = conn.cursor()
        c.execute("SELECT Name FROM Wyrmprints WHERE name = ?", (name,))
        result = c.fetchone()
        if result is None:
            c.execute(
                sql_wp_insert,
                (name, "?", "?", "?", "?", "?", "?", "?", "?", "?", "?", "?", "?"),
            )
    conn.commit()


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
                adven["obtained"],
                adven["release"],
                adven["avail"],
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


def update_wyrmprints(conn, force=False):
    cursor = conn.cursor()
    full_list = cursor.execute("SELECT * FROM Wyrmprints")
    full_list = full_list.fetchall()
    for row in full_list:
        name = row[0]
        update = False
        for entry in row[:-1]:
            if entry == "?" or not entry:
                update = True
            else:
                pass
        if not update and not force:
            # print(f"{name} already entered. Passing...")
            continue
        print(f"=====Updating Wyrmprint: {name}=====")
        resp = fetch(f"{MAIN_URL}{name}")
        wp = parse_wyrmprint(resp)
        cursor.execute(
            sql_wp_update,
            (
                wp["thumbnail"],
                wp["image"],
                wp["max_hp"],
                wp["max_str"],
                wp["rarity"],
                wp["abilities"][1],
                wp["abilities"][2],
                wp["abilities"][3],
                wp["obtained"],
                wp["release"],
                wp["availability"],
                name,
            ),
        )
        conn.commit()
        print(f"++++Updated!++++")


async def async_fill_adv_names(session, db):
    resp = await MISC.async_fetch_text(session, ADVEN_LIST_URL)
    soup = BeautifulSoup(resp, "html.parser")
    for each in soup.find_all("tr", class_="character-grid-entry grid-entry"):
        td_list = each.find_all("td")

        name = td_list[1].select("a[title]")[0]["title"]
        if name.lower() in [x.lower() for x in exceptions.keys()]:
            name = exceptions[name.lower()]
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


async def async_fill_wp_names(session, db):
    resp = await MISC.async_fetch_text(session, WYRMPRINT_LIST_URL)
    for name in parse_wp_names(resp):
        async with db.execute(
            "SELECT Name FROM Wyrmprints WHERE name = ?", (name,)
        ) as cursor:
            result = await cursor.fetchone()
            if result is None:
                await db.execute(
                    sql_wp_insert,
                    (name, "?", "?", "?", "?", "?", "?", "?", "?", "?", "?", "?", "?"),
                )
    await db.commit()


async def aysnc_update_advs(session, db, force=False):
    new = 0
    async with db.execute("SELECT * FROM Adventurers") as full_list:
        async for row in full_list:
            adven = {}
            name = row[0]
            update = False
            for entry in row[:-1]:
                if entry == "?" or not entry:
                    update = True
                else:
                    pass
            if not update and not force:
                continue
            print(f"=====Updating: {name}=====")
            resp = await MISC.async_fetch_text(session, f"{MAIN_URL}{name}")
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
                    adven["obtained"],
                    adven["release"],
                    adven["avail"],
                    name,
                ),
            )
            await db.commit()
            print(f"++++Updated!++++")
            new += 1
    return new


async def async_update_skills(session, db, force=False):
    new = 0
    skill_update = {}
    async with db.execute("SELECT * FROM Skills") as full_skill_list:
        async for row in full_skill_list:
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
    async with await db.execute("SELECT * FROM Adventurers") as full_adven_list:
        async for adv in full_adven_list:
            skills = {1: {"name": adv[12]}, 2: {"name": adv[13]}}
            for x in skills.keys():
                name = skills[x]["name"]
                try:
                    update = skill_update[name]
                except KeyError:
                    update = True
                if not update and not force:
                    # print(f"    {name} already entered. Passing skill...")
                    continue
                resp = await MISC.async_fetch_text(
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
                    new += 1
    return new


async def async_update_wyrmprints(session, db, force=False):
    new = 0
    async with db.execute("SELECT * FROM Wyrmprints") as full_list:
        async for row in full_list:
            wp = {}
            name = row[0]
            update = False
            for entry in row[:-1]:
                if entry == "?" or not entry:
                    update = True
                else:
                    pass
            if not update and not force:
                continue
            print(f"=====Updating Wyrmprint: {name}=====")
            resp = await MISC.async_fetch_text(session, f"{MAIN_URL}{name}")
            wp = parse_wyrmprint(resp)
            await db.execute(
                sql_wp_update,
                (
                    wp["thumbnail"],
                    wp["image"],
                    wp["max_hp"],
                    wp["max_str"],
                    wp["rarity"],
                    wp["abilities"][1],
                    wp["abilities"][2],
                    wp["abilities"][3],
                    wp["obtained"],
                    wp["availability"],
                    wp["release"],
                    name,
                ),
            )
            await db.commit()
            print(f"++++Updated!++++")
            new += 1
    return new


def parse_wp_names(resp):
    soup = BeautifulSoup(resp, "html.parser")
    soup = soup.find_all(id="mw-pages")[0]
    name_list = [name.text for name in soup.find_all("li")]
    return name_list


def parse_adventurer(resp):
    adven = {}
    soup = BeautifulSoup(resp, "html.parser")
    p = soup.find(class_="panel-heading")
    adven["title"] = p.find_all("div")[0].get_text()
    adven["element"] = elements[p.select("img[alt]")[0]["alt"]]
    adven["weapon"] = weapons[p.select("img[alt]")[1]["alt"]]
    divs = soup.find(style="flex-grow:1;text-align:center")
    divs = divs.find_all(style="width:100%")
    for each in divs:
        if each.find("div", {"class": "tooltip"}):
            if (
                "total max hp"
                in each.find("div", {"class": "tooltip"}).get_text().lower()
            ):
                adven["max_hp"] = (
                    each.find("span", {"class": "tooltip"})
                    .get_text()
                    .split(")")[1]
                    .split(" ")[0]
                )
            elif (
                "total max str"
                in each.find("div", {"class": "tooltip"}).get_text().lower()
            ):
                adven["max_str"] = (
                    each.find("span", {"class": "tooltip"})
                    .get_text()
                    .split(")")[1]
                    .split(" ")[0]
                )
        elif each.find("div").get_text().lower() == "defense":
            adven["defense"] = each.find_all("div")[1].get_text()
        elif each.find("div").get_text().lower() == "class":
            adven["adv_type"] = unit_types[each.select("img[alt]")[0]["alt"]]
        elif each.find("div").get_text().lower() == "base rarity":
            adven["rarity"] = rarities[each.select("img[alt]")[0]["alt"]]

    adven["obtained"] = divs[-3].find_all("div")[1].get_text()
    adven["release"] = divs[-2].find_all("div")[1].get_text()
    adven["avail"] = divs[-1].find_all("div")[1].get_text()

    skill_sections = soup.find_all(class_="skill-section")

    all_skills = skill_sections[0].find_all(class_="skill-table skill-levels")
    adven["skill_1"] = all_skills[0].find("th").select("a[title]")[0]["title"]
    adven["skill_2"] = all_skills[1].find("th").select("a[title]")[0]["title"]

    max_coab = (
        skill_sections[1].find(class_="ability-header").select("a[title]")[0]["title"]
    )
    for p in skill_sections[1].find(title="Lv5").find_all("p"):
        if "might" in p.get_text().lower():
            value = p.get_text()
            break
    adven["max_coab"] = f"{max_coab}: {value.split('(')[0]}"

    adven["abilities"] = {1: None, 2: None, 3: None}
    all_abilities = skill_sections[2].find_all(class_="skill-table skill-levels")
    for i, each in enumerate(all_abilities):
        ability_title = each.find(class_="ability-header").select("a[title]")[0][
            "title"
        ]
        ability_value = each.find_all(class_="tabbertab")
        try:
            ability_value = ability_value[2].find_all("p")[1].get_text().split("(")[0]
        except IndexError:
            try:
                ability_value = (
                    ability_value[1].find_all("p")[1].get_text().split("(")[0]
                )
            except IndexError:
                ability_value = (
                    ability_value[0].find_all("p")[1].get_text().split("(")[0]
                )
        adven["abilities"][i + 1] = f"{ability_title}: {ability_value}"

    return adven


def parse_skill(resp, skill):
    s_soup = BeautifulSoup(resp, "html.parser")
    skill["image"] = s_soup.find(class_="tabbertab").select("img[src]")[0]["src"]
    temp = s_soup.find(class_="skill-levels skill-details")
    divs = temp.find_all(style="width:100%")
    for each in divs:
        if each.find("div", {"class": "tooltip"}):
            if (
                "camera duration"
                in each.find("div", {"class": "tooltip"}).get_text().lower()
            ):
                skill["i_frames"] = each.find_all("div")[-1].get_text()
    skill["owner"] = (
        s_soup.find(style="padding:1em;").find("li").select("a[title]")[0]["title"]
    )
    if skill["owner"].lower() in [x.lower() for x in exceptions.keys()]:
        skill["owner"] = exceptions[skill["owner"].lower()]
    all_levels = s_soup.find(class_="skill-levels skill-details")
    all_levels = all_levels.find_all(class_="tabbertab")
    skill["levels"] = {}
    for i in range(1, len(all_levels) + 1):
        skill_div = all_levels[i - 1]
        skill["levels"][i] = {"internal_name": "", "desc": "", "sp_cost": ""}
        for br in skill_div.find_all("br"):
            br.replace_with("\n")
        skill["levels"][i]["desc"] = (
            skill_div.find_all("div")[1].get_text().replace("\\'", "'")
        )
        sp_cost = skill_div.find_all(style="width:100%")[0].find_all("div")
        skill["levels"][i]["sp_cost"] = sp_cost[-1].get_text()
        skill["levels"][i]["internal_name"] = f"{skill['name']}_{i}"
    return skill


def parse_wyrmprint(resp):
    wp = {}
    soup = BeautifulSoup(resp, "html.parser")
    max_hp = soup.find("div", {"id": "adv-hp"}).get_text()
    wp["max_hp"] = max_hp.split(" ")[-1]
    max_str = soup.find("div", {"id": "adv-str"}).get_text()
    wp["max_str"] = max_str.split(" ")[-1]
    wp["thumbnail"] = soup.find(class_="gallerybox").find("a").img["src"]
    wp["image"] = (
        soup.find_all(class_="image")[0].select("img[src]")[0]["src"].split("?")[0]
    )
    divs = soup.find_all(style="width:100%")
    for each in divs:
        if each.find("div").get_text().lower() == "rarity":
            wp["rarity"] = rarities[each.select("img[alt]")[0]["alt"]]

    wp["abilities"] = {1: None, 2: "N/A", 3: "N/A"}
    all_abilities = soup.find_all(class_="skill-table skill-levels")
    for i, each in enumerate(all_abilities):
        ability_title = each.find("th").select("a[title]")[0]["title"]
        ability_value = each.find_all(class_="tabbertab")
        try:
            ability_value = ability_value[2].find("p").get_text().split("(")[0]
        except IndexError:
            try:
                ability_value = ability_value[1].find("p").get_text().split("(")[0]
            except IndexError:
                ability_value = ability_value[0].find("p").get_text().split("(")[0]
        wp["abilities"][i + 1] = f"{ability_title}: {ability_value}"

    wp["obtained"] = divs[-3].find_all("div")[1].get_text()
    wp["release"] = divs[-2].find_all("div")[1].get_text()
    wp["availability"] = divs[-1].find_all("div")[1].get_text()
    return wp


class Update:
    def __init__(self, session, db_file):
        self.db_file = db_file
        self.session = session

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
            try:
                c.execute("SELECT * from Wyrmprints")
            except sqlite3.OperationalError:
                c.execute(sql_make_wyrmprints_table)

            fill_adv_names(conn)
            update_advs(conn, force)
            update_skills(conn, force)

            fill_wp_names(conn)
            update_wyrmprints(conn, force)

    async def async_full_update(self, force=False):
        tables = ["adv", "wp"]
        return await self.update(tables, force)

    async def update(self, tables, force=False):
        updated = {}
        async with async_sql.connect(self.db_file) as db:
            if "adv" in tables:
                updated["adv"] = await self.adventurer_update(force, self.session, db)
            if "wp" in tables:
                updated["wp"] = await self.wyrmprint_update(force, self.session, db)
        return updated

    async def adventurer_update(self, force, session, db):
        c = await db.cursor()
        try:
            await db.execute("SELECT * from Adventurers")
        except sqlite3.OperationalError:
            await db.execute(sql_make_adv_table)
        try:
            await db.execute("SELECT * from Skills")
        except sqlite3.OperationalError:
            await db.execute(sql_make_skills_table)
        # await c.close()
        if force:
            await c.execute("DROP TABLE Adventurers")
            await c.execute("DROP TABLE Skills")
            await db.execute(sql_make_adv_table)
            await db.execute(sql_make_skills_table)
        await async_fill_adv_names(session, db)
        updated = await aysnc_update_advs(session, db, force)
        await async_update_skills(session, db, force)
        return updated

    async def wyrmprint_update(self, force, session, db):
        c = await db.cursor()
        try:
            await db.execute("SELECT * from Wyrmprints")
        except sqlite3.OperationalError:
            await db.execute(sql_make_wyrmprints_table)
        if force:
            await c.execute("DROP TABLE Wyrmprints")
            await db.execute(sql_make_wyrmprints_table)
        await async_fill_wp_names(session, db)
        return await async_update_wyrmprints(session, db, force)
