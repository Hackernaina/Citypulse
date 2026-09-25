from pydantic import BaseModel, Field
from typing import Any

class Finding(BaseModel):
    id: str
    type: str
    title: str
    severity: str
    confidence: float = Field(ge=0, le=1)
    method: str
    endpoint: str
    description: str
    impact: str
    recommendation: str
    evidence: list[dict[str, Any]] = []
    poc: dict[str, Any] = {}
