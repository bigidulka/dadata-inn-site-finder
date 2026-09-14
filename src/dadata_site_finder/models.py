from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse

BLOCKED_DOMAINS = {
    "google.com", "google.ru", "yandex.ru", "yandex.com", "bing.com",
    "brave.com", "facebook.com", "instagram.com", "vk.com", "t.me",
    "youtube.com", "linkedin.com", "wikipedia.org", "2gis.ru",
}


def validate_inn(inn: str) -> str:
    value = str(inn).strip()
    if not value.isdigit() or len(value) not in (10, 12):
        raise ValueError("INN must contain exactly 10 or 12 digits")
    return value


def normalize_domain(value: str | None) -> str | None:
    if not value:
        return None
    raw = value.strip().lower()
    if not raw:
        return None
    parsed = urlparse(raw if "://" in raw else f"https://{raw}")
    hostname = (parsed.hostname or "").rstrip(".")
    if hostname.startswith("www."):
        hostname = hostname[4:]
    if not hostname or "." not in hostname or any(c.isspace() for c in hostname):
        return None
    return hostname


def is_blocked_domain(domain: str) -> bool:
    return any(domain == blocked or domain.endswith(f".{blocked}") for blocked in BLOCKED_DOMAINS)


@dataclass(frozen=True)
class Organization:
    inn: str
    name: str
    ogrn: str | None = None
    address: str | None = None
    source_domain: str | None = None


@dataclass(frozen=True)
class Evidence:
    url: str
    title: str
    snippet: str
    domain: str


@dataclass(frozen=True)
class Assessment:
    domain: str | None
    confidence: str
    rationale: str
    supporting_urls: tuple[str, ...]


@dataclass(frozen=True)
class Result:
    domain: str | None
    organization: Organization
    evidence: tuple[Evidence, ...]
    assessment: Assessment | None
