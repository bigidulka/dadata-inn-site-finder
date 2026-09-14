from __future__ import annotations

import os
from typing import Any

import requests

from .models import Evidence, Organization, normalize_domain


class ProviderError(RuntimeError):
    pass


class DaDataClient:
    url = "https://suggestions.dadata.ru/suggestions/api/4_1/rs/findById/party"

    def __init__(self, token: str | None = None, session: requests.Session | None = None):
        self.token = token or os.environ.get("DADATA_API_KEY")
        self.session = session or requests.Session()

    def lookup(self, inn: str) -> Organization:
        if not self.token:
            raise ProviderError("DADATA_API_KEY is required")
        response = self.session.post(
            self.url,
            headers={"Authorization": f"Token {self.token}"},
            json={"query": inn},
            timeout=20,
        )
        if response.status_code != 200:
            raise ProviderError(f"DaData lookup failed with HTTP {response.status_code}")
        suggestions = response.json().get("suggestions", [])
        if not suggestions:
            raise ProviderError("DaData returned no organisation for this INN")
        item = suggestions[0]
        data: dict[str, Any] = item.get("data", {})
        name = data.get("name", {}).get("full_with_opf") or item.get("value")
        address = data.get("address", {}).get("unrestricted_value")
        return Organization(
            inn=inn,
            name=name,
            ogrn=data.get("ogrn"),
            address=address,
            source_domain=normalize_domain(data.get("website") or data.get("site")),
        )


class BraveSearchClient:
    url = "https://api.search.brave.com/res/v1/web/search"

    def __init__(self, token: str | None = None, session: requests.Session | None = None):
        self.token = token or os.environ.get("BRAVE_SEARCH_API_KEY")
        self.session = session or requests.Session()

    def search(self, organization: Organization) -> list[Evidence]:
        if not self.token:
            raise ProviderError("BRAVE_SEARCH_API_KEY is required")
        query = f'"{organization.name}" {organization.inn} официальный сайт'
        response = self.session.get(
            self.url,
            headers={"Accept": "application/json", "X-Subscription-Token": self.token},
            params={"q": query, "count": 8, "search_lang": "ru"},
            timeout=20,
        )
        if response.status_code != 200:
            raise ProviderError(f"Brave Search failed with HTTP {response.status_code}")
        rows = response.json().get("web", {}).get("results", [])
        evidence: list[Evidence] = []
        for row in rows:
            url = row.get("url", "")
            domain = normalize_domain(url)
            if domain:
                evidence.append(Evidence(
                    url=url,
                    title=row.get("title", ""),
                    snippet=row.get("description", ""),
                    domain=domain,
                ))
        return evidence
