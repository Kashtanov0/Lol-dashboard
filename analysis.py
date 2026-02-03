import pandas as pd
from scipy import stats

from database import get_session, get_all_players, get_player_matches
from models import MatchHistory
from config import ANOMALY_THRESHOLD


def calculate_player_summary(session):
    players = get_all_players(session)
    summaries = []

    for player in players:
        matches = get_player_matches(session, player.id)

        if not matches:
            continue

        total = len(matches)
        wins = sum(1 for m in matches if m.win)
        losses = total - wins

        summaries.append(
            {
                "name": player.name,
                "tag_line": player.tag_line,
                "level": player.level,
                "profile_icon_url": player.profile_icon_url,
                "total_games": total,
                "wins": wins,
                "losses": losses,
                "win_rate": round(wins / total * 100, 1) if total > 0 else 0,
                "avg_kills": round(sum(m.kills for m in matches) / total, 1),
                "avg_deaths": round(sum(m.deaths for m in matches) / total, 1),
                "avg_assists": round(sum(m.assists for m in matches) / total, 1),
                "avg_kda": round(sum(m.kda for m in matches) / total, 2),
                "avg_gpm": round(sum(m.gold_per_min for m in matches) / total, 0),
                "avg_cspm": round(sum(m.cs_per_min for m in matches) / total, 1),
                "avg_dpm": round(sum(m.damage_per_min for m in matches) / total, 0),
                "avg_vision": round(sum(m.vision_score for m in matches) / total, 0),
            }
        )

    return pd.DataFrame(summaries)


def detect_anomalies(session):
    players = get_all_players(session)

    for player in players:
        matches = get_player_matches(session, player.id)

        if len(matches) < 5:
            continue

        kdas = [m.kda for m in matches]
        deaths_list = [m.deaths for m in matches]
        dpms = [m.damage_per_min for m in matches]
        gpms = [m.gold_per_min for m in matches]
        durations = [m.game_duration for m in matches]

        kda_mean, kda_std = pd.Series(kdas).mean(), pd.Series(kdas).std()
        deaths_mean, deaths_std = (
            pd.Series(deaths_list).mean(),
            pd.Series(deaths_list).std(),
        )
        dpm_mean, dpm_std = pd.Series(dpms).mean(), pd.Series(dpms).std()
        gpm_mean, gpm_std = pd.Series(gpms).mean(), pd.Series(gpms).std()
        dur_mean, dur_std = pd.Series(durations).mean(), pd.Series(durations).std()

        for match in matches:
            reasons = []

            if kda_std > 0:
                kda_z = abs(match.kda - kda_mean) / kda_std
                if kda_z > ANOMALY_THRESHOLD:
                    if match.kda > kda_mean:
                        reasons.append(f"Very high KDA ({match.kda})")
                    else:
                        reasons.append(f"Very low KDA ({match.kda})")

            if deaths_std > 0:
                deaths_z = (match.deaths - deaths_mean) / deaths_std
                if deaths_z > ANOMALY_THRESHOLD:
                    reasons.append(f"Many deaths ({match.deaths})")

            if dpm_std > 0:
                dpm_z = abs(match.damage_per_min - dpm_mean) / dpm_std
                if dpm_z > ANOMALY_THRESHOLD:
                    if match.damage_per_min > dpm_mean:
                        reasons.append(
                            f"Very high damage ({int(match.damage_per_min)} DPM)"
                        )
                    else:
                        reasons.append(
                            f"Very low damage ({int(match.damage_per_min)} DPM)"
                        )

            if gpm_std > 0:
                gpm_z = abs(match.gold_per_min - gpm_mean) / gpm_std
                if gpm_z > ANOMALY_THRESHOLD:
                    if match.gold_per_min > gpm_mean:
                        reasons.append(
                            f"Very high gold ({int(match.gold_per_min)} GPM)"
                        )
                    else:
                        reasons.append(f"Very low gold ({int(match.gold_per_min)} GPM)")

            if dur_std > 0:
                dur_z = abs(match.game_duration - dur_mean) / dur_std
                if dur_z > ANOMALY_THRESHOLD:
                    mins = match.game_duration // 60
                    if match.game_duration < dur_mean:
                        reasons.append(f"Very short game ({mins} min)")
                    else:
                        reasons.append(f"Very long game ({mins} min)")

            if reasons:
                match.is_anomaly = True
                match.anomaly_reason = "; ".join(reasons)
            else:
                match.is_anomaly = False
                match.anomaly_reason = None


def generate_insights(player_summary):
    insights = []

    for _, player in player_summary.iterrows():
        name = player["name"]
        icon = player["profile_icon_url"]

        if player["win_rate"] >= 55:
            insights.append(
                {
                    "name": name,
                    "profile_icon_url": icon,
                    "type": "Strength",
                    "insight": f"Good win rate ({player['win_rate']}%) - keep it up!",
                }
            )
        elif player["win_rate"] < 45:
            insights.append(
                {
                    "name": name,
                    "profile_icon_url": icon,
                    "type": "Improvement",
                    "insight": f"Win rate needs work ({player['win_rate']}%)",
                }
            )

        if player["avg_kda"] >= 3.0:
            insights.append(
                {
                    "name": name,
                    "profile_icon_url": icon,
                    "type": "Strength",
                    "insight": f"Great KDA ({player['avg_kda']}) - you stay alive well",
                }
            )
        elif player["avg_kda"] < 2.0:
            insights.append(
                {
                    "name": name,
                    "profile_icon_url": icon,
                    "type": "Improvement",
                    "insight": f"KDA needs work ({player['avg_kda']}) - try dying less",
                }
            )

        if player["avg_vision"] >= 25:
            insights.append(
                {
                    "name": name,
                    "profile_icon_url": icon,
                    "type": "Strength",
                    "insight": "Good vision control",
                }
            )
        elif player["avg_vision"] < 15:
            insights.append(
                {
                    "name": name,
                    "profile_icon_url": icon,
                    "type": "Improvement",
                    "insight": "Place more wards",
                }
            )

        if player["avg_cspm"] >= 6.0:
            insights.append(
                {
                    "name": name,
                    "profile_icon_url": icon,
                    "type": "Strength",
                    "insight": f"Good farming ({player['avg_cspm']} CS/min)",
                }
            )
        elif player["avg_cspm"] < 4.0:
            insights.append(
                {
                    "name": name,
                    "profile_icon_url": icon,
                    "type": "Improvement",
                    "insight": f"Practice last hitting ({player['avg_cspm']} CS/min)",
                }
            )

    return pd.DataFrame(insights)


def run_analysis():
    print("=" * 50)
    print("ANALYSIS")
    print("=" * 50)

    with get_session() as session:
        print("Calculating player summaries...")
        player_summary = calculate_player_summary(session)

        print("Detecting anomalies...")
        detect_anomalies(session)

        print("Generating insights...")
        insights = generate_insights(player_summary)

        print()
        print("Player Summary:")
        print(
            player_summary[["name", "total_games", "win_rate", "avg_kda"]].to_string(
                index=False
            )
        )
        print()

        anomaly_count = session.query(MatchHistory).filter_by(is_anomaly=True).count()
        print(f"Anomalies detected: {anomaly_count}")
        print(f"Insights generated: {len(insights)}")

    print()
    print("Analysis complete!")

    return player_summary, insights


if __name__ == "__main__":
    run_analysis()
