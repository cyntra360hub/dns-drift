"""dns-drift: watches domains for DNS record changes (A/AAAA/MX/NS/TXT)
and reports drift between runs."""

from dns_drift.drift import DriftResult, run_check

__all__ = ["DriftResult", "run_check"]
__version__ = "0.1.0"
