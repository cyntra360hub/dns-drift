"""Orchestrates a single check cycle: snapshot each configured domain's
DNS records, diff against the persisted state to find genuine changes,
then update the state file.

Cold-start note: on the very first run for a given domain (no prior
snapshot in the state file), nothing is reported as "drift" -- there's
no baseline yet, just an initial observation. This is different from
status-watch's incident-diffing (where a first-run flood of "new"
incidents is meaningful): a DNS record simply *existing* on day one
isn't drift, so establishing the baseline silently is the correct
behavior here, not a corner case to work around.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from dns_drift.config import Config
from dns_drift.dns_client import Fetcher, fetch_doh, snapshot_domain
from dns_drift.state import load_state, save_state


def _pluralize(n: int, singular: str, plural: str | None = None) -> str:
    return f"{n} {singular if n == 1 else (plural or singular + 's')}"


@dataclass(frozen=True)
class DriftChange:
    domain: str
    record_type: str
    old_values: tuple[str, ...]
    new_values: tuple[str, ...]


@dataclass(frozen=True)
class DomainCheck:
    domain: str
    ok: bool
    error: str | None
    changes: tuple[DriftChange, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class DriftResult:
    domains: tuple[DomainCheck, ...]

    @property
    def all_changes(self) -> tuple[DriftChange, ...]:
        return tuple(c for d in self.domains for c in d.changes)

    @property
    def has_errors(self) -> bool:
        """True only when a domain's DNS query itself failed -- as
        opposed to a successful query that found real drift, which is
        this agent doing its job."""
        return any(not d.ok for d in self.domains)

    @property
    def findings_summary(self) -> str | None:
        """A short, human-readable findings summary for the AiOps
        Enabler event's `details` field -- what actually renders on the
        agent's public pulse/profile activity. Names only a single
        example change plus a count, rather than every changed record.
        None when nothing changed."""
        changes = self.all_changes
        if not changes:
            return None
        example = changes[0]
        change_word = _pluralize(len(changes), "DNS change")
        domain_word = _pluralize(len(self.domains), "domain")
        return (
            f"found {change_word} across {domain_word} -- e.g. "
            f"{example.domain} {example.record_type} record changed"
        )[:500]

    @property
    def technical_summary(self) -> str | None:
        """The fuller list (every changed domain/record-type pair) for
        the event's legacy `external_ref` field."""
        changes = self.all_changes
        if not changes:
            return None
        parts = [f"{c.domain}/{c.record_type}" for c in changes]
        return ", ".join(parts)[:255]

    @property
    def outcome(self) -> str:
        """Maps to the AiOps Enabler `task_completed` outcome enum
        (success | failure). `failure` is reserved for a domain's DNS
        query itself erroring out (see `has_errors`); a completed check
        that *found* real drift is still `success` -- detection is this
        agent doing its job, and the findings are reported via
        `external_ref` (see `findings_summary`), not via a non-success
        outcome."""
        return "failure" if self.has_errors else "success"


def run_check(config: Config, fetcher: Fetcher = fetch_doh) -> DriftResult:
    state = load_state(config.state_file)
    domain_checks: list[DomainCheck] = []

    for domain in config.domains:
        try:
            new_snapshot = snapshot_domain(
                domain, config.record_types, timeout=config.timeout_seconds, fetcher=fetcher
            )
        except Exception as exc:  # noqa: BLE001 - any fetch/parse failure is a domain error
            domain_checks.append(DomainCheck(domain=domain, ok=False, error=str(exc)))
            continue

        old_snapshot = state.get(domain)
        changes: list[DriftChange] = []
        if old_snapshot is not None:
            for record_type in config.record_types:
                old_values = tuple(old_snapshot.get(record_type, []))
                new_values = tuple(new_snapshot.get(record_type, []))
                if old_values != new_values:
                    changes.append(
                        DriftChange(
                            domain=domain,
                            record_type=record_type,
                            old_values=old_values,
                            new_values=new_values,
                        )
                    )

        state[domain] = new_snapshot
        domain_checks.append(
            DomainCheck(domain=domain, ok=True, error=None, changes=tuple(changes))
        )

    save_state(config.state_file, state)
    return DriftResult(domains=tuple(domain_checks))
