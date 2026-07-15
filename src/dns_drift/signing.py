"""Raw HMAC-SHA256 request signing for the AiOps Enabler API, implemented
directly from the platform's own published spec -- no SDK dependency
(the officially documented SDK, `aiops-enabler`, lives in a private
GitHub repo as of this writing and is not installable by the public; see
README "Optional: AiOps Enabler integration").

Spec source: https://aiopsenabler.com/skill.md section 3, identically
restated in https://aiopsenabler.com/api-guide.md section 2. This
module's test vector in tests/test_signing.py reproduces the exact
published test vector.

Signing recipe:
  1. Serialize the JSON body to bytes exactly once; sign and send the
     same bytes.
  2. HMAC key = raw bytes of hex(sha256(secret)) -- hash the secret, then
     decode that hex string back into 32 raw bytes.
  3. Message = f"{timestamp}." (literal dot) + the exact body bytes.
  4. Signature = lowercase hex HMAC-SHA256(key, message).
Headers sent: X-Agent-Key-Id, X-Agent-Timestamp, X-Agent-Signature,
Content-Type: application/json.
"""

from __future__ import annotations

import hashlib
import hmac
import time

KEY_ID_HEADER = "X-Agent-Key-Id"
TIMESTAMP_HEADER = "X-Agent-Timestamp"
SIGNATURE_HEADER = "X-Agent-Signature"


def secret_hash(secret: str) -> str:
    return hashlib.sha256(secret.encode("utf-8")).hexdigest()


def compute_signature(*, secret: str, timestamp: str, body: bytes) -> str:
    key = bytes.fromhex(secret_hash(secret))
    message = f"{timestamp}.".encode("utf-8") + body
    return hmac.new(key, message, hashlib.sha256).hexdigest()


def sign_request(*, key_id: str, secret: str, body: bytes) -> dict[str, str]:
    timestamp = str(int(time.time()))
    signature = compute_signature(secret=secret, timestamp=timestamp, body=body)
    return {
        KEY_ID_HEADER: key_id,
        TIMESTAMP_HEADER: timestamp,
        SIGNATURE_HEADER: signature,
        "Content-Type": "application/json",
    }
