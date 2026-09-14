from __future__ import annotations

import json
import os
from typing import Protocol

import requests

from .models import Assessment, Evidence, Organization, normalize_domain
from .providers import ProviderError


class Assessor(Protocol):
    def assess(self, organization: Organization, evidence: list[Evidence]) -> Assessment: ...


class OpenAICompatibleAssessor:
    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
        session: requests.Session | None = None,
    ):
        self.api_key = api_key or os.environ.get("LLM_API_KEY")
        self.base_url = (base_url or os.environ.get("LLM_BASE_URL") or "https://api.openai.com/v1").rstrip("/")
        self.model = model or os.environ.get("LLM_MODEL") or "gpt-4o-mini"
        self.session = session or requests.Session()

    def assess(self, organization: Organization, evidence: list[Evidence]) -> Assessment:
        if not self.api_key:
            raise ProviderError("LLM_API_KEY is required")
        rows = [
            {"url": item.url, "domain": item.domain, "title": item.title, "snippet": item.snippet}
            for item in evidence[:10]
        ]
        prompt = {
            "task": "Identify the official website domain for one legal entity conservatively.",
            "organization": {
                "inn": organization.inn,
                "name": organization.name,
                "ogrn": organization.ogrn,
                "address": organization.address,
                "source_domain": organization.source_domain,
            },
            "evidence": rows,
            "rules": [
                "Choose a domain only when evidence directly supports it as the official website for this exact entity.",
                "Never infer a domain that is not represented by an evidence URL.",
                "Return null on ambiguity, a holding-company-only site, aggregators, social networks, or insufficient evidence.",
                "supporting_urls must contain the evidence URLs that justify the choice.",
            ],
            "response_schema": {
                "domain": "string or null",
                "confidence": "high|medium|low",
                "rationale": "short string",
                "supporting_urls": ["URL"],
            },
        }
        response = self.session.post(
            f"{self.base_url}/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            json={
                "model": self.model,
                "temperature": 0,
                "response_format": {"type": "json_object"},
                "messages": [
                    {"role": "system", "content": "You are a cautious entity-resolution reviewer. Return JSON only."},
                    {"role": "user", "content": json.dumps(prompt, ensure_ascii=False)},
                ],
            },
            timeout=45,
        )
        if response.status_code != 200:
            raise ProviderError(f"LLM assessment failed with HTTP {response.status_code}")
        try:
            content = response.json()["choices"][0]["message"]["content"]
            data = json.loads(content)
            confidence = str(data.get("confidence", "low")).lower()
            if confidence not in {"high", "medium", "low"}:
                confidence = "low"
            urls = tuple(str(url) for url in data.get("supporting_urls", []) if isinstance(url, str))
            return Assessment(
                domain=normalize_domain(data.get("domain")),
                confidence=confidence,
                rationale=str(data.get("rationale", ""))[:1000],
                supporting_urls=urls,
            )
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
            raise ProviderError("LLM returned an invalid structured assessment") from error
