from dadata_site_finder.models import Assessment, Evidence, Organization, normalize_domain, validate_inn
from dadata_site_finder.pipeline import SiteFinder


class FakeDaData:
    def lookup(self, inn):
        assert inn == "7721581040"
        return Organization(inn=inn, name="ООО «Дадата»", ogrn="1147746000000")


class FakeSearch:
    def search(self, organization):
        return [
            Evidence(
                url="https://dadata.ru/products/suggestions/",
                title="DaData — подсказки",
                snippet="Официальный сервис DaData",
                domain="dadata.ru",
            ),
            Evidence(
                url="https://example.org/review",
                title="Review",
                snippet="Unrelated",
                domain="example.org",
            ),
        ]


class FakeAssessor:
    def __init__(self, assessment):
        self.assessment = assessment

    def assess(self, organization, evidence):
        return self.assessment


def test_assignment_example_returns_dadata_domain():
    finder = SiteFinder(
        FakeDaData(),
        FakeSearch(),
        FakeAssessor(Assessment(
            domain="dadata.ru",
            confidence="high",
            rationale="Exact name and official product page match.",
            supporting_urls=("https://dadata.ru/products/suggestions/",),
        )),
    )
    assert finder.find("7721581040").domain == "dadata.ru"


def test_rejects_uncited_llm_hallucination():
    finder = SiteFinder(
        FakeDaData(),
        FakeSearch(),
        FakeAssessor(Assessment(
            domain="invented.example",
            confidence="high",
            rationale="Not in collected evidence.",
            supporting_urls=("https://invented.example",),
        )),
    )
    assert finder.find("7721581040").domain is None


def test_rejects_blocked_or_low_confidence_domains():
    for domain, confidence in (("google.com", "high"), ("dadata.ru", "low")):
        finder = SiteFinder(
            FakeDaData(),
            FakeSearch(),
            FakeAssessor(Assessment(domain=domain, confidence=confidence, rationale="", supporting_urls=("https://dadata.ru/products/suggestions/",))),
        )
        assert finder.find("7721581040").domain is None


def test_normalizes_domains_and_checks_inn_shape():
    assert normalize_domain("HTTPS://www.DaData.ru/path?x=1") == "dadata.ru"
    assert validate_inn("7721581040") == "7721581040"
    try:
        validate_inn("not-an-inn")
    except ValueError:
        pass
    else:
        raise AssertionError("invalid INN accepted")
