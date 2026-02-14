import re

import requests
from bs4 import BeautifulSoup


class MCBrawlClient:
    BASE_URL = "https://www.mcbrawl.com/players"

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

        html = resp.text

        if "page-header" not in html:
            raise ValueError("Player not found on mcbrawl.com")

        soup = BeautifulSoup(html, "html.parser")
        result = {}

        header = soup.find("div", class_="page-header")
        if header:
            badge = header.find("span", class_="badge")
            if badge:
                rank = badge.get_text(strip=True)
                if rank:
                    result["rank"] = rank

        general = {}
        general_header = soup.find("h3", string=re.compile(r"General"))
        if general_header:
            table = general_header.find_next("table")
            if table:
                for row in table.find_all("tr"):
                    cols = row.find_all("td")
                    if len(cols) == 2:
                        key = cols[0].get_text(strip=True)
                        val = cols[1].get_text(strip=True)
                        if key and val:
                            general[key] = val
        if general:
            result["general"] = general

        games = {}

        for thumb in soup.select("div.thumbnail.game-thumb"):
            caption = thumb.find("div", class_="caption")
            if not caption:
                continue

            h3 = caption.find("h3")
            if not h3:
                continue
            game_name = h3.get_text(strip=True)
            if not game_name:
                continue

            stats = self._parse_list_group(caption)

            view_more = caption.find("a", attrs={"data-target": True})
            if view_more:
                modal_id = view_more["data-target"]
                modal = soup.select_one(modal_id)
                if modal:
                    modal_body = modal.find("div", class_="modal-body")
                    if modal_body:
                        detailed = self._parse_list_group(modal_body)
                        if detailed:
                            stats = detailed

                        tabs = {}
                        for pane in modal_body.select("div.tab-pane"):
                            tab_id = pane.get("id", "")
                            for tab_link in modal_body.select("a[data-toggle='tab']"):
                                href = tab_link.get("href", "")
                                if href.lstrip("#") == tab_id:
                                    tab_name = tab_link.get_text(strip=True)
                                    tab_stats = self._parse_list_group(pane)
                                    if tab_stats:
                                        tabs[tab_name] = tab_stats
                                    break
                        if tabs:
                            stats["classes"] = tabs

            if stats:
                games[game_name] = stats

        if games:
            result["games"] = games

        if not result:
            raise ValueError("Player not found on mcbrawl.com")

        return result

    @staticmethod
    def _parse_list_group(container) -> dict:
        data = {}
        for li in container.find_all("li", class_="list-group-item", recursive=True):
            text = li.get_text(strip=True)
            badge = li.find("span", class_="badge")
            if badge:
                val = badge.get_text(strip=True)
                key = text.replace(val, "").strip().rstrip(":")
                if key and val:
                    data[key] = val
        return data
