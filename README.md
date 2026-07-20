# dns-drift

A small, deterministic Python agent that watches a configurable list of
domains for **DNS record changes** (A, AAAA, MX, NS, TXT) and reports
drift between runs, keeping a state file so only genuine changes are
flagged.

No LLM calls, no paid APIs, no server to run — it's a script you run on
a schedule (cron, GitHub Actions, etc.) or by hand.

## What it does

For each configured domain, dns-drift:

1. Queries A/AAAA/MX/NS/TXT records via
   [Google's public DNS-over-HTTPS JSON API](https://developers.google.com/speed/public-dns/docs/doh/json)
   (free, no API key, plain HTTPS GET).
2. Compares the result against the last-seen snapshot in its state file.
3. Reports any record type whose value set changed since last time.
4. Saves the new snapshot for next run.

Default domains: `aiopsenabler.com`, `cyntra360hub.com`.

**Cold-start note:** on a domain's very first run (no prior snapshot),
nothing is reported as drift — there's no baseline yet to compare
against, just an initial observation. Subsequent runs only report
genuine changes.

## Install

Requires Python 3.12+.

```bash
pip install .
```

## Usage

```bash
dns-drift
```

Or as a module:

```bash
python -m dns_drift.cli
```

### Configuration (environment variables)

| Variable | Default | Meaning |
|---|---|---|
| `DNS_DRIFT_DOMAINS` | `aiopsenabler.com,cyntra360hub.com` | comma-separated domain list |
| `DNS_DRIFT_STATE_FILE` | `.state/dns_drift_state.json` | where to persist the last-seen snapshot |
| `DNS_DRIFT_TIMEOUT_SECONDS` | `10` | network timeout per DNS query |

Copy `.env.example` to `.env` to set these locally; `.env` is gitignored
and never committed.

## Optional: AiOps Enabler integration

dns-drift can optionally report each run as a signed task event to
[AiOps Enabler](https://aiopsenabler.com), a public-interest registry of
verified AI agent performance. **This is opt-in and off by default** —
the agent never phones home unless you explicitly configure credentials.

Reporting is implemented as **raw HMAC-signed REST**
(`src/dns_drift/signing.py` + `reporting.py`), built directly from the
platform's own published spec ([skill.md](https://aiopsenabler.com/skill.md) §3,
[api-guide.md](https://aiopsenabler.com/api-guide.md) §2) using only the
standard library. This is a deliberate substitution for the
officially-documented Python SDK (`aiops-enabler`): its install command
points at `github.com/cyntra360hub/aiops-enabler`, which is currently a
**private** repository and not installable by the public despite being
the documented path for external integrators. Raw signed REST sidesteps
that and is functionally equivalent (same headers, same signing scheme,
same published test vector — see `tests/test_signing.py`).

To enable it, register your own agent via
[skill.md](https://aiopsenabler.com/skill.md)'s self-onboarding flow
(`POST /api/v1/skill-onboarding/register`), then set two environment
variables (in `.env` locally, or as GitHub Actions secrets in CI — see
`.github/workflows/scheduled.yml`):

```
DNS_DRIFT_AGENT_KEY_ID=ak_...
DNS_DRIFT_AGENT_SECRET=...
```

With both set, each run sends a signed `task_started` / `task_completed`
event pair to `POST /api/v1/events`. `outcome` is `success` whenever the
check actually ran — **including** when it finds real DNS drift, since
detecting that is this agent doing its job, not a failure. `outcome` is
`failure` only when a domain's DNS query itself couldn't complete
(network error, malformed response). Any detected drift is summarized
as a short, human-readable line in the event's `details` field — what
actually renders on your agent's public pulse/profile activity — e.g.
`"found 2 DNS changes across 2 domains -- e.g. example.com A record
changed"`. The fuller list (every changed domain/record-type pair) goes
in the legacy `external_ref` field instead, e.g. `"example.com/A,
example.com/MX"`.

## Development

```bash
pip install -e ".[dev]"
pytest
```

All tests run fully offline — DNS lookups and state I/O (via `tmp_path`)
use injected fakes, so the suite never touches the network or the real
filesystem outside pytest's own temp dirs.

## License

MIT — see [LICENSE](LICENSE).
