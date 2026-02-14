import requests


class SubTiersClient:
    BASE_URL = "https://subtiers.net/api"

    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "mcsint/1.0",
            "Accept": "application/json",
        })

    def get_profile(self, identifier: str) -> dict:
        url = f"{self.BASE_URL}/profile/{identifier}"
        resp = self.session.get(url, timeout=self.timeout)

        if resp.status_code == 404:
            raise ValueError(f"Not found on subtiers.net: {identifier}")
        if resp.status_code != 200:
            raise Exception(
                f"subtiers.net request failed: {resp.status_code} {resp.text}"
            )

        raw = resp.json()
        return self._format(raw)

    def _format(self, raw: dict) -> dict:
        result = {}

        if raw.get("name"):
            result["username"] = raw["name"]
        if raw.get("uuid"):
            result["uuid"] = raw["uuid"]
        if raw.get("region"):
            result["region"] = raw["region"]
        if raw.get("points") is not None:
            result["points"] = raw["points"]
        if raw.get("overall") is not None:
            result["overall_rank"] = raw["overall"]

        rankings = raw.get("rankings", {})
        if rankings:
            modes = {}
            for mode, info in rankings.items():
                entry = {}
                if info.get("tier") is not None:
                    entry["tier"] = info["tier"]
                if info.get("pos") is not None:
                    entry["pos"] = info["pos"]
                if info.get("peak_tier") is not None:
                    entry["peak_tier"] = info["peak_tier"]
                if info.get("peak_pos") is not None:
                    entry["peak_pos"] = info["peak_pos"]
                if info.get("retired") is not None:
                    entry["retired"] = info["retired"]
                if entry:
                    modes[mode] = entry
            if modes:
                result["rankings"] = modes

        badges = raw.get("badges", [])
        if badges:
            seen = set()
            unique = []
            for b in badges:
                title = b.get("title", "")
                if title and title not in seen:
                    seen.add(title)
                    unique.append({
                        "title": title,
                        "description": b.get("desc", ""),
                    })
            if unique:
                result["badges"] = unique

        return result
