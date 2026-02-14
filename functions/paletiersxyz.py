import base64
import time
import tls_client


class PaleTiersClient:
    BASE_URL = "https://www.paletiers.xyz"
    API_URL = "https://www.paletiers.xyz/api/tiers"
    PLAYER_API = "https://www.paletiers.xyz/api/players/"

    def __init__(self, timeout: int = 15, cache_ttl: int = 60):
        self.timeout = timeout
        self.cache_ttl = cache_ttl
        self.session = tls_client.Session(
            client_identifier="firefox_120",
            random_tls_extension_order=True,
        )
        self.session.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) "
                "Gecko/20100101 Firefox/120.0"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }
        self._cache = None
        self._cache_time = 0.0
        self._session_ready = False

    def get_profile(self, username: str) -> dict:
        data = self._get_tiers()
        player = self._find_player(data, username)
        if player is None:
            raise ValueError("Player not found on paletiers.xyz")
        profile = self._get_player_profile(username)
        return self._format(player, data, profile)

    def _warm_session(self):
        if self._session_ready:
            return
        self.session.get(self.BASE_URL)
        self._session_ready = True

    def _get_tiers(self) -> dict:
        now = time.time()
        if self._cache and (now - self._cache_time) < self.cache_ttl:
            return self._cache

        self._warm_session()

        self.session.headers["Accept"] = "application/json"
        self.session.headers["Referer"] = self.BASE_URL + "/"
        resp = self.session.get(self.API_URL)
        if resp.status_code != 200:
            raise ValueError(
                f"Failed to fetch paletiers.xyz (HTTP {resp.status_code})"
            )

        data = resp.json()
        self._cache = data
        self._cache_time = now
        return data

    def _get_player_profile(self, username: str) -> dict | None:
        try:
            player_id = base64.b64encode(username.encode()).decode().rstrip("=")
            self._warm_session()
            self.session.headers["Accept"] = "application/json"
            self.session.headers["Referer"] = self.BASE_URL + "/"
            resp = self.session.get(self.PLAYER_API + player_id)
            if resp.status_code == 200:
                return resp.json()
        except Exception:
            pass
        return None

    def _find_player(self, data: dict, username: str) -> dict | None:
        target = username.lower()

        for player in data.get("overall", []):
            if (player.get("ingame_username") or "").lower() == target:
                return player
        for gm_list in (data.get("gamemodes") or {}).values():
            if isinstance(gm_list, list):
                for player in gm_list:
                    if (player.get("ingame_username") or "").lower() == target:
                        return player

        return None

    def _format(self, player: dict, data: dict, profile: dict | None = None) -> dict:
        result = {}

        if player.get("ingame_username"):
            result["username"] = player["ingame_username"]

        modes = player.get("modes") or {}
        gamemodes = {}

        for key in ("sword", "mace", "nethpot"):
            tier = (
                player.get(f"{key}_tier")
                or (modes.get(key, {}) or {}).get("tier")
            )
            score = (
                player.get(f"{key}_score")
                or (modes.get(key, {}) or {}).get("score")
            )
            if tier or score:
                gm = {}
                if tier:
                    gm["tier"] = tier
                if score is not None:
                    gm["score"] = score
                gamemodes[key] = gm

        if gamemodes:
            result["gamemodes"] = gamemodes

        total = 0
        for key in ("sword", "mace", "nethpot"):
            total += int(player.get(f"{key}_score") or 0)
        if not total:
            for m in modes.values():
                if isinstance(m, dict):
                    total += int(m.get("score") or 0)

        if total:
            result["total_score"] = total
            result["title"] = self._get_title(total)

        overall = data.get("overall", [])
        target = (player.get("ingame_username") or "").lower()
        for i, p in enumerate(overall):
            if (p.get("ingame_username") or "").lower() == target:
                result["rank"] = i + 1
                result["total_players"] = len(overall)
                break

        src = profile or player
        if src.get("discord_username"):
            result["discord"] = src["discord_username"]
        if src.get("discord_id"):
            result["discord_id"] = src["discord_id"]

        likes = (profile or {}).get("likes") or player.get("likes")
        if likes is not None:
            result["likes"] = likes

        return result

    @staticmethod
    def _get_title(score: int) -> str:
        if score >= 235:
            return "Legendary Hero"
        if score >= 225:
            return "Gladiator Supreme"
        if score >= 190:
            return "Champion Master"
        if score >= 155:
            return "Warrior Elite"
        if score >= 120:
            return "Battle Adept"
        if score >= 80:
            return "Combat Advanced"
        if score >= 40:
            return "Combat Intermediate"
        return "Combat Beginner"
