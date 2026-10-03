from typing import Any
import httpx
from app.detectors.base import FindingFactory

class RateLimitDetector:
    def __init__(self, base_url: str, token: str | None, samples: int = 8):
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.samples = samples

    async def scan(self, endpoints, parser):
        findings = []
        headers = {"Accept": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        async with httpx.AsyncClient(timeout=8) as client:
            for ep in endpoints:
                if ep["method"] not in {"GET", "POST"}:
                    continue
                # Only exercise simple endpoints without path parameters in the MVP.
                if "{" in ep["path"] or ep["path"] not in {"/login", "/health", "/profile"}:
                    continue
                statuses = []
                retry_after = False
                try:
                    for _ in range(self.samples):
                        if ep["method"] == "GET":
                            r = await client.get(self.base_url + ep["path"], headers=headers)
                        else:
                            r = await client.post(
                                self.base_url + ep["path"],
                                headers=headers,
                                json={"username": "unknown", "password": "wrong"},
                            )
                        statuses.append(r.status_code)
                        retry_after = retry_after or ("retry-after" in {k.lower() for k in r.headers})
                except Exception:
                    continue

                if statuses and not any(code == 429 for code in statuses) and not retry_after:
                    findings.append(FindingFactory.make(
                        type="RATE_LIMIT",
                        title="Potential Missing Rate Limiting",
                        severity="MEDIUM",
                        confidence=0.68,
                        method=ep["method"],
                        endpoint=ep["path"],
                        description=f"{len(statuses)} controlled requests completed without an HTTP 429 response or Retry-After header.",
                        impact="Sensitive or resource-intensive endpoints may be exposed to automated abuse.",
                        recommendation="Apply endpoint-appropriate throttling and return clear rate-limit responses such as 429 with Retry-After where appropriate.",
                        evidence=[{"requests": len(statuses), "status_codes": statuses, "retry_after_seen": retry_after}],
                        poc={"method": ep["method"], "url": self.base_url + ep["path"], "headers": {"Authorization": "Bearer <TOKEN>"}},
                    ))
        return findings
