import hashlib
import hmac


def verify_meta_signature(raw_body: bytes, signature: str | None, app_secret: str | None) -> bool:
    """Verify Meta's X-Hub-Signature-256 header without logging its payload."""
    if not app_secret or not signature:
        return False
    expected = "sha256=" + hmac.new(
        app_secret.encode("utf-8"), raw_body, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)
