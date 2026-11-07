import asyncio

import httpx
import pytest

from app.core.config import Settings
from app.services.whatsapp import WhatsAppClient, WhatsAppSendError


def test_expired_token_error_retains_codes_without_secrets(monkeypatch):
    async def rejected_post(self, url, **kwargs):
        return httpx.Response(
            401,
            json={"error": {"code": 190, "error_subcode": 463, "message": "private provider detail"}},
            request=httpx.Request("POST", url),
        )

    monkeypatch.setattr(httpx.AsyncClient, "post", rejected_post)
    client = WhatsAppClient(Settings(
        _env_file=None, whatsapp_phone_number_id="test-phone-id", whatsapp_access_token="test-secret",
    ))
    with pytest.raises(WhatsAppSendError) as error:
        asyncio.run(client.send_text("test-recipient", "private patient content"))
    assert error.value.details["reason"] == "access_token_expired"
    assert error.value.details["code"] == 190
    assert "test-secret" not in str(error.value)
    assert "private" not in str(error.value)
