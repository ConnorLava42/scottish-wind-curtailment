import time
import requests

BASE = "https://data.elexon.co.uk/bmrs/api/v1"

def get(path: str, params: dict | None = None, retries: int = 5) -> list[dict]:
    """Call an Elexon endpoint and return a list of records."""
    url = f"{BASE}{path}"
    params = {"format": "json", **(params or {})}
    for attempt in range(retries):
        r = requests.get(url, params=params, timeout=60)
        if r.status_code == 429 or r.status_code >= 500:
            time.sleep(2 ** attempt)  # back off: 1, 2, 4, 8, 16 s
            continue
        r.raise_for_status()
        body = r.json()
        # Some endpoints wrap rows in {"data": [...]}, others return a bare list
        return body["data"] if isinstance(body, dict) else body
    raise RuntimeError(f"Gave up on {url}")