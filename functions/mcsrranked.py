import requests


class McsrRankedClient:
    BASE_URL = "https://mcsrranked.com/api/users"

    def __init__(self, timeout: int = 10, season: int = 10):
        self.timeout = timeout
        self.season = season
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "cubelytics/1.0"})

    def get_profile(self, username: str) -> dict:
        url = f"{self.BASE_URL}/{username}"
        resp = self.session.get(
            url,
            params={"season": self.season},
            timeout=self.timeout,
        )

        if resp.status_code == 404:
            raise ValueError(f"Not found: {username}")
        if resp.status_code != 200:
            raise Exception(f"Request failed: {resp.status_code} {resp.text}")

        body = resp.json()

        if isinstance(body, dict) and body.get("status") == "success" and "data" in body:
            return self._clean(body["data"])

        return body

    def _clean(self, data: dict) -> dict:
        result = {}

        for key in ("nickname", "uuid", "eloRate", "eloRank", "roleType", "country"):
            if key in data and data[key] is not None:
                result[key] = data[key]

        ts = data.get("timestamp", {})
        if ts:
            from datetime import datetime, timezone
            for k in ("firstOnline", "lastOnline", "lastRanked"):
                if ts.get(k):
                    result[k] = datetime.fromtimestamp(
                        ts[k], tz=timezone.utc
                    ).strftime("%b %d, %Y")

        season = data.get("statistics", {}).get("season", {})
        if season:
            s = {}
            for k, v in season.items():
                if isinstance(v, dict):
                    ranked = v.get("ranked")
                    if ranked is not None and ranked != 0:
                        s[k] = ranked
                else:
                    s[k] = v
            if s:
                result["season_stats"] = s

        total = data.get("statistics", {}).get("total", {})
        if total:
            t = {}
            for k, v in total.items():
                if isinstance(v, dict):
                    ranked = v.get("ranked")
                    if ranked is not None and ranked != 0:
                        t[k] = ranked
                else:
                    t[k] = v
            if t:
                result["total_stats"] = t

        conns = data.get("connections", {})
        if conns:
            links = {}
            for platform, info in conns.items():
                if isinstance(info, dict) and info.get("name"):
                    links[platform] = info["name"]
            if links:
                result["connections"] = links

        return result
