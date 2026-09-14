from __future__ import annotations

from .assessor import Assessor
from .models import Assessment, Evidence, Organization, Result, is_blocked_domain, normalize_domain, validate_inn
from .providers import BraveSearchClient, DaDataClient


class SiteFinder:
    def __init__(self, dadata: DaDataClient, search: BraveSearchClient, assessor: Assessor):
        self.dadata = dadata
        self.search = search
        self.assessor = assessor

    def find(self, inn: str) -> Result:
        inn = validate_inn(inn)
        organization = self.dadata.lookup(inn)
        evidence = self.search.search(organization)
        if organization.source_domain:
            evidence.insert(0, Evidence(
                url=f"https://{organization.source_domain}",
                title="DaData source website",
                snippet="Website domain supplied with entity data.",
                domain=organization.source_domain,
            ))
        assessment = self.assessor.assess(organization, evidence)
        accepted = self._accept(assessment, evidence)
        return Result(
            domain=accepted,
            organization=organization,
            evidence=tuple(evidence),
            assessment=assessment,
        )

    @staticmethod
    def _accept(assessment: Assessment, evidence: list[Evidence]) -> str | None:
        domain = normalize_domain(assessment.domain)
        if not domain or assessment.confidence not in {"high", "medium"} or is_blocked_domain(domain):
            return None
        evidence_urls = {item.url for item in evidence}
        evidence_domains = {item.domain for item in evidence}
        if domain not in evidence_domains:
            return None
        cited_domains = {normalize_domain(url) for url in assessment.supporting_urls if url in evidence_urls}
        if domain not in cited_domains:
            return None
        return domain
