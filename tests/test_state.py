from pathlib import Path

from dns_drift.state import load_state, save_state


def test_load_state_missing_file_returns_empty(tmp_path: Path):
    assert load_state(tmp_path / "nope.json") == {}


def test_save_then_load_roundtrips(tmp_path: Path):
    path = tmp_path / "state.json"
    state = {"example.com": {"A": ["1.2.3.4"], "MX": []}}
    save_state(path, state)
    assert load_state(path) == state


def test_save_creates_parent_directories(tmp_path: Path):
    path = tmp_path / "nested" / "dir" / "state.json"
    save_state(path, {"example.com": {"A": ["1.2.3.4"]}})
    assert path.exists()
