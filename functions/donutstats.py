import re
import json
import requests


class DonutStatsClient:

    BASE_URL = "https://www.donutstats.net/player-stats"

    def __init__(self, timeout: int = 15):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            ),
        })

    @staticmethod
    def _ms_to_human(ms_val) -> str:
        try:
            ms = int(float(ms_val))
        except (ValueError, TypeError):
            return str(ms_val)
        secs = ms // 1000
        days, secs = divmod(secs, 86400)
        hours, secs = divmod(secs, 3600)
        mins, _ = divmod(secs, 60)
        parts = []
        if days:
            parts.append(f"{days}d")
        if hours:
            parts.append(f"{hours}h")
        if mins:
            parts.append(f"{mins}m")
        return " ".join(parts) if parts else "0m"

    @staticmethod
    def _format_number(val) -> str:
        try:
            n = float(val)
        except (ValueError, TypeError):
            return str(val)
        if n >= 1_000_000:
            return f"{n / 1_000_000:.1f}M"
        if n >= 1_000:
            return f"{n / 1_000:.1f}K"
        return str(int(n))

    def get_profile(self, username: str) -> dict:
        url = f"{self.BASE_URL}/{username}"
        resp = self.session.get(url, timeout=self.timeout)
        resp.raise_for_status()

        html = resp.text

        props = self._extract_rsc_props(html)
        if props is None:
            raise ValueError("Player not found on donutstats.net")

        result = {"username": props.get("username", username)}

        stats = props.get("stats", {})
        if stats:
            stat_map = {
                "money": "Money",
                "shards": "Shards",
                "kills": "Kills",
                "deaths": "Deaths",
                "playtime": "Playtime",
                "placed_blocks": "Blocks Placed",
                "broken_blocks": "Blocks Broken",
                "mobs_killed": "Mobs Killed",
                "money_spent_on_shop": "Money Spent on Shop",
                "money_made_from_sell": "Money Made from Sell",
            }
            parsed_stats = {}
            for key, label in stat_map.items():
                val = stats.get(key)
                if val is None:
                    continue
                if key == "playtime":
                    parsed_stats[label] = self._ms_to_human(val)
                else:
                    parsed_stats[label] = self._format_number(val)
            if parsed_stats:
                result["stats"] = parsed_stats

            try:
                kills = int(stats.get("kills", 0))
                deaths = int(stats.get("deaths", 0))
                if deaths > 0:
                    result["kd_ratio"] = str(round(kills / deaths, 2))
            except (ValueError, TypeError):
                pass

        online = props.get("onlineStatus", {})
        if online:
            result["online"] = online.get("is_online", False)
            loc = online.get("location")
            if loc:
                result["location"] = loc

        popularity = props.get("popularity", {})
        if popularity:
            pop = {}
            if popularity.get("profileViews"):
                pop["Profile Views"] = str(popularity["profileViews"])
            if popularity.get("searchesLast30Days"):
                pop["Searches (30d)"] = str(popularity["searchesLast30Days"])
            if popularity.get("rank"):
                pop["Popularity Rank"] = str(popularity["rank"])
            if pop:
                result["popularity"] = pop

        return result

    @staticmethod
    def _extract_rsc_props(html: str) -> dict | None:
        pattern = r'self\.__next_f\.push\(\[1,"((?:[^"\\]|\\.)*)"\]\)'
        for m in re.finditer(pattern, html):
            raw = m.group(1)
            if "stats" not in raw or "username" not in raw:
                continue
            if "money" not in raw:
                continue

            try:
                decoded = raw.encode("utf-8").decode("unicode_escape")
            except Exception:
                decoded = raw.replace('\\"', '"').replace('\\\\', '\\')

            idx = decoded.find('"stats"')
            if idx < 0:
                continue

            brace_depth = 0
            obj_start = None
            for i in range(idx - 1, -1, -1):
                ch = decoded[i]
                if ch == '}':
                    brace_depth += 1
                elif ch == '{':
                    if brace_depth == 0:
                        obj_start = i
                        break
                    brace_depth -= 1

            if obj_start is None:
                continue

            brace_depth = 0
            obj_end = None
            for i in range(obj_start, len(decoded)):
                ch = decoded[i]
                if ch == '{':
                    brace_depth += 1
                elif ch == '}':
                    brace_depth -= 1
                    if brace_depth == 0:
                        obj_end = i + 1
                        break

            if obj_end is None:
                continue

            blob = decoded[obj_start:obj_end]
            blob = blob.replace('"$undefined"', 'null')

            try:
                data = json.loads(blob)
            except json.JSONDecodeError:
                continue

            if "stats" in data:
                return data

        return None
