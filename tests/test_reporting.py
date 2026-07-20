import json

from dns_drift.config import Config
from dns_drift.drift import DomainCheck, DriftChange, DriftResult
from dns_drift.reporting import ReportingError, report_run


def _result(changes=(), errors=False) -> DriftResult:
    if errors:
        check = DomainCheck(domain="example.com", ok=False, error="boom")
    else:
        check = DomainCheck(domain="example.com", ok=True, error=None, changes=changes)
    return DriftResult(domains=(check,))


class _FakePoster:
    def __init__(self):
        self.calls = []

    def __call__(self, url, body, headers):
        self.calls.append((url, body, headers))
        return {"id": "evt_123"}


def test_report_disabled_returns_none():
    poster = _FakePoster()
    config = Config(report_enabled=False)
    assert report_run(config, _result(), poster=poster) is None
    assert poster.calls == []


def test_report_enabled_sends_started_then_completed():
    poster = _FakePoster()
    config = Config(report_enabled=True, agent_key_id="ak_test", agent_secret="s3cret")
    response = report_run(config, _result(), poster=poster)
    assert response == {"id": "evt_123"}
    kinds = [json.loads(c[1])["event_type"] for c in poster.calls]
    assert kinds == ["task_started", "task_completed"]


def test_drift_found_is_success_with_details_and_external_ref():
    poster = _FakePoster()
    config = Config(report_enabled=True, agent_key_id="ak_test", agent_secret="s3cret")
    change = DriftChange(domain="example.com", record_type="A", old_values=("1.1.1.1",), new_values=("2.2.2.2",))
    report_run(config, _result(changes=(change,)), poster=poster)
    second_body = json.loads(poster.calls[1][1])
    assert second_body["outcome"] == "success"
    assert second_body["details"] == "found 1 DNS change across 1 domain -- e.g. example.com A record changed"
    assert second_body["external_ref"] == "example.com/A"


def test_query_error_is_failure_without_external_ref():
    poster = _FakePoster()
    config = Config(report_enabled=True, agent_key_id="ak_test", agent_secret="s3cret")
    report_run(config, _result(errors=True), poster=poster)
    second_body = json.loads(poster.calls[1][1])
    assert second_body["outcome"] == "failure"
    assert "external_ref" not in second_body


def test_reporting_error_carries_status_and_detail():
    err = ReportingError(422, '{"detail": "bad request"}')
    assert err.status_code == 422
    assert "bad request" in err.detail


def test_duration_ms_is_never_zero():
    poster = _FakePoster()
    config = Config(report_enabled=True, agent_key_id="ak_test", agent_secret="s3cret")
    report_run(config, _result(), poster=poster)
    second_body = json.loads(poster.calls[1][1])
    assert isinstance(second_body["duration_ms"], int)
    assert second_body["duration_ms"] >= 1


def test_duration_ms_reflects_real_elapsed_run_time():
    import time

    poster = _FakePoster()
    config = Config(report_enabled=True, agent_key_id="ak_test", agent_secret="s3cret")
    run_started = time.monotonic() - 2.5
    report_run(config, _result(), poster=poster, run_started=run_started)
    second_body = json.loads(poster.calls[1][1])
    assert second_body["duration_ms"] >= 2500
