"""Persists the last-seen DNS snapshot per domain, so repeat runs can
diff against a real baseline instead of re-reporting the same records
forever.

Stored as plain JSON: `{"<domain>": {"<record_type>": ["<value>", ...]}}`.
In CI this file is expected to be restored/saved across scheduled runs
via `actions/cache` (see `.github/workflows/scheduled.yml`) -- GitHub
Actions runners are otherwise stateless between runs.
"""

from __future__ import annotations

import json
from pathlib import Path

Snapshot = dict[str, list[str]]
State = dict[str, Snapshot]


def load_state(path: Path) -> State:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def save_state(path: Path, state: State) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2, sort_keys=True), encoding="utf-8")
