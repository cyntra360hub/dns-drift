# Contributing to dns-drift

Thanks for considering a contribution! This is a small, focused tool —
keep changes deterministic (no LLM calls, no paid APIs) and offline-testable
(mock the network, don't call the real DNS-over-HTTPS API in tests).

## Getting started

```bash
git clone https://github.com/cyntra360hub/dns-drift.git
cd dns-drift
pip install -e ".[dev]"
pytest
```

## Workflow

1. Open an issue first for anything beyond a trivial fix, so we can agree
   on approach before you invest time.
2. Fork, branch, make your change, add/update tests.
3. Run `pytest` — all tests must pass, and new behavior needs new tests.
4. Open a PR describing what changed and why.

## Good first issues

These are scoped to be approachable without deep familiarity with the
codebase:

- **`good-first-issue`: Add CNAME/SOA record support.** Extend
  `dns_client.RECORD_TYPES` and add tests in `test_dns_client.py` for
  the new type(s) -- the DoH API already supports any record type
  string, no new fetch logic needed.
- **`good-first-issue`: Add a `--domain` CLI flag.** Let a caller check
  a single ad-hoc domain without editing `DNS_DRIFT_DOMAINS`, useful for
  quick manual checks.
- **`good-first-issue`: Add a JSON output mode.** Add a `--json` flag (or
  `DNS_DRIFT_OUTPUT=json` env var) to `cli.py` that prints the
  `DriftResult` as machine-readable JSON instead of the human-readable
  report, for piping into other tools.
- **`good-first-issue`: Prune stale domains from the state file.** If a
  domain is removed from `DNS_DRIFT_DOMAINS`, its old snapshot lingers
  in the state file forever. Add an option to prune entries not present
  in the current domain list, with tests using `tmp_path`.
- **`good-first-issue`: Support a secondary DoH resolver as fallback.**
  `dns_client.fetch_doh` always queries `dns.google`; add a fallback to
  `https://cloudflare-dns.com/dns-query` (same JSON shape) if the
  primary query fails, with tests using an injected fetcher that fails
  once then succeeds.

## Code style

- Standard library only, including AiOps Enabler reporting
  (`signing.py`/`reporting.py` use only `hmac`/`hashlib`/
  `urllib.request` — no SDK dependency; see README).
- Keep network I/O behind an injectable `fetcher` parameter (see
  `dns_client.py`, `reporting.py`) so tests never touch the network.
- No comments explaining *what* code does — only *why*, when non-obvious.
