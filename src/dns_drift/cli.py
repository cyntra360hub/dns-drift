"""dns-drift command-line entry point."""

from __future__ import annotations

import sys
import time

from dns_drift.config import load_config
from dns_drift.drift import DriftResult, run_check
from dns_drift.reporting import report_run


def _print_report(result: DriftResult) -> None:
    for check in result.domains:
        if not check.ok:
            print(f"[ERROR] {check.domain}: {check.error}")
            continue
        if not check.changes:
            print(f"[OK] {check.domain}: no drift")
            continue
        print(f"[DRIFT] {check.domain}:")
        for change in check.changes:
            print(f"    {change.record_type}: {list(change.old_values)} -> {list(change.new_values)}")
    print()
    print(f"Overall: outcome={result.outcome}")


def main() -> int:
    run_started = time.monotonic()
    config = load_config()
    result = run_check(config)
    _print_report(result)

    if config.report_enabled:
        try:
            report_run(config, result, run_started=run_started)
            print("Reported run to AiOps Enabler.")
        except Exception as exc:  # noqa: BLE001
            print(f"AiOps Enabler reporting failed (non-fatal): {exc}", file=sys.stderr)
    else:
        print("AiOps Enabler reporting disabled (no credentials configured).")

    return 1 if result.has_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
