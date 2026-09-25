from typing import Any
import httpx
from app.detectors.base import FindingFactory

SUSPICIOUS_FIELDS = {
    "password", "password_hash", "passwd", "secret", "secret_key",
    "token", "access_token", "refresh_token", "private_key",
    "internal_notes", "ssn", "social_security_number"
}

class ExposureDetector:
    def __init__(self, base_url: str, token: str | None):
        self.base_url = base_url.rstrip("/")
        self.token = token

    async def scan(self, endpoints, parser):
        findings = []
        headers = {"Accept": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        async with httpx.AsyncClient(timeout=8) as client:
            for ep in endpoints:
                if ep["method"] != "GET" or "{" in ep["path"]:
                    continue
                try:
                    response = await client.get(self.base_url + ep["path"], headers=headers)
                    if response.status_code != 200:
                        continue
                    data = response.json()
                except Exception:
                    continue

                if isinstance(data, dict):
                    keys = {str(k).lower() for k in data.keys()}
                    suspicious = sorted(keys.intersection(SUSPICIOUS_FIELDS))
                    if suspicious:
                        findings.append(FindingFactory.make(
                            type="EXCESSIVE_DATA_EXPOSURE",
                            title="Potential Excessive Data Exposure",
                            severity="HIGH",
                            confidence=0.88,
                            method=ep["method"],
                            endpoint=ep["path"],
                            description="The endpoint response contains fields that are commonly considered sensitive or internal.",
                            impact="Sensitive information may be exposed to API clients that do not require it.",
                            recommendation="Return only fields required by the client and enforce field-level authorization.",
                            evidence=[{"suspicious_fields": suspicious, "status_code": response.status_code}],
                            poc={"method": "GET", "url": self.base_url + ep["path"], "headers": {"Authorization": "Bearer <TOKEN>"}},
                        ))
        return findings
