import requests


class LabyNetClient:
    SEARCH_URL = "https://laby.net/api/search/names"
    USER_URL = "https://laby.net/api/user"

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
        uuid = self._resolve_uuid(username)
        if uuid is None:
            raise ValueError("Player not found on laby.net")

        snippet = self._get_snippet(uuid)
        if snippet is None:
            raise ValueError("Player not found on laby.net")

        result = {}

        user = snippet.get("user", {})
        result["username"] = user.get("username") or user.get("name", username)
        result["uuid"] = user.get("uuid", uuid)
        history = snippet.get("name_history", [])
        if history:
            names = []
            for entry in history:
                rec = {"name": entry.get("name", "")}
                changed = entry.get("changed_at")
                if changed:
                    rec["changed_at"] = changed
                last_seen = entry.get("last_seen_at")
                if last_seen:
                    rec["last_seen"] = last_seen
                names.append(rec)
            if names:
                result["name_history"] = names

            last_entry = history[-1]
            last_seen = last_entry.get("last_seen_at")
            if last_seen:
                result["last_seen"] = last_seen

        badges = snippet.get("badges", [])
        if badges:
            result["badges"] = [
                b.get("name", b.get("id", str(b))) for b in badges
            ]

        settings = snippet.get("settings", {})
        bg = settings.get("background")
        if bg and bg != "NONE":
            result["background"] = bg

        return result

    def _resolve_uuid(self, username: str) -> str | None:
        resp = self.session.get(
            f"{self.SEARCH_URL}/{username}",
            timeout=self.timeout,
        )
        if resp.status_code != 200:
            return None
        data = resp.json()
        results = data.get("results", [])
        for r in results:
            if r.get("user_name", "").lower() == username.lower():
                return r["uuid"]
            if r.get("name", "").lower() == username.lower():
                return r["uuid"]
        if results:
            return results[0].get("uuid")
        return None

    def _get_snippet(self, uuid: str) -> dict | None:
        resp = self.session.get(
            f"{self.USER_URL}/{uuid}/get-snippet",
            timeout=self.timeout,
        )
        if resp.status_code != 200:
            return None
        return resp.json()
