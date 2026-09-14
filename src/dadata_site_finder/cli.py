from __future__ import annotations

import argparse
import json
import sys

from .assessor import OpenAICompatibleAssessor
from .pipeline import SiteFinder
from .providers import BraveSearchClient, DaDataClient, ProviderError


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Resolve a Russian organisation INN to an official website domain")
    parser.add_argument("inn", help="10- or 12-digit Russian INN")
    parser.add_argument("--explain", action="store_true", help="write an evidence summary to stderr")
    args = parser.parse_args(argv)
    try:
        finder = SiteFinder(DaDataClient(), BraveSearchClient(), OpenAICompatibleAssessor())
        result = finder.find(args.inn)
    except (ValueError, ProviderError) as error:
        print(str(error), file=sys.stderr)
        return 2
    print(json.dumps({"domain": result.domain}, ensure_ascii=False))
    if args.explain and result.assessment:
        trace = {
            "organization": {"inn": result.organization.inn, "name": result.organization.name},
            "assessment": {
                "confidence": result.assessment.confidence,
                "rationale": result.assessment.rationale,
                "supporting_urls": list(result.assessment.supporting_urls),
            },
            "evidence": [{"domain": item.domain, "url": item.url} for item in result.evidence],
        }
        print(json.dumps(trace, ensure_ascii=False), file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
