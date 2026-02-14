import requests


class CentralTierListClient:
    BASE_URL = "https://api.centraltierlist.com/api"

    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "mcsint/1.0"
        })

    def get_profile(self, identifier: str) -> dict:
        url = f"{self.BASE_URL}/search_profile/{identifier}"

        response = self.session.get(url, timeout=self.timeout)

        if response.status_code == 404:
            raise ValueError(f"Not found: {identifier}")
        if response.status_code != 200:
            raise Exception(
                f"Request failed: {response.status_code} {response.text}"
            )

        return response.json()
