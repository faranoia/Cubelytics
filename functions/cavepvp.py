import requests
from bs4 import BeautifulSoup


class CavePvPClient:

    BASE_URL = "https://cavepvp.com/u"

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

    def get_profile(self, username: str) -> dict:
        url = f"{self.BASE_URL}/{username}"
        resp = self.session.get(url, timeout=self.timeout)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")
        result = {}

        details = soup.select_one("div.card-user-details")
        if not details:
            raise ValueError("Player not found on cavepvp.com")

        name_el = details.select_one("div.username")
        if name_el:
            result["username"] = name_el.get_text(strip=True)

        rank_el = details.select_one("div.rank span")
        if rank_el:
            result["rank"] = rank_el.get_text(strip=True)

        meta = details.select_one("div.user-small-meta")
        if meta:
            for div in meta.find_all("div"):
                text = div.get_text(" ", strip=True)
                if "Joined" in text:
                    result["joined"] = text

        last_seen = soup.select_one("div.card-footer.last-seen")
        if last_seen:
            text = last_seen.get_text(" ", strip=True)
            if text:
                result["last_seen"] = text

        stat_grid = soup.select_one("div.stat-grid")
        if stat_grid:
            games = {}
            for card in stat_grid.select("div.card"):
                header = card.select_one("div.card-header span")
                if not header:
                    continue
                game_name = header.get_text(strip=True)
                if not game_name:
                    continue

                stats = {}
                for li in card.select("li.list-group-item"):
                    label_el = li.select_one("div.fw-bold")
                    value_el = li.select_one("span.badge")
                    if label_el and value_el:
                        label = label_el.get_text(strip=True)
                        value = value_el.get_text(strip=True)
                        if label and value:
                            stats[label] = value

                if stats:
                    games[game_name] = stats

            if games:
                result["games"] = games

        if not result:
            raise ValueError("Player not found on cavepvp.com")

        return result
