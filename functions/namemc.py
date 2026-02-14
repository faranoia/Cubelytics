import tls_client
from bs4 import BeautifulSoup


class NameMCClient:
    BASE_URL = "https://namemc.com/profile"

    def __init__(self, timeout: int = 15):
        self.timeout = timeout
        self.session = tls_client.Session(client_identifier="firefox_120")

    def get_profile(self, username: str) -> dict:
        url = f"{self.BASE_URL}/{username}"
        resp = self.session.get(url, timeout_seconds=self.timeout)

        if resp.status_code in (301, 302, 303, 307, 308):
            location = resp.headers.get("Location", "")
            if location:
                if location.startswith("/"):
                    location = f"https://namemc.com{location}"
                resp = self.session.get(location, timeout_seconds=self.timeout)

        if resp.status_code != 200:
            raise ValueError(
                f"Failed to fetch NameMC profile (HTTP {resp.status_code})"
            )

        soup = BeautifulSoup(resp.text, "html.parser")
        result = {}

        h1 = soup.select_one("main h1")
        if h1:
            result["username"] = h1.get_text(strip=True)
        uuid_select = soup.select_one("#uuid-select option[value='standard']")
        if uuid_select:
            result["uuid"] = uuid_select.get_text(strip=True)
        else:
            uuid_input = soup.select_one("input[name='profile']")
            if uuid_input:
                result["uuid"] = uuid_input.get("value", "")

        for row in soup.select(".card-body .row.g-0"):
            label = row.select_one("strong")
            if label and label.get_text(strip=True) == "Views":
                value_col = row.select_one(".col-auto")
                if value_col:
                    result["views"] = value_col.get_text(strip=True)

        for row in soup.select(".card-body .row.g-0"):
            label = row.select_one("strong")
            if label and label.get_text(strip=True) == "Information":
                info_items = []
                for a_tag in row.select("a[data-bs-content]"):
                    content = a_tag.get("data-bs-content", "").strip()
                    if content:
                        content = content.replace("\ufeff", "")
                        info_items.append(content)
                if info_items:
                    result["information"] = info_items

        history_card = None
        for card in soup.select(".card"):
            header = card.select_one(".card-header strong")
            if header and "Name History" in header.get_text():
                history_card = card
                break

        if history_card:
            names = []
            for tr in history_card.select("tbody tr"):
                if "d-lg-none" in tr.get("class", []):
                    continue

                cells = tr.select("td")
                if len(cells) < 2:
                    continue

                name_link = tr.select_one("a[translate='no']")
                if not name_link:
                    continue

                entry = {"name": name_link.get_text(strip=True)}

                time_el = tr.select_one("time[data-type='date']")
                if time_el:
                    entry["date"] = time_el.get("datetime", "")
                duration_cells = tr.select("td.text-center")
                for dc in duration_cells:
                    text = dc.get_text(strip=True)
                    if text.startswith("~"):
                        entry["duration"] = text

                names.append(entry)

            if names:
                result["name_history"] = names

        for card in soup.select(".card"):
            header = card.select_one(".card-header strong")
            if header and "Skins" in header.get_text():
                skins_link = header.select_one("a")
                if skins_link:
                    result["skins_count"] = skins_link.get_text(strip=True)

        if not result:
            raise ValueError("Player not found on namemc.com")

        return result
