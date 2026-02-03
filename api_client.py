import os
import requests
from dotenv import load_dotenv
from riotwatcher import LolWatcher

from config import REGION, REGIONAL, MATCH_COUNT, DDRAGON_BASE, DDRAGON_VERSION

load_dotenv()


class ApiClient:
    def __init__(self):
        self.api_key = os.getenv("RIOT_API_KEY")
        self.watcher = LolWatcher(self.api_key)
        self.version = self.get_latest_version()

    def get_latest_version(self):
        try:
            response = requests.get(
                "https://ddragon.leagueoflegends.com/api/versions.json", timeout=10
            )
            if response.status_code == 200:
                versions = response.json()
                return versions[0] if versions else DDRAGON_VERSION
        except:
            pass
        return DDRAGON_VERSION

    def get_account(self, name, tag):
        url = f"https://{REGIONAL}.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{name}/{tag}"
        headers = {"X-Riot-Token": self.api_key}
        response = requests.get(url, headers=headers, timeout=30)
        return response.json()

    def get_summoner(self, puuid):
        return self.watcher.summoner.by_puuid(REGION, puuid)

    def get_match_ids(self, puuid):
        return self.watcher.match.matchlist_by_puuid(REGIONAL, puuid, count=MATCH_COUNT)

    def get_match(self, match_id):
        return self.watcher.match.by_id(REGIONAL, match_id)

    def get_champion_icon_url(self, champion_name):
        fixed_name = self.fix_champion_name(champion_name)
        return f"{DDRAGON_BASE}/{self.version}/img/champion/{fixed_name}.png"

    def get_item_icon_url(self, item_id):
        if not item_id or item_id == 0:
            return None
        return f"{DDRAGON_BASE}/{self.version}/img/item/{item_id}.png"

    def get_profile_icon_url(self, icon_id):
        return f"{DDRAGON_BASE}/{self.version}/img/profileicon/{icon_id}.png"

    def get_spell_icon_url(self, spell_id):
        spell_names = {
            1: "SummonerBoost",
            3: "SummonerExhaust",
            4: "SummonerFlash",
            6: "SummonerHaste",
            7: "SummonerHeal",
            11: "SummonerSmite",
            12: "SummonerTeleport",
            13: "SummonerMana",
            14: "SummonerDot",
            21: "SummonerBarrier",
            32: "SummonerSnowball",
        }
        spell_name = spell_names.get(spell_id)
        if not spell_name:
            return None
        return f"{DDRAGON_BASE}/{self.version}/img/spell/{spell_name}.png"

    def fix_champion_name(self, name):
        fixes = {
            "Kai'Sa": "Kaisa",
            "Kha'Zix": "Khazix",
            "Vel'Koz": "Velkoz",
            "Cho'Gath": "Chogath",
            "Rek'Sai": "RekSai",
            "Kog'Maw": "KogMaw",
            "LeBlanc": "Leblanc",
            "Wukong": "MonkeyKing",
            "Nunu & Willump": "Nunu",
            "Renata Glasc": "Renata",
        }
        return fixes.get(name, name)

    def get_item_name(self, item_id):
        if not item_id or item_id == 0:
            return None
        try:
            url = f"{DDRAGON_BASE}/{self.version}/data/en_US/item.json"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                item_data = data["data"].get(str(item_id))
                if item_data:
                    return item_data["name"]
        except:
            pass
        return f"Item {item_id}"
