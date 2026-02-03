from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Float,
    Boolean,
    DateTime,
    ForeignKey,
    JSON,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Player(Base):
    __tablename__ = "players"

    id = Column(Integer, primary_key=True)
    puuid = Column(String, unique=True)
    name = Column(String)
    tag_line = Column(String)
    level = Column(Integer)
    profile_icon_url = Column(String)
    updated_at = Column(DateTime)

    matches = relationship(
        "MatchHistory", back_populates="player", cascade="all, delete-orphan"
    )


class MatchHistory(Base):
    __tablename__ = "match_history"

    id = Column(Integer, primary_key=True)
    player_id = Column(Integer, ForeignKey("players.id"))
    match_id = Column(String)
    game_date = Column(DateTime)
    game_duration = Column(Integer)

    champion_name = Column(String)
    champion_icon_url = Column(String)

    win = Column(Boolean)

    kills = Column(Integer)
    deaths = Column(Integer)
    assists = Column(Integer)
    kda = Column(Float)
    kill_participation = Column(Float)

    gold_earned = Column(Integer)
    gold_per_min = Column(Float)
    cs = Column(Integer)
    cs_per_min = Column(Float)

    total_damage = Column(Integer)
    damage_per_min = Column(Float)
    damage_to_objectives = Column(Integer)
    team_damage_pct = Column(Float)

    vision_score = Column(Integer)
    wards_placed = Column(Integer)
    control_wards = Column(Integer)

    items = Column(JSON)
    summoner_spells = Column(JSON)

    is_anomaly = Column(Boolean, default=False)
    anomaly_reason = Column(String, nullable=True)

    player = relationship("Player", back_populates="matches")
