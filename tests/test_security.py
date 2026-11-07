import hashlib
import hmac

from app.core.security import verify_meta_signature


def test_meta_signature_verification() -> None:
    body = b'{"object":"whatsapp_business_account"}'
    secret = "test-secret"
    signature = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    assert verify_meta_signature(body, signature, secret) is True
    assert verify_meta_signature(body, None, "test-secret") is False
