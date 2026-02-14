import requests


class ReafyClient:
    BASE_URL = "https://gogy.reafystats.com/api/v1/players/"

    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "cubelytics/1.0"})

    def get_profile(self, username: str) -> dict:
        resp = self.session.get(
            self.BASE_URL,
            params={"query": username},
            timeout=self.timeout,
        )

        if resp.status_code == 404:
            raise ValueError(f"Not found: {username}")
        if resp.status_code != 200:
            raise Exception(f"Request failed: {resp.status_code} {resp.text}")

        data = resp.json()

        if isinstance(data, list):
            if not data:
                raise ValueError(f"Not found: {username}")
            return data[0]

        return data
