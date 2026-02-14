import re
import requests


class MojangClient:
    API_URL = "https://api.mojang.com"
    SESSION_URL = "https://sessionserver.mojang.com"
    GEYSER_URL = "https://api.geysermc.org/v2"

    UUID_RE = re.compile(
        r"^[0-9a-f]{8}-?[0-9a-f]{4}-?[0-9a-f]{4}-?[0-9a-f]{4}-?[0-9a-f]{12}$",
        re.IGNORECASE,
    )

    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "cubelytics/1.0"})

    @staticmethod
    def insert_dashes(raw: str) -> str:
        raw = raw.replace("-", "")
        return f"{raw[:8]}-{raw[8:12]}-{raw[12:16]}-{raw[16:20]}-{raw[20:]}"

    def is_uuid(self, text: str) -> bool:
        return bool(self.UUID_RE.match(text))

    def username_to_uuid(self, username: str) -> str:
        url = f"{self.API_URL}/users/profiles/minecraft/{username}"
        resp = self.session.get(url, timeout=self.timeout)

        if resp.status_code in (404, 204):
            raise ValueError(f"Player '{username}' not found")
        if resp.status_code != 200:
            raise ConnectionError(f"Mojang API error: {resp.status_code}")

        return self.insert_dashes(resp.json().get("id", ""))

    def uuid_to_username(self, uuid: str) -> str:
        clean = uuid.replace("-", "")
        url = f"{self.SESSION_URL}/session/minecraft/profile/{clean}"
        resp = self.session.get(url, timeout=self.timeout)

        if resp.status_code in (404, 204):
            raise ValueError(f"UUID '{uuid}' not found")
        if resp.status_code != 200:
            raise ConnectionError(f"Mojang API error: {resp.status_code}")

        return resp.json().get("name", "")

    def resolve_both(self, identifier: str) -> tuple[str, str]:
        if self.is_uuid(identifier):
            uuid = self.insert_dashes(identifier)
            username = self.uuid_to_username(uuid)
        else:
            username = identifier
            uuid = self.username_to_uuid(username)
        return uuid, username

    def resolve_bedrock(self, gamertag: str) -> str | None:
        url = f"{self.GEYSER_URL}/xbox/xuid/{gamertag}"
        try:
            resp = self.session.get(url, timeout=self.timeout)
            if resp.status_code == 200:
                data = resp.json()
                xuid = data.get("xuid")
                if xuid:
                    return str(xuid)
        except Exception:
            pass
        return None
