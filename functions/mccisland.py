import requests


_GAME_NAMES = {
    "bb": "Battle Box",
    "ba": "Battle Arena",
    "sb": "Sky Battle",
    "tg": "TGTTOS",
    "hw": "Hole in the Wall",
    "pw": "Parkour Warrior",
    "ps": "Parkour Survivor",
    "db": "Dynaball",
    "rs": "Rocket Spleef",
    "gl": "Globetrotters",
    "fi": "Fishing",
}


class MccIslandClient:
    BASE_URL = "https://stats.derniklaas.de/api/player"

    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "cubelytics/1.0",
            "Content-Type": "application/json",
        })

    def get_profile(self, username: str) -> dict:
        resp = self.session.post(
            self.BASE_URL,
            json={"username": username},
            timeout=self.timeout,
        )

        if resp.status_code == 404:
            raise ValueError(f"Not found: {username}")
        if resp.status_code != 200:
            raise Exception(f"Request failed: {resp.status_code} {resp.text}")

        body = resp.json()
        player = (body.get("data") or {}).get("playerByUsername")
        if not player:
            raise ValueError(f"Not found on MCC Island: {username}")

        return self._clean(player)

    def _clean(self, data: dict) -> dict:
        result = {}

        for key in ("uuid", "username"):
            if data.get(key):
                result[key] = data[key]

        ranks = data.get("ranks", [])
        if ranks:
            clean = []
            for r in ranks:
                if isinstance(r, str):
                    clean.append(r.replace("_", " ").title())
                elif isinstance(r, dict) and r.get("name"):
                    clean.append(r["name"])
            if clean:
                result["ranks"] = ", ".join(clean)

        crown = data.get("crownLevel", {})
        if isinstance(crown, dict):
            ld = crown.get("levelData", {})
            if isinstance(ld, dict) and ld.get("level") is not None:
                result["crown_level"] = ld["level"]

            trophies = crown.get("trophies", {})
            if isinstance(trophies, dict) and trophies.get("obtained"):
                result["trophies"] = f"{trophies['obtained']:,} / {trophies.get('obtainable', '?'):,}"

            for label, key in [
                ("skill_trophies", "skillTrophies"),
                ("style_trophies", "styleTrophies"),
                ("angler_trophies", "anglerTrophies"),
            ]:
                sub = crown.get(key, {})
                if isinstance(sub, dict) and sub.get("obtained"):
                    result[label] = f"{sub['obtained']:,} / {sub.get('obtainable', '?'):,}"

        plus = data.get("mccPlusStatus")
        if isinstance(plus, dict):
            mcc_plus = {}
            if plus.get("evolution"):
                mcc_plus["evolution"] = plus["evolution"]
            if plus.get("totalDays"):
                mcc_plus["total_days"] = plus["totalDays"]
            if plus.get("streakStart"):
                mcc_plus["streak_start"] = plus["streakStart"][:10]
            if mcc_plus:
                result["mcc_plus"] = mcc_plus

        factions = data.get("factions", [])
        active = {}
        for f in factions:
            if not isinstance(f, dict):
                continue
            xp = f.get("totalExperience", 0)
            if xp > 0:
                name = f.get("name", "?").replace("_", " ").title()
                lvl = (f.get("levelData") or {}).get("level", 0)
                sel = " ★" if f.get("selected") else ""
                active[name] = f"Lv.{lvl} ({xp:,} XP){sel}"
        if active:
            result["factions"] = active

        stats = data.get("statistics", {})
        if isinstance(stats, dict) and stats:
            games = {}
            for stat_key, value in stats.items():
                if not isinstance(value, (int, float)) or value == 0:
                    continue
                if stat_key.endswith("_weekly"):
                    continue
                parts = stat_key.split("_", 1)
                if len(parts) < 2:
                    continue
                prefix = parts[0]
                game_name = _GAME_NAMES.get(prefix, prefix.upper())
                stat_name = parts[1].replace("_lifetime", "").replace("_", " ").title()
                if game_name not in games:
                    games[game_name] = {}
                games[game_name][stat_name] = f"{value:,}" if isinstance(value, int) else value
            if games:
                result["game_stats"] = games

        badges = data.get("badges", [])
        if isinstance(badges, list) and badges:
            completed = 0
            total_badges = len(badges)
            for b in badges:
                if not isinstance(b, dict):
                    continue
                progress = b.get("stageProgress", [])
                if isinstance(progress, list) and progress:
                    last = progress[-1]
                    if isinstance(last, dict):
                        p = last.get("progress", {})
                        if isinstance(p, dict):
                            if (p.get("obtained", 0) or 0) >= (p.get("obtainable", 1) or 1):
                                completed += 1
            result["badges"] = f"{completed} / {total_badges} completed"

        return result
