"""Developer access to the unapproved pathway library.

No draft pathway output is available through a patient-facing assessment route.
The simulator requires an explicit local/test opt-in and a separate shared secret.
"""

from hmac import compare_digest

from fastapi import APIRouter, Depends, Header, HTTPException, status

from app.clinical.coverage import build_coverage_report
from app.clinical.engine import assess
from app.clinical.loader import ROOT, registry
from app.clinical.types import AssessmentInput, AssessmentOutput
from app.core.config import Settings, get_settings

router = APIRouter(tags=["pathway engineering"])


@router.get("/pathways")
def list_pathways() -> list[dict]:
    """Read-only release metadata; no patient data or claimed clinical approval."""
    return [
        {
            "id": pathway_id,
            "versions": [
                {"version": entry.version, "status": entry.status}
                for entry in sorted(versions.values(), key=lambda item: item.version)
            ],
        }
        for pathway_id, versions in sorted(registry().by_id.items())
    ]


@router.get("/coverage")
def coverage() -> dict:
    return build_coverage_report(ROOT)


@router.post("/simulate", response_model=AssessmentOutput)
def simulate(
    request: AssessmentInput,
    simulation_key: str | None = Header(default=None, alias="X-Ayuvan-Simulation-Key"),
    settings: Settings = Depends(get_settings),
) -> AssessmentOutput:
    configured = settings.pathway_simulation_key
    secret = configured.get_secret_value() if configured else ""
    if (
        settings.environment not in {"development", "test"}
        or not settings.enable_pathway_simulator
        or len(secret) < 32
        or simulation_key is None
        or not compare_digest(simulation_key, secret)
    ):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Pathway simulator unavailable")
    return assess(registry(), request, include_drafts=True)


@router.post("/assess")
def assess_patient() -> None:
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Patient-facing pathway assessment is disabled pending clinical approval and validation",
    )
