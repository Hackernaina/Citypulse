import httpx
from typing import Any

class HTTPClient:
    def __init__(self, base_url: str, auth_token: str | None = None):
        self.base_url = base_url.rstrip("/")
        self.auth_token = auth_token

    def headers(self) -> dict[str, str]:
        headers = {"Accept": "application/json", "User-Agent": "SentinelAPI/1.0"}
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        return headers

    async def request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        url = self.base_url + (path if path.startswith("/") else "/" + path)
        headers = kwargs.pop("headers", self.headers())
        timeout = kwargs.pop("timeout", 10.0)
        async with httpx.AsyncClient(follow_redirects=False, timeout=timeout) as client:
            return await client.request(method.upper(), url, headers=headers, **kwargs)
