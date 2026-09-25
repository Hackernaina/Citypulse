from datetime import datetime, timezone
from typing import Any
import json
import httpx

from app.parser.openapi_parser import OpenAPIParser
from app.detectors.bola_detector import BOLADetector
from app.detectors.exposure_detector import ExposureDetector
from app.detectors.rate_limit_detector import RateLimitDetector
from app.detectors.auth_detector import AuthDetector

class ScannerEngine:
    def __init__(
        self,
        target_url: str,
        auth_token: str | None = None,
        second_auth_token: str | None = None,
        openapi_url: str | None = None,
        spec: dict[str, Any] | None = None,
        enable_bola: bool = True,
        enable_exposure: bool = True,
        enable_rate_limit: bool = True,
        enable_auth_checks: bool = True,
    ):
        self.target_url = target_url.rstrip("/")
        self.auth_token = auth_token
        self.second_auth_token = second_auth_token
        self.openapi_url = openapi_url
        self.spec = spec
        self.enable_bola = enable_bola
        self.enable_exposure = enable_exposure
        self.enable_rate_limit = enable_rate_limit
        self.enable_auth_checks = enable_auth_checks

    async def load_spec(self) -> dict[str, Any]:
        if self.spec:
            return self.spec
        url = self.openapi_url or f"{self.target_url}/openapi.json"
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.json()

    async def run(self) -> dict[str, Any]:
        spec = await self.load_spec()
        parser = OpenAPIParser(spec)
        endpoints = parser.endpoints()
        findings = []

        detectors = []
        if self.enable_bola:
            detectors.append(BOLADetector(self.target_url, self.auth_token, self.second_auth_token))
        if self.enable_exposure:
            detectors.append(ExposureDetector(self.target_url, self.auth_token))
        if self.enable_rate_limit:
            detectors.append(RateLimitDetector(self.target_url, self.auth_token))
        if self.enable_auth_checks:
            detectors.append(AuthDetector(self.target_url, self.auth_token))

        for detector in detectors:
            findings.extend(await detector.scan(endpoints, parser))

        severity_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "INFO": 4}
        findings.sort(key=lambda x: severity_order.get(x.severity, 5))

        counts = {level: sum(1 for f in findings if f.severity == level)
                  for level in severity_order}

        return {
            "scan": {
                "target": self.target_url,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "endpoints_scanned": len(endpoints),
                "findings_count": len(findings),
            },
            "summary": counts,
            "endpoints": endpoints,
            "findings": [f.model_dump() for f in findings],
        }
