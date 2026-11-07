"""Versioned Meta WhatsApp Flow definitions and lifecycle helpers.

The Flow is a controlled form. Its fields and visible choices are reviewed product content;
Gemini never writes this JSON or decides which answer is clinically important.
"""

import json
from typing import Any

import httpx

from app.core.config import Settings


SYMPTOM_INTAKE_FLOW_NAME = "AYUVAN Symptom Intake v1"
SYMPTOM_INTAKE_FLOW_SCREEN = "SYMPTOM_INTAKE"


def symptom_intake_flow_definition() -> dict[str, Any]:
    """Return a compact static Flow which completes into the normal WhatsApp webhook."""
    return {
        "version": "6.3",
        "screens": [{
            "id": SYMPTOM_INTAKE_FLOW_SCREEN,
            "title": "Symptom update",
            "terminal": True,
            "success": True,
            "data": {},
            "layout": {
                "type": "SingleColumnLayout",
                "children": [{
                    "type": "Form",
                    "name": "intake_form",
                    "children": [
                        {"type": "TextHeading", "text": "A few quick details"},
                        {
                            "type": "TextBody",
                            "text": "Your answers help AYUVAN keep an accurate record. This does not diagnose a condition.",
                        },
                        {
                            "type": "RadioButtonsGroup", "name": "onset", "required": True,
                            "label": "When did this begin?",
                            "data-source": [
                                {"id": "today", "title": "Today"},
                                {"id": "one_to_three_days", "title": "1–3 days ago"},
                                {"id": "four_to_seven_days", "title": "4–7 days ago"},
                                {"id": "more_than_one_week", "title": "More than one week ago"},
                                {"id": "not_sure", "title": "Not sure"},
                            ],
                        },
                        {
                            "type": "RadioButtonsGroup", "name": "severity", "required": True,
                            "label": "How severe is it right now?",
                            "data-source": [
                                {"id": "mild", "title": "Mild"},
                                {"id": "moderate", "title": "Moderate"},
                                {"id": "severe", "title": "Severe"},
                                {"id": "not_sure", "title": "Not sure"},
                            ],
                        },
                        {
                            "type": "RadioButtonsGroup", "name": "progression", "required": True,
                            "label": "Since it began, is it changing?",
                            "data-source": [
                                {"id": "improving", "title": "Improving"},
                                {"id": "about_the_same", "title": "About the same"},
                                {"id": "getting_worse", "title": "Getting worse"},
                                {"id": "not_sure", "title": "Not sure"},
                            ],
                        },
                        {
                            "type": "CheckboxGroup", "name": "associated_symptoms", "required": False,
                            "label": "Any other symptoms? Select all that apply.",
                            "data-source": [
                                {"id": "nausea_or_vomiting", "title": "Nausea or vomiting"},
                                {"id": "dizziness", "title": "Dizziness"},
                                {"id": "vision_change", "title": "Vision change"},
                                {"id": "weakness_or_numbness", "title": "Weakness or numbness"},
                                {"id": "fever_or_stiff_neck", "title": "Fever or stiff neck"},
                                {"id": "none", "title": "None of these"},
                            ],
                        },
                        {
                            "type": "RadioButtonsGroup", "name": "functional_impact", "required": True,
                            "label": "Can you manage your usual activities?",
                            "data-source": [
                                {"id": "mostly_manageable", "title": "Yes, mostly"},
                                {"id": "some_activities_difficult", "title": "Some are difficult"},
                                {"id": "hard_to_carry_on", "title": "Hard to carry on normally"},
                                {"id": "not_sure", "title": "Not sure"},
                            ],
                        },
                        {
                            "type": "Footer", "label": "Submit update",
                            "on-click-action": {
                                "name": "complete",
                                "payload": {
                                    "onset": "${form.onset}",
                                    "severity": "${form.severity}",
                                    "progression": "${form.progression}",
                                    "associated_symptoms": "${form.associated_symptoms}",
                                    "functional_impact": "${form.functional_impact}",
                                },
                            },
                        },
                    ],
                }],
            },
        }],
    }


class MetaFlowClient:
    """Small, explicit lifecycle client for creating one versioned static Flow."""

    def __init__(self, settings: Settings) -> None:
        if not settings.whatsapp_business_account_id or not settings.whatsapp_access_token:
            raise ValueError("WhatsApp Business Account ID and access token are required")
        self.settings = settings
        self.headers = {"Authorization": f"Bearer {settings.whatsapp_access_token.get_secret_value()}"}
        self.base_url = f"https://graph.facebook.com/{settings.graph_api_version}"

    async def create_upload_and_publish_symptom_intake(self) -> str:
        async with httpx.AsyncClient(timeout=30) as client:
            create = await client.post(
                f"{self.base_url}/{self.settings.whatsapp_business_account_id}/flows",
                headers=self.headers,
                data={"name": SYMPTOM_INTAKE_FLOW_NAME, "categories": json.dumps(["SURVEY"])} ,
            )
            create.raise_for_status()
            flow_id = create.json()["id"]
            upload = await client.post(
                f"{self.base_url}/{flow_id}/assets",
                headers=self.headers,
                data={"name": "flow.json", "asset_type": "FLOW_JSON"},
                files={"file": ("flow.json", json.dumps(symptom_intake_flow_definition()), "application/json")},
            )
            upload.raise_for_status()
            publish = await client.post(f"{self.base_url}/{flow_id}/publish", headers=self.headers)
            publish.raise_for_status()
        return flow_id
