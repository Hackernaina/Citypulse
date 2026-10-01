import re
from typing import Any
import httpx
from app.detectors.base import FindingFactory

ID_NAMES = {"id", "user_id", "userid", "userId", "order_id", "orderId", "account_id", "accountId"}

class BOLADetector:
    def __init__(self, base_url: str, token_a: str | None, token_b: str | None):
        self.base_url = base_url.rstrip("/")
        self.token_a = token_a
        self.token_b = token_b

    async def scan(self, endpoints: list[dict[str, Any]], parser):
        if not self.token_a or not self.token_b:
            return []
        findings = []
        for ep in endpoints:
            if ep["method"] not in {"GET", "PUT", "PATCH", "DELETE"}:
                continue
            path = ep["path"]
            if "{" not in path:
                continue
            params = re.findall(r"{([^}]+)}", path)
            if not any(p in ID_NAMES or p.lower().endswith("_id") for p in params):
                continue

            values = {}
            for p in params:
                values[p] = "101" if "order" in p.lower() else "1"
            candidate = path
            for p, value in values.items():
                candidate = candidate.replace("{" + p + "}", value)

            url = self.base_url + candidate
            async with httpx.AsyncClient(timeout=8) as client:
                headers_a = {"Authorization": f"Bearer {self.token_a}", "Accept": "application/json"}
                headers_b = {"Authorization": f"Bearer {self.token_b}", "Accept": "application/json"}
                try:
                    a = await client.request(ep["method"], url, headers=headers_a)
                    b = await client.request(ep["method"], url, headers=headers_b)
                except Exception:
                    continue

            if a.status_code == 200 and b.status_code == 200:
                # Demo heuristic: both authenticated identities can retrieve the same object.
                # Real-world BOLA confirmation requires an ownership oracle.
                findings.append(FindingFactory.make(
                    type="BOLA",
                    title="Possible Broken Object Level Authorization",
                    severity="HIGH",
                    confidence=0.72,
                    method=ep["method"],
                    endpoint=ep["path"],
                    description="The same object identifier returned a successful response for two different authenticated sessions. This is evidence of a possible object-level authorization weakness.",
                    impact="An authenticated user may be able to access an object that belongs to another user.",
                    recommendation="Enforce server-side ownership checks for every object identifier before returning or modifying the object.",
                    evidence=[
                        {"session": "User A", "status_code": a.status_code, "url": url},
                        {"session": "User B", "status_code": b.status_code, "url": url},
                    ],
                    poc={"method": ep["method"], "url": url, "headers": {"Authorization": "Bearer <USER_TOKEN>"}},
                ))
        return findings
