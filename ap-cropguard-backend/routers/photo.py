"""
AP-CropGuard — Photo Router
=============================
Screen 3 endpoints: photo assessment, VRO feedback,
Bayesian weight history, and evidence log.
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from datetime import datetime, timezone
from typing import Optional
import uuid

from data.mandals import get_mandal
from data.crops import CROP_NAMES
from engines.photo_engine import assess_photo
from engines.fraud_engine import run_full_fraud_check
from engines.bayesian_engine import (
    update_weights,
    compute_consensus_loss,
    get_weight_history,
    get_weights,
)

router = APIRouter(prefix="/photo", tags=["photo"])

# ---------------------------------------------------------------------------
# MODULE-LEVEL STATE
# ---------------------------------------------------------------------------

EVIDENCE_LOG: dict = {}

_VALID_FEEDBACK_TYPES = {
    "DISPUTE_SATELLITE",
    "AGREE_SATELLITE",
    "DISPUTE_PHOTO",
    "AGREE_PHOTO",
}

# ---------------------------------------------------------------------------
# REQUEST MODEL
# ---------------------------------------------------------------------------

class FeedbackRequest(BaseModel):
    mandal_id:     str
    assessment_id: str
    feedback_type: str
    vro_id:        str
    note:          Optional[str] = ""

# ---------------------------------------------------------------------------
# HELPER
# ---------------------------------------------------------------------------

def make_response(data: dict) -> dict:
    return {
        "success":   True,
        "data":      data,
        "error":     None,
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


def _validate_mandal(mandal_id: str) -> dict:
    try:
        return get_mandal(mandal_id)
    except ValueError:
        raise HTTPException(
            status_code=404,
            detail=f"Mandal '{mandal_id}' not found. Valid IDs: KNL_001 to KNL_027",
        )

# ---------------------------------------------------------------------------
# ENDPOINTS
# ---------------------------------------------------------------------------

@router.post("/assess")
async def post_photo_assess(
    image:                  UploadFile = File(...),
    claimed_mandal_id:      str        = Form(...),
    claimed_crop:           str        = Form(...),
    claimed_disaster_date:  str        = Form(...),
):
    """
    Accept a crop photo upload, run Gemini/Groq vision assessment,
    fraud checks, and Bayesian consensus scoring.
    Stores the result in the in-memory evidence log.
    """
    mandal = _validate_mandal(claimed_mandal_id)

    if claimed_crop not in CROP_NAMES:
        raise HTTPException(
            status_code=400,
            detail=f"Crop '{claimed_crop}' not recognised. Valid crops: {CROP_NAMES}",
        )

    image_bytes = await image.read()

    # Vision assessment (Gemini → Groq → rule-based fallback)
    assessment = assess_photo(image_bytes, claimed_crop)

    # Fraud check (EXIF + geofence + timestamp + edit signature)
    fraud_check = run_full_fraud_check(
        image_bytes, claimed_mandal_id, claimed_disaster_date
    )

    # Photo loss — conservative if fraud flagged
    if fraud_check["overall_status"] == "CLEAN":
        photo_loss = float(assessment.get("estimated_photo_loss_pct", 45.0))
    else:
        photo_loss = 45.0

    # Bayesian consensus
    satellite_loss = 55.0  # Default — replaced by real value from district endpoint
    consensus = compute_consensus_loss(
        claimed_mandal_id, satellite_loss, photo_loss
    )

    # Generate unique assessment ID
    date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
    assessment_id = f"ASS_{date_str}_{uuid.uuid4().hex[:6].upper()}"

    # Store in evidence log
    if claimed_mandal_id not in EVIDENCE_LOG:
        EVIDENCE_LOG[claimed_mandal_id] = []

    EVIDENCE_LOG[claimed_mandal_id].append({
        "submission_id":           assessment_id,
        "submitted_by":            "VRO_FIELD",
        "submitted_at":            datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "crop":                    claimed_crop,
        "damage_class":            assessment.get("damage_class", "Unknown"),
        "photo_loss_pct":          photo_loss,
        "fraud_status":            fraud_check["overall_status"],
        "vro_feedback":            None,
        "final_consensus_loss_pct": consensus["final_loss_pct"],
        "analysis_source":         assessment.get("analysis_source", "Unknown"),
    })

    return make_response({
        "assessment_id":   assessment_id,
        "assessment":      assessment,
        "fraud_check":     fraud_check,
        "consensus":       consensus,
        "evidence_stored": True,
    })


@router.post("/feedback")
def post_photo_feedback(req: FeedbackRequest):
    """
    Record VRO feedback on a photo assessment and update Bayesian weights.
    Feedback type controls whether satellite or photo weight increases.
    """
    if req.feedback_type not in _VALID_FEEDBACK_TYPES:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Invalid feedback_type '{req.feedback_type}'. "
                f"Valid values: {sorted(_VALID_FEEDBACK_TYPES)}"
            ),
        )

    _validate_mandal(req.mandal_id)

    weight_result = update_weights(
        req.mandal_id,
        req.feedback_type,
        req.vro_id,
        req.note,
    )

    # Update evidence log entry if assessment_id matches
    for entry in EVIDENCE_LOG.get(req.mandal_id, []):
        if entry["submission_id"] == req.assessment_id:
            entry["vro_feedback"] = req.feedback_type
            break

    return make_response(weight_result)


@router.get("/weight-history")
def get_photo_weight_history(mandal_id: str):
    """Return full Bayesian weight update history for a mandal."""
    mandal = _validate_mandal(mandal_id)

    history = get_weight_history(mandal_id)
    history["mandal_name"] = mandal["mandal_name"]

    return make_response(history)


@router.get("/evidence-log")
def get_evidence_log(mandal_id: str, season: str):
    """Return all photo assessment submissions for a mandal in a season."""
    mandal = _validate_mandal(mandal_id)

    entries = EVIDENCE_LOG.get(mandal_id, [])

    return make_response({
        "mandal_id":         mandal_id,
        "mandal_name":       mandal["mandal_name"],
        "season":            season,
        "total_submissions": len(entries),
        "evidence":          entries,
    })
