import time
from datetime import datetime

from api_client import ApiClient
from database import (
    get_session,
    init_db,
    get_or_create_player,
    add_match,
    cleanup_old_matches,
    delete_player_matches,
)
from config import PLAYERS


def extract_match_data(client, match, puuid):
    info = match["info"]
    metadata = match["metadata"]

    participant = None
    for p in info["participants"]:
        if p["puuid"] == puuid:
            participant = p
            break

    if not participant:
        return None

    game_duration = info.get("gameDuration", 1)
    duration_min = game_duration / 60 if game_duration > 0 else 1

    kills = participant.get("kills", 0)
    deaths = participant.get("deaths", 0)
    assists = participant.get("assists", 0)
    kda = (kills + assists) / max(deaths, 1)

    challenges = participant.get("challenges", {})
    kill_participation = challenges.get("killParticipation", 0)
    team_damage_pct = challenges.get("teamDamagePercentage", 0)

    cs = participant.get("totalMinionsKilled", 0) + participant.get(
        "neutralMinionsKilled", 0
    )

    items = []
    for i in range(7):
        item_id = participant.get(f"item{i}", 0)
        if item_id and item_id > 0:
            items.append(
                {
                    "id": item_id,
                    "name": client.get_item_name(item_id),
                    "icon_url": client.get_item_icon_url(item_id),
                }
            )

    spell1_id = participant.get("summoner1Id")
    spell2_id = participant.get("summoner2Id")
    summoner_spells = [
        {"id": spell1_id, "icon_url": client.get_spell_icon_url(spell1_id)},
        {"id": spell2_id, "icon_url": client.get_spell_icon_url(spell2_id)},
    ]

    champion_name = participant.get("championName", "Unknown")

    return {
        "match_id": metadata.get("matchId"),
        "game_date": datetime.fromtimestamp(info.get("gameCreation", 0) / 1000),
        "game_duration": game_duration,
        "champion_name": champion_name,
        "champion_icon_url": client.get_champion_icon_url(champion_name),
        "win": participant.get("win", False),
        "kills": kills,
        "deaths": deaths,
        "assists": assists,
        "kda": round(kda, 2),
        "kill_participation": round(kill_participation, 2),
        "gold_earned": participant.get("goldEarned", 0),
        "gold_per_min": round(participant.get("goldEarned", 0) / duration_min, 1),
        "cs": cs,
        "cs_per_min": round(cs / duration_min, 1),
        "total_damage": participant.get("totalDamageDealtToChampions", 0),
        "damage_per_min": round(
            participant.get("totalDamageDealtToChampions", 0) / duration_min, 1
        ),
        "damage_to_objectives": participant.get("damageDealtToObjectives", 0),
        "team_damage_pct": round(team_damage_pct, 2),
        "vision_score": participant.get("visionScore", 0),
        "wards_placed": participant.get("wardsPlaced", 0),
        "control_wards": participant.get("detectorWardsPlaced", 0),
        "items": items,
        "summoner_spells": summoner_spells,
    }


def extract_player(client, session, name, tag):
    print(f"  Fetching account for {name}#{tag}...")
    account = client.get_account(name, tag)
    puuid = account["puuid"]

    print(f"  Fetching summoner info...")
    summoner = client.get_summoner(puuid)
    level = summoner.get("summonerLevel", 0)
    icon_id = summoner.get("profileIconId", 29)
    profile_icon_url = client.get_profile_icon_url(icon_id)

    player = get_or_create_player(session, puuid, name, tag, level, profile_icon_url)

    delete_player_matches(session, player.id)

    print(f"  Fetching match history...")
    match_ids = client.get_match_ids(puuid)
    print(f"  Found {len(match_ids)} matches")

    for i, match_id in enumerate(match_ids):
        try:
            print(f"    [{i + 1}/{len(match_ids)}] {match_id}")
            match = client.get_match(match_id)
            match_data = extract_match_data(client, match, puuid)

            if match_data:
                add_match(session, player.id, match_data)

            time.sleep(0.5)
        except Exception as e:
            print(f"    Error: {e}")
            continue

    cleanup_old_matches(session, player.id)
    print(f"  Done with {name}")


def run_extraction():
    print("=" * 50)
    print("DATA EXTRACTION")
    print("=" * 50)

    init_db()
    client = ApiClient()

    print(f"Using Data Dragon version: {client.version}")
    print()

    with get_session() as session:
        for player_config in PLAYERS:
            name = player_config["name"]
            tag = player_config["tag"]

            print(f"Processing {name}#{tag}")
            try:
                extract_player(client, session, name, tag)
            except Exception as e:
                print(f"  Failed: {e}")

            print()
            time.sleep(1)

    print("Extraction complete!")


if __name__ == "__main__":
    run_extraction()
