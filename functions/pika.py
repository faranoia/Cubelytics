import requests


class PikaClient:
    BASE_URL = "https://stats.pika-network.net/api/profile"

    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "cubelytics/1.0"})

    def get_profile(self, username: str) -> dict:
        url = f"{self.BASE_URL}/{username}"
        resp = self.session.get(url, timeout=self.timeout)

        if resp.status_code == 404:
            raise ValueError(f"Not found: {username}")
        if resp.status_code != 200:
            raise Exception(f"Request failed: {resp.status_code} {resp.text}")

        return resp.json()
