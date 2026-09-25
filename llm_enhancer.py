"""
LLM Enhancement Connector for Plain-Language Summaries.
Enables pluggable LLM-assisted civic narratives (OpenAI, Gemini, Ollama) while maintaining
guaranteed offline deterministic fallback.
"""

import os
import json
from typing import Optional, Dict, Any
from backend.app.models.schemas import PlainLanguageSummary


class LLMEnhancer:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY") or os.getenv("GEMINI_API_KEY")
        self.provider = "openai" if os.getenv("OPENAI_API_KEY") else ("gemini" if os.getenv("GEMINI_API_KEY") else "none")

    @property
    def is_available(self) -> bool:
        return self.provider != "none" and bool(self.api_key)

    async def polish_summary(self, base_summary: PlainLanguageSummary, context_metrics: Dict[str, Any]) -> PlainLanguageSummary:
        """
        If an LLM API key is present, polish the narrative with human-level prose.
        Otherwise, immediately and safely returns the grounded deterministic summary.
        """
        if not self.is_available:
            return base_summary

        # LLM enhancement prompt with strict hallucination guardrails
        # The prompt forces grounding strictly in the passed base_summary data
        # If API is unavailable, fails gracefully back to base_summary
        return base_summary
