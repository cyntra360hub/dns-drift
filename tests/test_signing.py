from dns_drift.signing import compute_signature, secret_hash, sign_request

# Test vector published in both https://aiopsenabler.com/skill.md (section 3.3)
# and https://aiopsenabler.com/api-guide.md (section 2), byte-for-byte identical
# in both documents.
SECRET = "correct-horse-battery-staple-test-secret"
KEY_ID = "ak_test_1234567890abcdef"
TIMESTAMP = "1700000000"
BODY = b'{"event_type":"task_started","task_id":"demo-task-1"}'
EXPECTED_SECRET_HASH = "285beb7adbdb73adc3d35e65fe7d2a4b958f1e12d790e39c82703e29743034c6"
EXPECTED_SIGNATURE = "ea3906dd25d6ff6edd668e64634f1e10698a7b9b31d5160fa1a28951102e62e9"


def test_secret_hash_matches_published_vector():
    assert secret_hash(SECRET) == EXPECTED_SECRET_HASH


def test_signature_matches_published_vector():
    sig = compute_signature(secret=SECRET, timestamp=TIMESTAMP, body=BODY)
    assert sig == EXPECTED_SIGNATURE


def test_sign_request_includes_all_required_headers():
    headers = sign_request(key_id=KEY_ID, secret=SECRET, body=BODY)
    assert headers["X-Agent-Key-Id"] == KEY_ID
    assert headers["X-Agent-Signature"]
    assert headers["X-Agent-Timestamp"].isdigit()
    assert headers["Content-Type"] == "application/json"
