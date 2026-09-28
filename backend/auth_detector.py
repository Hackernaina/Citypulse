from typing import Any
import httpx
from app.detectors.base import FindingFactory

class AuthDetector:
    def __init__(self, base_url: str, token: str | None):
        self.base_url = base_url.rstrip("/")
        self.token = token

    async def scan(self, endpoints, parser):
        findings = []
        async with httpx.AsyncClient(timeout=8) as client:
            for ep in endpoints:
                security = ep.get("security")
                if security:
                    continue
                if ep["path"] in {"/", "/health", "/docs", "/openapi.json"}:
                    continue
                if ep["method"] != "GET" or "{" in ep["path"]:
                    continue
                try:
                    response = await client.get(self.base_url + ep["path"], headers={"Accept": "application/json"})
                except Exception:
                    continue
                if response.status_code == 200:
                    findings.append(FindingFactory.make(
                        type="AUTH_MISCONFIGURATION",
                        title="Potential Unauthenticated Sensitive Endpoint",
                        severity="MEDIUM",
                        confidence=0.65,
                        method=ep["method"],
                        endpoint=ep["path"],
                        description="The OpenAPI operation has no security requirement and returned HTTP 200 without an Authorization header.",
                        impact="An endpoint intended to be protected may be accessible without authentication.",
                        recommendation="Declare and enforce the required security scheme at the API operation or global level.",
                        evidence=[{"status_code": response.status_code, "security_requirement": security}],
                        poc={"method": "GET", "url": self.base_url + ep["path"], "headers": {}},
                    ))
        return findings
