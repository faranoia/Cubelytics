import requests


class McTiersClient:
    BASE_URL = "https://mctiers.com/api/v2"

    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "mcsint/1.0"
        })

    def get_profile(self, uuid: str) -> dict:
        url = f"{self.BASE_URL}/profile/{uuid}"

        response = self.session.get(url, timeout=self.timeout)

        if response.status_code != 200:
            raise Exception(
                f"Request failed: {response.status_code} {response.text}"
            )

        return response.json()
