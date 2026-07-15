"""Configuration for dns-drift, sourced from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dns_drift.dns_client import RECORD_TYPES

DEFAULT_DOMAINS = ("aiopsenabler.com", "cyntra360hub.com")
DEFAULT_STATE_FILE = ".state/dns_drift_state.json"
DEFAULT_TIMEOUT_SECONDS = 10.0


@dataclass(frozen=True)
class Config:
    domains: tuple[str, ...] = DEFAULT_DOMAINS
    record_types: tuple[str, ...] = RECORD_TYPES
    state_file: Path = Path(DEFAULT_STATE_FILE)
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS
    report_enabled: bool = False
    agent_key_id: str | None = None
    agent_secret: str | None = None
    base_url: str = "https://api.aiopsenabler.com"


def load_config(env: dict[str, str] | None = None) -> Config:
    """Build a Config from environment variables (or an injected mapping,
    for tests). Reporting is opt-in: it only turns on when both
    DNS_DRIFT_AGENT_KEY_ID and DNS_DRIFT_AGENT_SECRET are set. An
    explicitly empty env var is treated the same as an unset one (see
    the other agents' config.py modules for why -- `dict.get(key,
    default)` alone only falls back when the key is *absent*)."""
    source = env if env is not None else os.environ

    raw_domains = (source.get("DNS_DRIFT_DOMAINS") or "").strip()
    domains = (
        tuple(d.strip() for d in raw_domains.split(",") if d.strip())
        if raw_domains
        else DEFAULT_DOMAINS
    )

    state_file = Path(source.get("DNS_DRIFT_STATE_FILE") or DEFAULT_STATE_FILE)
    timeout_seconds = float(source.get("DNS_DRIFT_TIMEOUT_SECONDS") or DEFAULT_TIMEOUT_SECONDS)

    key_id = source.get("DNS_DRIFT_AGENT_KEY_ID") or None
    secret = source.get("DNS_DRIFT_AGENT_SECRET") or None
    base_url = source.get("DNS_DRIFT_BASE_URL") or "https://api.aiopsenabler.com"

    return Config(
        domains=domains,
        state_file=state_file,
        timeout_seconds=timeout_seconds,
        report_enabled=bool(key_id and secret),
        agent_key_id=key_id,
        agent_secret=secret,
        base_url=base_url,
    )
