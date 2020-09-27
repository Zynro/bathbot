import os
import json
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String

path_to_pnp_guilds = "modules/"


def init_pnp_guilds():
    engine = create_engine("sqlite:///pnp_guilds.db", echo=True)
    meta = MetaData()

    guilds = Table(
        "guilds",
        meta,
        Column("guild", Integer, primary_key=True),
        Column("current", String),
    )

    systems = Table(
        "systems",

        )
    meta.create_all(engine)


class PnP_DB:
    def __init__(self):
        if not os.path.exists(f"modules/roleplay/pnp_db.db"):
            init_pnp_guilds()

    def set_system(self, system)



init_pnp_guilds()
