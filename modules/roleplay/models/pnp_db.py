import os
import campaign
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

supported_systems = campaign.pnp_list.keys()

path_to_pnp_guilds = "modules/"

engine = create_engine("sqlite:///pnp_guilds.db", echo=True)
Base = declarative_base()


def open(Session):
    Session.configure(bind=engine)
    session = Session()
    if not os.path.exists(f"modules/roleplay/pnp_db.db"):
        Base.metadata.create_all(engine)
    return session


class Guilds(Base):
    __tablename__ = "guilds"
    guild = Column(Integer, primary_key=True)
    system = Column(String)

    """def __init__(self, **kw):
        for k in kw.keys():
            k = k.lower()
            setattr(self, k, kw[k])"""

    def __init__(self, guild, system):
        self.guild = guild
        self.system = system


class PNP_DB(Guilds):
    def __init__(self, Session):
        self.Session = Session

    def get_guild(self, guild_id, session=None):
        if not session:
            session = open(self.Session)
            guild = session.query(Guilds).get(guild_id)
            session.close()
        else:
            guild = session.query(Guilds).get(guild_id)
        return guild

    def set_system(self, guild_id, system):
        session = open(self.Session)
        if system.lower() in supported_systems:
            if not session.query(Guilds).filter_by(guild=guild_id).scalar():
                # print("DOES NOT EXIST")
                row = super.__init__(guild_id, system)
                session.add(row)
                session.commit()
            else:
                # print("EXISTS")
                guild = self.get_guild(guild_id, session)
                guild.system = system
                session.commit()
        return session.close()
