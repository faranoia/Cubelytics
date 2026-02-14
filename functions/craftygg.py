import tls_client
from bs4 import BeautifulSoup


class CraftyGGClient:

    API_URL = "https://api.crafty.gg/api/v2/players"
    WEB_URL = "https://crafty.gg/@"

    def __init__(self, timeout: int = 15):
        self.timeout = timeout
        self.session = tls_client.Session(client_identifier="firefox_120")

    def get_profile(self, username: str) -> dict:
        try:
            data = self._try_api(username)
            if data:
                return data
        except Exception:
            pass

        return self._scrape_html(username)

    def _try_api(self, username: str) -> dict | None:
        resp = self.session.get(
            f"{self.API_URL}/{username}",
            timeout_seconds=self.timeout,
        )
        if resp.status_code != 200:
            return None

        try:
            raw = resp.json()
        except Exception:
            return None

        if not raw or (isinstance(raw, dict) and raw.get("error")):
            return None

        return self._parse_api(raw)

    def _parse_api(self, raw: dict) -> dict:
        result = {}

        data = raw.get("data", raw)

        if data.get("username"):
            result["username"] = data["username"]

        if data.get("uuid"):
            result["uuid"] = data["uuid"]

        if data.get("type"):
            result["account_type"] = data["type"]

        if data.get("views_monthly") is not None:
            result["views_monthly"] = data["views_monthly"]
        if data.get("upvotes_monthly") is not None:
            result["upvotes_monthly"] = data["upvotes_monthly"]
        if data.get("skins_count") is not None:
            result["skins_count"] = data["skins_count"]
        if data.get("capes_count") is not None:
            result["capes_count"] = data["capes_count"]

        if data.get("bio"):
            result["biography"] = data["bio"]

        usernames = data.get("usernames", [])
        if usernames:
            names = []
            for entry in usernames:
                name = entry.get("username") or entry.get("name", "")
                if name:
                    rec = {"name": name}
                    changed = entry.get("changed_at")
                    if changed:
                        rec["changed_at"] = changed
                    names.append(rec)
            if names:
                result["name_history"] = names

        socials = data.get("socials", [])
        if socials:
            social_list = []
            for s in socials:
                if isinstance(s, dict):
                    social_list.append(s)
                elif isinstance(s, str):
                    social_list.append({"url": s})
            if social_list:
                result["socials"] = social_list

        user = data.get("user")
        if user and isinstance(user, dict):
            if user.get("username"):
                result["claimed_by"] = user["username"]

        if not result:
            return None
        return result

    def _scrape_html(self, username: str) -> dict:
        url = f"{self.WEB_URL}{username}"
        resp = self.session.get(url, timeout_seconds=self.timeout)

        if resp.status_code in (301, 302, 303, 307, 308):
            location = resp.headers.get("Location", "")
            if location:
                if location.startswith("/"):
                    location = f"https://crafty.gg{location}"
                resp = self.session.get(location, timeout_seconds=self.timeout)

        if resp.status_code != 200:
            raise ValueError(
                f"Failed to fetch crafty.gg profile (HTTP {resp.status_code})"
            )

        soup = BeautifulSoup(resp.text, "html.parser")
        result = {}

        title = soup.select_one("h1, .username, .profile-name, [class*='username']")
        if title:
            result["username"] = title.get_text(strip=True)
        for el in soup.select("[class*='uuid'], .uuid"):
            text = el.get_text(strip=True)
            if len(text) >= 32:
                result["uuid"] = text
                break

        if "uuid" not in result:
            for el in soup.select("[data-uuid]"):
                result["uuid"] = el.get("data-uuid", "")
                break

        for el in soup.select("[class*='view'], [class*='stat']"):
            text = el.get_text(strip=True).lower()
            if "view" in text:
                num = "".join(c for c in text if c.isdigit() or c == ",")
                if num:
                    result["views"] = num

        for el in soup.select("[class*='upvote'], [class*='vote'], [class*='like']"):
            text = el.get_text(strip=True)
            num = "".join(c for c in text if c.isdigit() or c == ",")
            if num:
                result["upvotes"] = num

        names = []
        for row in soup.select(
            "[class*='name-history'] tr, "
            "[class*='namehistory'] li, "
            "[class*='history'] tr"
        ):
            cells = row.select("td")
            if cells:
                name = cells[0].get_text(strip=True)
                if name:
                    entry = {"name": name}
                    if len(cells) > 1:
                        entry["date"] = cells[1].get_text(strip=True)
                    names.append(entry)
        if names:
            result["name_history"] = names

        bio = soup.select_one("[class*='bio'], [class*='biography']")
        if bio:
            text = bio.get_text(strip=True)
            if text:
                result["biography"] = text

        if not result:
            raise ValueError("Player not found on crafty.gg")

        return result
