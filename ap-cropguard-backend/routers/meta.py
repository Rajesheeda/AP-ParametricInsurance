"""
AP-CropGuard — Meta Router
===========================
Static reference data endpoints: crops, mandals,
disaster history, and system health check.
"""

from fastapi import APIRouter, HTTPException
from datetime import datetime, timezone

from data.crops import CROPS, CROP_NAMES, PERILS, THRESHOLD_LOSS_PCT
from data.mandals import get_all_mandals, get_mandal
from data.historical import get_disaster_history

router = APIRouter(prefix="/meta", tags=["meta"])

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

# ---------------------------------------------------------------------------
# ENDPOINTS
# ---------------------------------------------------------------------------

@router.get("/crops")
def get_crops():
    """Return full crop master data for all 5 Kurnool Kharif crops."""
    return make_response({
        "crops":              list(CROPS.values()),
        "crop_names":         CROP_NAMES,
        "perils":             PERILS,
        "threshold_loss_pct": THRESHOLD_LOSS_PCT,
        "total_crops":        len(CROPS),
    })


@router.get("/crops/{crop_name}")
def get_crop_by_name(crop_name: str):
    """Return data for a single crop by name."""
    if crop_name not in CROPS:
        raise HTTPException(
            status_code=404,
            detail=f"Crop '{crop_name}' not found. Valid crops: {CROP_NAMES}",
        )
    return make_response(CROPS[crop_name])


@router.get("/mandals")
def get_mandals():
    """Return all 27 Kurnool mandals with district summary counts."""
    mandals = get_all_mandals()
    drought_prone_count = sum(1 for m in mandals if m.get("drought_prone", False))
    flood_prone_count   = sum(1 for m in mandals if m.get("flood_prone", False))

    return make_response({
        "district":           "Kurnool",
        "total_mandals":      len(mandals),
        "mandals":            mandals,
        "drought_prone_count": drought_prone_count,
        "flood_prone_count":   flood_prone_count,
    })


@router.get("/mandals/{mandal_id}")
def get_mandal_by_id(mandal_id: str):
    """Return data for a single mandal by ID."""
    try:
        mandal = get_mandal(mandal_id)
    except (KeyError, ValueError):
        raise HTTPException(
            status_code=404,
            detail=f"Mandal '{mandal_id}' not found.",
        )
    return make_response(mandal)


@router.get("/disaster-history")
def get_disaster_history_endpoint():
    """Return Kurnool historical disaster event timeline."""
    events = get_disaster_history()
    return make_response({
        "district":     "Kurnool",
        "total_events": len(events),
        "events":       events,
    })


@router.get("/health")
def health_check():
    """System health check — confirms all engines and data are loaded."""
    mandals = get_all_mandals()
    return make_response({
        "status":         "operational",
        "version":        "1.0.0",
        "district":       "Kurnool",
        "crops_loaded":   len(CROPS),
        "mandals_loaded": len(mandals),
        "engines": [
            "spi_engine",
            "vci_engine",
            "actuarial_engine",
            "backtest_engine",
            "bayesian_engine",
            "photo_engine",
            "fraud_engine",
        ],
    })
