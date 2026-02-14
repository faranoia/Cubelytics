import re
import json
import requests


class SixB6tClient:
    BASE_URL = "https://www.6b6t.org/en/stats"

    def __init__(self, timeout: int = 15):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        })

    def get_profile(self, username: str) -> dict:
        url = f"{self.BASE_URL}/{username}"
        resp = self.session.get(url, timeout=self.timeout)

        if resp.status_code == 404:
            raise ValueError(f"Not found on 6b6t: {username}")
        if resp.status_code != 200:
            raise Exception(f"Request failed: {resp.status_code}")

        stats_data = self._extract_stats(resp.text)
        if not stats_data:
            raise ValueError(f"No stats found for '{username}' on 6b6t")

        if "first_join" not in stats_data and "player_stats" not in stats_data:
            raise ValueError(f"Player '{username}' has not joined 6b6t")

        return stats_data

    def _extract_stats(self, html: str) -> dict | None:
        pattern = re.compile(r'self\.__next_f\.push\(\s*\[(\d+)\s*,\s*"((?:[^"\\]|\\.)*)"\s*\]\s*\)')

        for match in pattern.finditer(html):
            raw = match.group(2)

            try:
                unescaped = raw.encode().decode('unicode_escape')
            except Exception:
                unescaped = raw.replace('\\"', '"').replace('\\n', '\n').replace('\\/', '/')

            for line in unescaped.split('\n'):
                line = line.strip()
                colon_idx = line.find(':')
                if colon_idx < 0 or colon_idx > 4:
                    continue

                payload = line[colon_idx + 1:]
                if '"player_stats"' not in payload and '"stats"' not in payload:
                    continue

                try:
                    arr = json.loads(payload)
                    if isinstance(arr, list) and len(arr) >= 4:
                        props = arr[3]
                        if isinstance(props, dict) and "stats" in props:
                            return self._clean_stats(props["stats"])
                except (json.JSONDecodeError, IndexError, TypeError):
                    continue

        return None

    def _clean_stats(self, raw) -> dict:
        if not isinstance(raw, dict):
            raise ValueError("Player not found on 6b6t")

        result = {}

        for key in ("username", "rank", "uuid"):
            if key in raw and raw[key]:
                result[key] = raw[key]

        inner = raw.get("stats")
        if not isinstance(inner, dict):
            if result:
                return result
            raise ValueError("Player not found on 6b6t")

        if inner.get("first_join"):
            result["first_join"] = inner["first_join"]

        player_stats = inner.get("player_stats")
        if isinstance(player_stats, list) and player_stats:
            stats_table = {}
            for s in player_stats:
                if not isinstance(s, dict):
                    continue
                name = s.get("stat_name", s.get("stat_id", "?"))
                vals = s.get("values", {})
                if not isinstance(vals, dict):
                    continue
                stats_table[name] = {
                    "7d": vals.get("seven_days", "0"),
                    "30d": vals.get("thirty_days", "0"),
                    "total": vals.get("total", "0"),
                }
            if stats_table:
                result["player_stats"] = stats_table

        return result
