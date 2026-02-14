import requests


class HiveClient:

    BASE_URL = "https://api.playhive.com/v0/game/all/all"

    def __init__(self, timeout: int = 15):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "cubelytics/1.0"})

    def get_profile(self, identifier: str) -> dict:
        url = f"{self.BASE_URL}/{identifier}"
        resp = self.session.get(url, timeout=self.timeout)

        if resp.status_code == 404:
            raise ValueError(f"Not found: {identifier}")
        if resp.status_code != 200:
            raise Exception(f"Request failed: {resp.status_code} {resp.text}")

        return resp.json()
