import re
import requests
from bs4 import BeautifulSoup


_ZERO_VALUES = {"0", "-", "0%", "00:00", "0s", "0h0m0s", "N/A", ""}


def _is_zero(value: str) -> bool:
    return value.strip().replace(",", "") in _ZERO_VALUES


class HypixelClient:

    BASE_URL = "https://plancke.io/hypixel/player/stats"

    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://plancke.io/",
        })


    def get_profile(self, identifier: str) -> dict:
        url = f"{self.BASE_URL}/{identifier}"
        resp = self.session.get(url, timeout=self.timeout)

        if resp.status_code != 200:
            raise Exception(f"Request failed: {resp.status_code}")

        soup = BeautifulSoup(resp.text, "html.parser")

        title = soup.find("title")
        if title and "not found" in title.text.lower():
            raise ValueError(f"Player '{identifier}' not found on Hypixel")

        result = {}

        info = self._parse_player_info(soup)
        if info:
            result["player_info"] = info
        status = self._parse_status(soup)
        if status:
            result["status"] = status

        socials = self._parse_socials(soup, resp.text)
        if socials:
            result["socials"] = socials
        games = self._parse_game_panels(soup)
        if games:
            result["games"] = games

        if not result:
            raise ValueError(f"No stats found for '{identifier}'")

        return result

    def _parse_player_info(self, soup: BeautifulSoup) -> dict:
        info = {}
        cards = soup.find_all("div", class_="card-box")

        for card in cards:
            header = card.find("h3", class_="header-title")
            if header and "Player Information" in header.text:
                text = card.get_text(separator="\n")
                for line in text.split("\n"):
                    line = line.strip()
                    if ":" in line:
                        key, _, val = line.partition(":")
                        key = key.strip().strip("*")
                        val = val.strip()
                        if key and val and key != "Player Information":
                            info[key] = val
                break
        return info

    def _parse_status(self, soup: BeautifulSoup) -> str:
        cards = soup.find_all("div", class_="card-box")
        for card in cards:
            header = card.find("h4", class_="header-title")
            if header and "Status" in header.text:
                b = card.find("b")
                if b:
                    return b.text.strip()
        return "Unknown"

    def _parse_socials(self, soup: BeautifulSoup, raw_html: str) -> dict:
        socials = {}

        social_links = soup.find_all("a", id=re.compile(r"^social_"))
        for link in social_links:
            social_id = link.get("id", "")            
            platform = social_id.replace("social_", "").capitalize()

            pattern = re.compile(
                r'"\#' + re.escape(social_id) + r'".*?swal\(\s*"[^"]*"\s*,\s*"([^"]*)"',
                re.DOTALL,
            )
            m = pattern.search(raw_html)
            if m:
                socials[platform] = m.group(1)
            else:
                href = link.get("href", "")
                if href and href != "javascript:void(0)":
                    socials[platform] = href
                else:
                    socials[platform] = "linked"

        return socials

    def _parse_game_panels(self, soup: BeautifulSoup) -> dict:
        games = {}
        panels = soup.find_all("div", class_="stat_panel")

        for panel in panels:
            title_a = panel.find("a")
            if not title_a:
                continue
            game_name = title_a.text.strip()

            body = panel.find("div", class_="panel-body")
            if not body:
                continue

            game_data = {}

            stats = self._parse_bold_pairs(body)
            if stats:
                game_data["stats"] = stats
            tables = self._parse_tables(body)
            if tables:
                game_data["tables"] = tables

            if game_data:
                games[game_name] = game_data

        return games

    def _parse_bold_pairs(self, container) -> dict:
        pairs = {}
        for b_tag in container.find_all("b", recursive=True):
            text = b_tag.text.strip()
            if text.endswith(":"):
                key = text[:-1].strip()
                val = ""
                sibling = b_tag.next_sibling
                if sibling:
                    val = str(sibling).strip() if not hasattr(sibling, "text") else sibling.text.strip()
                if key and val and not _is_zero(val):
                    pairs[key] = val
        return pairs

    def _parse_tables(self, container) -> list:
        tables = []
        for table in container.find_all("table", class_="table"):
            parsed = self._parse_single_table(table)
            if parsed:
                tables.append(parsed)
        return tables

    def _parse_single_table(self, table) -> dict | None:
        headers = []
        thead = table.find("thead")
        if thead:
            header_rows = thead.find_all("tr")
            if header_rows:
                last_row = header_rows[-1]
                for th in last_row.find_all(["th", "td"]):
                    headers.append(th.text.strip())

        rows = []
        for tr in table.find_all("tr"):
            if tr.parent and tr.parent.name == "thead":
                continue
            cells = []
            for td in tr.find_all(["td", "th"]):
                cells.append(td.text.strip())
            if cells and any(c for c in cells):
                rows.append(cells)

        if not headers and not rows:
            return None

        if headers:
            data_rows = []
            for row in rows:
                values = row[1:]
                if values and all(_is_zero(v) for v in values):
                    continue
                entry = {}
                for i, h in enumerate(headers):
                    if i < len(row) and h:
                        entry[h] = row[i]
                if entry:
                    data_rows.append(entry)
            if not data_rows:
                return None
            return {"headers": headers, "rows": data_rows}

        filtered = [r for r in rows if not all(_is_zero(c) for c in r)]
        if not filtered:
            return None
        return {"rows": filtered}
