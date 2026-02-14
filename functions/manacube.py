import requests


_STAT_NAMES = {
    "base:play_time": "Hours Played",
    "base:mob_kills": "Mobs Killed",
    "base:player_kills": "Player Kills",
    "base:blocks_broken": "Blocks Broken",
    "command:victory": "Trial Victories",
    "command:easymonster": "Easy Monster Kills",
    "command:hardmonster": "Hard Monster Kills",
    "command:quest": "Quests Completed",
    "command:boss": "Boss Kills",
    "command:pond": "Pond Catches",
    "command:prestige": "Prestiges",
    "command:lpswin": "LPS Wins",
    "command:easy": "Easy Parkour Maps",
    "command:medium": "Medium Parkour Maps",
    "command:hard": "Hard Parkour Maps",
    "command:expert": "Expert Parkour Maps",
    "command:insane": "Insane Parkour Maps",
    "command:adventure": "Adventure Maps",
}


class ManaCubeClient:
    FETCH_URL = "https://manacube.com/stats_data/fetch.php"

    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            ),
            "Referer": "https://manacube.com/stats/player/",
        })

    def get_profile(self, uuid: str) -> dict:
        resp = self.session.get(
            self.FETCH_URL,
            params={"uuid": uuid},
            timeout=self.timeout,
        )

        if resp.status_code != 200:
            raise Exception(f"ManaCube request failed: {resp.status_code}")

        data = resp.json()

        if not data.get("exists"):
            raise ValueError("Player has not joined ManaCube")

        return self._clean(data)

    def _clean(self, data: dict) -> dict:
        result = {}

        if data.get("level"):
            result["level"] = data["level"]
        if data.get("rank"):
            result["rank"] = data["rank"]
        if data.get("cubits"):
            result["cubits"] = data["cubits"]

        ls = data.get("lastSeen")
        if isinstance(ls, dict):
            parts = []
            if ls.get("timeAgo"):
                parts.append(ls["timeAgo"])
            if ls.get("server"):
                parts.append(f"on {ls['server']}")
            if parts:
                result["last_seen"] = " ".join(parts)

        stats = data.get("stats", {})
        if isinstance(stats, dict):
            clean_stats = {}
            for key, friendly in _STAT_NAMES.items():
                val = stats.get(key)
                if val and str(val) != "0":
                    clean_stats[friendly] = val
            if clean_stats:
                result["stats"] = clean_stats

        return result
