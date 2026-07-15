import json

import pytest

from dns_drift.dns_client import fetch_record, snapshot_domain


def _response(status: int, answers: list[dict] | None = None) -> str:
    return json.dumps({"Status": status, "Answer": answers or []})


def test_fetch_record_returns_sorted_values():
    payload = _response(0, [{"data": "10.0.0.2"}, {"data": "10.0.0.1"}])
    values = fetch_record("example.com", "A", fetcher=lambda url, timeout: payload)
    assert values == ["10.0.0.1", "10.0.0.2"]


def test_fetch_record_no_answer_key_is_empty_list():
    payload = json.dumps({"Status": 0})
    values = fetch_record("example.com", "TXT", fetcher=lambda url, timeout: payload)
    assert values == []


def test_fetch_record_nxdomain_status_3_is_empty_list_not_error():
    payload = _response(3)
    values = fetch_record("example.com", "MX", fetcher=lambda url, timeout: payload)
    assert values == []


def test_fetch_record_servfail_status_raises():
    payload = _response(2)
    with pytest.raises(ValueError, match="Status=2"):
        fetch_record("example.com", "A", fetcher=lambda url, timeout: payload)


def test_fetch_record_builds_correct_url():
    seen = {}

    def fetcher(url, timeout):
        seen["url"] = url
        return _response(0)

    fetch_record("example.com", "MX", fetcher=fetcher)
    assert seen["url"] == "https://dns.google/resolve?name=example.com&type=MX"


def test_snapshot_domain_queries_all_record_types():
    calls = []

    def fetcher(url, timeout):
        calls.append(url)
        return _response(0, [{"data": "x"}])

    snapshot = snapshot_domain("example.com", record_types=("A", "MX"), fetcher=fetcher)
    assert snapshot == {"A": ["x"], "MX": ["x"]}
    assert len(calls) == 2
