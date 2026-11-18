import hashlib
import hmac

from google.auth.transport.requests import Request as GoogleRequest
from google.oauth2 import id_token


def verify_meta_signature(raw_body: bytes, signature: str | None, app_secret: str | None) -> bool:
    """Verify Meta's X-Hub-Signature-256 header without logging its payload."""
    if not app_secret or not signature:
        return False
    expected = "sha256=" + hmac.new(
        app_secret.encode("utf-8"), raw_body, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


def verify_cloud_task_identity(token: str, audience: str, email: str) -> bool:
    """Authenticate a task's Google-issued OIDC token and dedicated sender identity."""
    claims = id_token.verify_oauth2_token(token, GoogleRequest(), audience=audience)
    return claims.get("email") == email and claims.get("email_verified") is True
