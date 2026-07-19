import json
from pathlib import Path

from dns_drift.config import Config
from dns_drift.drift import run_check


def _doh_response(status: int, values: list[str]) -> str:
    return json.dumps({"Status": status, "Answer": [{"data": v} for v in values]})


def _fetcher_for(records: dict[str, list[str]]):
    def fetcher(url: str, timeout: float) -> str:
        for record_type, values in records.items():
            if f"type={record_type}" in url:
                return _doh_response(0, values)
        return _doh_response(0, [])

    return fetcher


def test_first_run_establishes_baseline_no_drift(tmp_path: Path):
    config = Config(
        domains=("example.com",),
        record_types=("A",),
        state_file=tmp_path / "state.json",
    )
    result = run_check(config, fetcher=_fetcher_for({"A": ["1.2.3.4"]}))
    assert result.domains[0].ok
    assert result.domains[0].changes == ()
    assert result.outcome == "success"
    assert result.findings_summary is None


def test_second_run_no_change_reports_no_drift(tmp_path: Path):
    state_file = tmp_path / "state.json"
    config = Config(domains=("example.com",), record_types=("A",), state_file=state_file)

    run_check(config, fetcher=_fetcher_for({"A": ["1.2.3.4"]}))
    second = run_check(config, fetcher=_fetcher_for({"A": ["1.2.3.4"]}))

    assert second.domains[0].changes == ()
    assert second.outcome == "success"


def test_second_run_changed_value_is_drift_and_still_success(tmp_path: Path):
    state_file = tmp_path / "state.json"
    config = Config(domains=("example.com",), record_types=("A",), state_file=state_file)

    run_check(config, fetcher=_fetcher_for({"A": ["1.2.3.4"]}))
    second = run_check(config, fetcher=_fetcher_for({"A": ["5.6.7.8"]}))

    assert len(second.domains[0].changes) == 1
    change = second.domains[0].changes[0]
    assert change.record_type == "A"
    assert change.old_values == ("1.2.3.4",)
    assert change.new_values == ("5.6.7.8",)
    # Detected drift is a successful detection, not a tool failure.
    assert second.outcome == "success"
    assert second.findings_summary == "swept 1 domain(s) -- 1 change(s): example.com/A"


def test_dns_query_error_is_failure(tmp_path: Path):
    config = Config(domains=("example.com",), record_types=("A",), state_file=tmp_path / "state.json")

    def failing_fetcher(url, timeout):
        raise TimeoutError("connection timed out")

    result = run_check(config, fetcher=failing_fetcher)
    assert not result.domains[0].ok
    assert result.has_errors
    assert result.outcome == "failure"


def test_state_persists_across_runs(tmp_path: Path):
    state_file = tmp_path / "state.json"
    config = Config(domains=("example.com",), record_types=("A",), state_file=state_file)
    run_check(config, fetcher=_fetcher_for({"A": ["1.2.3.4"]}))
    assert state_file.exists()
    saved = json.loads(state_file.read_text())
    assert saved["example.com"]["A"] == ["1.2.3.4"]


def test_multiple_domains_are_independent(tmp_path: Path):
    config = Config(
        domains=("a.com", "b.com"), record_types=("A",), state_file=tmp_path / "state.json"
    )

    def fetcher(url, timeout):
        if "a.com" in url:
            return _doh_response(0, ["1.1.1.1"])
        return _doh_response(0, ["2.2.2.2"])

    result = run_check(config, fetcher=fetcher)
    assert len(result.domains) == 2
    assert {d.domain for d in result.domains} == {"a.com", "b.com"}
