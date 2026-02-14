import requests
from bs4 import BeautifulSoup


class LeoneMCClient:
    BASE_URL = "https://leonemc.net/user"

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

        name_el = soup.select_one("h1.font-bold.text-2xl")
        if not name_el:
            raise ValueError("Player not found on leonemc.net")
        result["username"] = name_el.get_text(strip=True)
        rank_el = soup.select_one("span.rounded-full.uppercase")
        if rank_el:
            result["rank"] = rank_el.get_text(strip=True)

        for h1 in soup.find_all("h1"):
            text = h1.get_text(strip=True)
            if text.startswith("Joined"):
                blue = h1.select_one("span.text-blue-400")
                if blue:
                    result["joined"] = blue.get_text(strip=True)
                break

        for h1 in soup.find_all("h1"):
            text = h1.get_text(" ", strip=True)
            if "Last seen" in text:
                result["last_seen"] = text
                break

        stat_grid = soup.select_one("div.grid")
        if stat_grid:
            games = {}
            for card in stat_grid.children:
                if not hasattr(card, "select_one"):
                    continue

                header_h1 = card.select_one("h1.text-white.text-2xl")
                if not header_h1:
                    continue
                game_name = header_h1.get_text(strip=True)
                if not game_name:
                    continue

                stats = {}
                for row in card.select("div.justify-between"):
                    label_el = row.select_one("h1.font-bold")
                    value_el = row.select_one("span.bg-green-500")
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
            raise ValueError("Player not found on leonemc.net")

        return result
