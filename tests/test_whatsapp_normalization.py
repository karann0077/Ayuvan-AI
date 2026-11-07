from app.services.whatsapp import normalize_incoming_message


def test_normalizes_interactive_button_reply() -> None:
    message = normalize_incoming_message({
        "id": "wamid.1", "from": "919999999999", "timestamp": "1733500000", "type": "interactive",
        "interactive": {"type": "button_reply", "button_reply": {"id": "FREQUENCY_CONTINUOUS", "title": "Continuously"}},
    })
    assert message.content == "Continuously"
    assert message.metadata["reply_id"] == "FREQUENCY_CONTINUOUS"


def test_normalizes_document_reference_without_reading_media() -> None:
    message = normalize_incoming_message({
        "id": "wamid.2", "from": "919999999999", "type": "document",
        "document": {"id": "media-1", "mime_type": "application/pdf", "filename": "report.pdf"},
    })
    assert message.media_id == "media-1"
    assert message.metadata["filename"] == "report.pdf"
