# DaData INN → official domain

A small, auditable agentic pipeline for the DaData analyst take-home. It accepts a Russian organisation INN and returns the organisation's **official website domain** or `null` when the evidence is insufficient.

The implementation deliberately separates deterministic evidence collection from the LLM decision:

```text
INN → DaData party lookup → organisation identity
                         ↘ web search candidates → URL/domain normalization
                                                   ↘ LLM evidence assessment → JSON result
```

The LLM receives only the organisation identity and bounded search evidence. It must return structured JSON and cite the evidence URLs that support its decision. A deterministic guard rejects a domain that is absent from the evidence set, a search-provider domain, or unsupported by citations.

## Requirements

- Python 3.11+
- A DaData API key (`DADATA_API_KEY`) for authoritative INN → organisation identity
- A Web Search API key (`BRAVE_SEARCH_API_KEY`) for candidate discovery
- An OpenAI-compatible LLM API key (`LLM_API_KEY`) for evidence assessment

The assessment document explicitly expects AI development tools and asks for a Web Search + LLM solution. The CLI keeps credentials in environment variables; none are written to files or logs.

## Setup

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e '.[dev]'

export DADATA_API_KEY='…'
export BRAVE_SEARCH_API_KEY='…'
export LLM_API_KEY='…'
# Optional when using a non-default OpenAI-compatible endpoint/model:
export LLM_BASE_URL='https://api.openai.com/v1'
export LLM_MODEL='gpt-4o-mini'
```

For direct verification with the assignment example:

```bash
dadata-site-finder 7721581040
# {"domain":"dadata.ru"}
```

## CLI contract

Input: one 10- or 12-digit Russian INN.

Output is always one JSON object on stdout:

```json
{"domain":"dadata.ru"}
```

or

```json
{"domain":null}
```

Operational diagnostics go to stderr. The process exits non-zero only for invalid input or unavailable required providers; an evidence-based no-match is a successful `{"domain": null}` result.

## Quality, confidence and limitations

### Candidate collection

1. DaData's `findById/party` endpoint resolves the official legal name, registration identifiers, address, and any source-level web field.
2. Brave Search queries the legal name plus the INN and `официальный сайт`.
3. The pipeline normalizes URLs to registrable-looking hostnames, removes tracking parameters and filters search-engine/social/network domains.
4. A source web domain, when available, is retained as a high-priority candidate, but is still sent through the same assessment contract.

### LLM decision and safeguards

The assessor is asked to choose a domain only if search snippets and URLs establish it as the organisation's official site. Otherwise it must return `null`. It returns a confidence level, short rationale, and supporting URLs. The application then validates the schema and accepts a domain only when:

- it appears in collected evidence;
- it is not in the blocked platform/search-domain list;
- at least one cited evidence URL has that domain;
- confidence is `high` or `medium`.

This makes false positives fail closed. The resulting JSON is intentionally minimal; an `--explain` flag emits a redacted decision trace to stderr for review.

### Updating the directory

A production directory can persist every run with the INN, resolved identity fingerprint, accepted domain, confidence, evidence URLs, timestamps and reviewer feedback. Refresh jobs can prioritise old entries, legal-name/address changes, domains with repeated low confidence, and user reports. Quality can be measured using a labelled sample: precision of accepted domains, coverage, `null` rate, disagreement rate across reruns, and time-to-detect a stale domain.

### Known limitations

- Organisations without an independently indexed official website legitimately return `null`.
- Legal-name collisions, holding-company sites and franchise pages require conservative rejection unless the evidence directly links the exact INN/legal entity.
- Search snippets can lag a rebrand or domain migration. The implementation therefore returns `null` rather than guessing and retains evidence URLs for later refresh/review.
- Real provider credentials are intentionally not bundled. Unit tests use deterministic HTTP fakes and cover the assignment's expected result.

## Development

```bash
pip install -e '.[dev]'
pytest -q
```

## Repository layout

- `src/dadata_site_finder/` — provider clients, normalization, LLM assessment and CLI
- `tests/` — isolated tests using fake HTTP sessions
- `docs/solution.md` — concise design notes for submission

