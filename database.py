from contextlib import contextmanager
from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config import DATABASE_URL, MATCH_COUNT
from models import Base, Player, MatchHistory


engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)


def init_db():
    Base.metadata.create_all(engine)


@contextmanager
def get_session():
    session = Session()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()


def get_or_create_player(session, puuid, name, tag_line, level, profile_icon_url):
    player = session.query(Player).filter_by(puuid=puuid).first()

    if player:
        player.name = name
        player.tag_line = tag_line
        player.level = level
        player.profile_icon_url = profile_icon_url
        player.updated_at = datetime.now()
    else:
        player = Player(
            puuid=puuid,
            name=name,
            tag_line=tag_line,
            level=level,
            profile_icon_url=profile_icon_url,
            updated_at=datetime.now(),
        )
        session.add(player)
        session.flush()

    return player


def add_match(session, player_id, match_data):
    existing = (
        session.query(MatchHistory)
        .filter_by(player_id=player_id, match_id=match_data["match_id"])
        .first()
    )

    if existing:
        return existing

    match = MatchHistory(
        player_id=player_id,
        match_id=match_data["match_id"],
        game_date=match_data["game_date"],
        game_duration=match_data["game_duration"],
        champion_name=match_data["champion_name"],
        champion_icon_url=match_data["champion_icon_url"],
        win=match_data["win"],
        kills=match_data["kills"],
        deaths=match_data["deaths"],
        assists=match_data["assists"],
        kda=match_data["kda"],
        kill_participation=match_data["kill_participation"],
        gold_earned=match_data["gold_earned"],
        gold_per_min=match_data["gold_per_min"],
        cs=match_data["cs"],
        cs_per_min=match_data["cs_per_min"],
        total_damage=match_data["total_damage"],
        damage_per_min=match_data["damage_per_min"],
        damage_to_objectives=match_data["damage_to_objectives"],
        team_damage_pct=match_data["team_damage_pct"],
        vision_score=match_data["vision_score"],
        wards_placed=match_data["wards_placed"],
        control_wards=match_data["control_wards"],
        items=match_data["items"],
        summoner_spells=match_data["summoner_spells"],
        is_anomaly=False,
        anomaly_reason=None,
    )
    session.add(match)
    return match


def get_all_players(session):
    return session.query(Player).all()


def get_player_matches(session, player_id):
    return (
        session.query(MatchHistory)
        .filter_by(player_id=player_id)
        .order_by(MatchHistory.game_date.desc())
        .all()
    )


def cleanup_old_matches(session, player_id):
    matches = (
        session.query(MatchHistory)
        .filter_by(player_id=player_id)
        .order_by(MatchHistory.game_date.desc())
        .all()
    )

    if len(matches) > MATCH_COUNT:
        old_matches = matches[MATCH_COUNT:]
        for match in old_matches:
            session.delete(match)


def delete_player_matches(session, player_id):
    session.query(MatchHistory).filter_by(player_id=player_id).delete()
