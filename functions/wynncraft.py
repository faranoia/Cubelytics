import requests


class WynncraftClient:
    BASE_URL = "https://api.wynncraft.com/v3/player"

    def __init__(self, timeout: int = 15):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            ),
            "Accept": "application/json",
        })

    def get_profile(self, uuid: str) -> dict:
        url = f"{self.BASE_URL}/{uuid}"
        resp = self.session.get(url, timeout=self.timeout)
        resp.raise_for_status()

        data = resp.json()

        if not data or "username" not in data:
            raise ValueError("Player not found on Wynncraft")

        result = {}

        for key in ("username", "rank", "server", "online",
                    "firstJoin", "lastJoin", "playtime", "guild"):
            if key in data and data[key] is not None:
                result[key] = data[key]

        gd = data.get("globalData", {})
        if gd:
            global_info = {}
            for key in ("totalLevel", "mobsKilled", "chestsFound",
                        "completedQuests", "wars", "contentCompletion",
                        "worldEvents", "lootruns", "caves"):
                val = gd.get(key)
                if val is not None and val != 0:
                    global_info[key] = val

            pvp = gd.get("pvp", {})
            if pvp:
                kills = pvp.get("kills", 0)
                deaths = pvp.get("deaths", 0)
                if kills or deaths:
                    global_info["pvp_kills"] = kills
                    global_info["pvp_deaths"] = deaths

            dungeons = gd.get("dungeons", {})
            if dungeons.get("total", 0) > 0:
                global_info["dungeons_total"] = dungeons["total"]
                dlist = dungeons.get("list", {})
                if dlist:
                    global_info["dungeons"] = dlist

            raids = gd.get("raids", {})
            if raids.get("total", 0) > 0:
                global_info["raids_total"] = raids["total"]
                rlist = raids.get("list", {})
                if rlist:
                    global_info["raids"] = rlist

            if global_info:
                result["global_data"] = global_info

        ranking = data.get("ranking", {})
        if ranking:
            ranks = {k: v for k, v in ranking.items()
                     if v is not None and v > 0}
            if ranks:
                result["ranking"] = ranks

        return result
