import os
import json
import pandas as pd

from database import get_session, get_all_players, get_player_matches
from models import MatchHistory
from analysis import calculate_player_summary, generate_insights


OUTPUT_DIR = "tableau_data"


def export_player_summary():
    with get_session() as session:
        df = calculate_player_summary(session)
    return df


def export_match_history():
    rows = []

    with get_session() as session:
        players = get_all_players(session)

        for player in players:
            matches = get_player_matches(session, player.id)

            for match in matches:
                rows.append(
                    {
                        "name": player.name,
                        "profile_icon_url": player.profile_icon_url,
                        "match_id": match.match_id,
                        "game_date": match.game_date,
                        "game_duration": match.game_duration,
                        "champion_name": match.champion_name,
                        "champion_icon_url": match.champion_icon_url,
                        "win": match.win,
                        "kills": match.kills,
                        "deaths": match.deaths,
                        "assists": match.assists,
                        "kda": match.kda,
                        "kill_participation": match.kill_participation,
                        "gold_earned": match.gold_earned,
                        "gold_per_min": match.gold_per_min,
                        "cs": match.cs,
                        "cs_per_min": match.cs_per_min,
                        "total_damage": match.total_damage,
                        "damage_per_min": match.damage_per_min,
                        "damage_to_objectives": match.damage_to_objectives,
                        "team_damage_pct": match.team_damage_pct,
                        "vision_score": match.vision_score,
                        "wards_placed": match.wards_placed,
                        "control_wards": match.control_wards,
                        "items": json.dumps(match.items) if match.items else "[]",
                        "summoner_spells": json.dumps(match.summoner_spells)
                        if match.summoner_spells
                        else "[]",
                        "is_anomaly": match.is_anomaly,
                        "anomaly_reason": match.anomaly_reason,
                    }
                )

    return pd.DataFrame(rows)


def export_anomalies():
    rows = []

    with get_session() as session:
        players = get_all_players(session)

        for player in players:
            matches = get_player_matches(session, player.id)

            for match in matches:
                if match.is_anomaly:
                    rows.append(
                        {
                            "name": player.name,
                            "profile_icon_url": player.profile_icon_url,
                            "game_date": match.game_date,
                            "champion_name": match.champion_name,
                            "champion_icon_url": match.champion_icon_url,
                            "win": match.win,
                            "kda": match.kda,
                            "kills": match.kills,
                            "deaths": match.deaths,
                            "assists": match.assists,
                            "anomaly_reason": match.anomaly_reason,
                        }
                    )

    return pd.DataFrame(rows)


def export_insights():
    with get_session() as session:
        player_summary = calculate_player_summary(session)
    return generate_insights(player_summary)


def run_export():
    print("=" * 50)
    print("EXPORT TO CSV")
    print("=" * 50)

    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    print("Exporting player summary...")
    player_summary = export_player_summary()
    player_summary.to_csv(f"{OUTPUT_DIR}/player_summary.csv", index=False)
    print(f"  Saved {len(player_summary)} rows")

    print("Exporting match history...")
    match_history = export_match_history()
    match_history.to_csv(f"{OUTPUT_DIR}/match_history.csv", index=False)
    print(f"  Saved {len(match_history)} rows")

    print("Exporting anomalies...")
    anomalies = export_anomalies()
    anomalies.to_csv(f"{OUTPUT_DIR}/anomalies.csv", index=False)
    print(f"  Saved {len(anomalies)} rows")

    print("Exporting insights...")
    insights = export_insights()
    insights.to_csv(f"{OUTPUT_DIR}/player_insights.csv", index=False)
    print(f"  Saved {len(insights)} rows")

    print()
    print(f"All files saved to {OUTPUT_DIR}/")
    print("Export complete!")


if __name__ == "__main__":
    run_export()
