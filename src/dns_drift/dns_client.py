"""DNS record lookups via Google's public DNS-over-HTTPS JSON API
(https://developers.google.com/speed/public-dns/docs/doh/json) -- free,
no API key, no auth, plain HTTPS GET returning JSON, so no third-party
DNS library is needed.
"""

from __future__ import annotations

import json
import urllib.request
from collections.abc import Callable

RECORD_TYPES: tuple[str, ...] = ("A", "AAAA", "MX", "NS", "TXT")

DOH_URL_TEMPLATE = "https://dns.google/resolve?name={name}&type={type}"

# DNS response codes (RFC 1035 section 4.1.1) that mean "the query itself
# succeeded" -- 0 (NOERROR, records may or may not be present) and
# 3 (NXDOMAIN, treated as "no records of this type" rather than an error,
# since we're checking specific record sets, not asserting the domain's
# overall existence). Anything else (SERVFAIL, REFUSED, ...) is a real
# lookup failure.
_OK_STATUSES = (0, 3)

Fetcher = Callable[[str, float], str]


def fetch_doh(url: str, timeout: float) -> str:
    """Real HTTP GET against dns.google. The default `fetcher` --
    swapped out entirely in tests, so no live network call happens in
    the test suite."""
    request = urllib.request.Request(url, headers={"Accept": "application/dns-json"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read().decode("utf-8")


def fetch_record(
    domain: str, record_type: str, timeout: float = 10.0, fetcher: Fetcher = fetch_doh
) -> list[str]:
    """Return the sorted list of record values for `domain`/`record_type`,
    or an empty list if none exist. Raises if the query itself fails."""
    url = DOH_URL_TEMPLATE.format(name=domain, type=record_type)
    raw = fetcher(url, timeout)
    data = json.loads(raw)
    status = data.get("Status")
    if status not in _OK_STATUSES:
        raise ValueError(f"DNS query for {domain} {record_type} failed with Status={status}")
    values = [answer["data"] for answer in data.get("Answer", [])]
    return sorted(values)


def snapshot_domain(
    domain: str,
    record_types: tuple[str, ...] = RECORD_TYPES,
    timeout: float = 10.0,
    fetcher: Fetcher = fetch_doh,
) -> dict[str, list[str]]:
    """Query every configured record type for `domain`, returning
    `{record_type: [values]}`. Raises on the first record type whose
    query fails (the caller decides how to handle that)."""
    return {
        record_type: fetch_record(domain, record_type, timeout=timeout, fetcher=fetcher)
        for record_type in record_types
    }
