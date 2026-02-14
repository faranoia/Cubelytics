import re

import requests
from bs4 import BeautifulSoup


class ExtremeCraftClient:
    BASE_URL = "https://www.extremecraft.net/players"

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
        profile_url = f"{self.BASE_URL}/{username}/"
        resp = self.session.get(profile_url, timeout=self.timeout)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")
        result = {}

        user_section = soup.select_one("div.youplay-user div.user-data")
        if not user_section:
            raise ValueError("Player not found on extremecraft.net")

        h1 = user_section.find("h1")
        if h1:
            result["username"] = h1.get_text(strip=True)

        for loc in user_section.select("div.location"):
            text = loc.get_text(strip=True)
            if not text:
                continue
            if "Joined" in text or "joined" in text:
                result["joined"] = text
            else:
                result["rank"] = text

        content = soup.select_one("div.youplay-content div.col-md-12")
        if content:
            p = content.find("p")
            if p:
                desc = p.get_text(strip=True)
                if desc:
                    result["description"] = desc

        offenses_url = None
        nav = soup.select_one("div.youplay-user-navigation")
        if nav:
            for a in nav.find_all("a", href=True):
                if "/offenses/" in a["href"]:
                    href = a["href"]
                    if href.startswith("http"):
                        offenses_url = href
                    else:
                        offenses_url = f"https://www.extremecraft.net/{href.lstrip('/')}"
                    break

        if not offenses_url:
            offenses_url = f"{self.BASE_URL}/{username}/offenses/"

        try:
            resp2 = self.session.get(offenses_url, timeout=self.timeout)
            resp2.raise_for_status()
            soup2 = BeautifulSoup(resp2.text, "html.parser")

            offenses_content = soup2.select_one("div.youplay-content div.col-md-12")
            if offenses_content:
                no_offenses = offenses_content.find("p")
                if no_offenses and "no offenses" in no_offenses.get_text().lower():
                    result["offenses"] = "None (last 90 days)"
                else:
                    offenses = self._parse_offenses(offenses_content)
                    if offenses:
                        result["offenses"] = offenses
        except Exception:
            pass 

        if not result:
            raise ValueError("Player not found on extremecraft.net")

        return result

    @staticmethod
    def _parse_offenses(container) -> list:
        offenses = []

        table = container.find("table")
        if table:
            for row in table.find_all("tr"):
                cols = row.find_all("td")
                if cols:
                    entry = {}
                    texts = [c.get_text(strip=True) for c in cols]
                    if len(texts) >= 2:
                        entry["reason"] = texts[0]
                        entry["date"] = texts[1]
                    if len(texts) >= 3:
                        entry["duration"] = texts[2]
                    if entry:
                        offenses.append(entry)
            return offenses

        for item in container.select("div.offense, li"):
            text = item.get_text(" ", strip=True)
            if text:
                offenses.append(text)

        return offenses
