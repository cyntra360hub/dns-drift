from pathlib import Path

from dns_drift.config import DEFAULT_DOMAINS, DEFAULT_STATE_FILE, load_config


def test_defaults_when_env_empty():
    config = load_config(env={})
    assert config.domains == DEFAULT_DOMAINS
    assert config.state_file == Path(DEFAULT_STATE_FILE)
    assert config.report_enabled is False


def test_custom_domains_from_env():
    config = load_config(env={"DNS_DRIFT_DOMAINS": "a.com, b.com ,c.com"})
    assert config.domains == ("a.com", "b.com", "c.com")


def test_empty_string_env_vars_fall_back_to_defaults():
    config = load_config(
        env={"DNS_DRIFT_DOMAINS": "", "DNS_DRIFT_STATE_FILE": "", "DNS_DRIFT_TIMEOUT_SECONDS": ""}
    )
    assert config.domains == DEFAULT_DOMAINS
    assert config.state_file == Path(DEFAULT_STATE_FILE)
    assert config.timeout_seconds == 10.0


def test_reporting_enabled_only_when_both_creds_present():
    assert load_config(env={"DNS_DRIFT_AGENT_KEY_ID": "ak_x"}).report_enabled is False
    assert (
        load_config(
            env={"DNS_DRIFT_AGENT_KEY_ID": "ak_x", "DNS_DRIFT_AGENT_SECRET": "s"}
        ).report_enabled
        is True
    )
