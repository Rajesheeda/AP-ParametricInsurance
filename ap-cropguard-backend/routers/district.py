"""
AP-CropGuard — District Router
================================
Screen 1 endpoints: district overview, mandal map data,
satellite timeseries, and 72-hour pipeline status.
"""

from fastapi import APIRouter, HTTPException, Query
from datetime import datetime, timezone

from data.mandals import get_all_mandals, get_mandal
from data.historical import get_ndvi_timeseries, get_disaster_history
from engines.vci_engine import (
    compute_vci,
    classify_vci,
    compute_ndvi_anomaly,
    estimate_satellite_loss,
    check_flood_indicator,
)
from engines.spi_engine import classify_spi

router = APIRouter(prefix="/district", tags=["district"])

# ---------------------------------------------------------------------------
# CONSTANTS
# ---------------------------------------------------------------------------

_DISTRICT_SPI = {"Kharif_2023": -1.87, "Kharif_2020": 0.31}
_DOMINANT_PERIL = {"Kharif_2023": "Drought", "Kharif_2020": "None"}

# Per-zone SPI proxies for mandal-level variation
_ZONE_SPI_2023 = {
    "Northern": -1.95,
    "Western":  -1.80,
    "Southern": -1.75,
    "Eastern":  -1.55,
    "Central":  -1.60,
}
_ZONE_SPI_2020 = {
    "Northern": 0.28,
    "Western":  0.35,
    "Southern": 0.25,
    "Eastern":  0.42,
    "Central":  0.38,
}

_PIPELINE_STAGES_2023 = [
    {
        "stage_id": 1,
        "label": "Event Detected",
        "description": "SPI threshold breached — district drought alert triggered",
        "completed_at": "2023-09-12T06:00:00Z",
        "hours_from_event": 0,
        "status": "COMPLETE",
    },
    {
        "stage_id": 2,
        "label": "Satellite Analysis",
        "description": "NDVI/VCI computed for all 27 mandals via MODIS MOD13Q1",
        "completed_at": "2023-09-13T06:00:00Z",
        "hours_from_event": 24,
        "status": "COMPLETE",
    },
    {
        "stage_id": 3,
        "label": "Damage Assessment",
        "description": "Parametric triggers evaluated, crop loss % calculated per mandal",
        "completed_at": "2023-09-13T18:00:00Z",
        "hours_from_event": 36,
        "status": "COMPLETE",
    },
    {
        "stage_id": 4,
        "label": "Ground Verification Dispatch",
        "description": "Photo validation requests dispatched to 24 mandal VROs",
        "completed_at": "2023-09-14T06:00:00Z",
        "hours_from_event": 48,
        "status": "COMPLETE",
    },
    {
        "stage_id": 5,
        "label": "Relief Order Approved",
        "description": "Final compensation order generated and submitted to AP Finance Dept",
        "completed_at": "2023-09-14T18:00:00Z",
        "hours_from_event": 60,
        "status": "COMPLETE",
    },
]

_PIPELINE_STAGES_2020 = [
    {
        "stage_id": 1,
        "label": "Season Monitoring Start",
        "description": "Routine Kharif season NDVI monitoring initiated",
        "completed_at": "2020-07-01T06:00:00Z",
        "hours_from_event": 0,
        "status": "COMPLETE",
    },
    {
        "stage_id": 2,
        "label": "Satellite Analysis",
        "description": "NDVI/VCI computed — all mandals within normal range",
        "completed_at": "2020-07-02T06:00:00Z",
        "hours_from_event": 24,
        "status": "COMPLETE",
    },
    {
        "stage_id": 3,
        "label": "Damage Assessment",
        "description": "Parametric triggers evaluated — no threshold breaches detected",
        "completed_at": "2020-07-02T18:00:00Z",
        "hours_from_event": 36,
        "status": "COMPLETE",
    },
    {
        "stage_id": 4,
        "label": "Ground Verification",
        "description": "Spot checks conducted — confirmed healthy season baseline",
        "completed_at": "2020-07-03T06:00:00Z",
        "hours_from_event": 48,
        "status": "COMPLETE",
    },
    {
        "stage_id": 5,
        "label": "Season Cleared",
        "description": "No relief required — season marked as normal baseline",
        "completed_at": "2020-07-03T12:00:00Z",
        "hours_from_event": 54,
        "status": "COMPLETE",
    },
]

# Synthetic rainfall series (mm) aligned to 18-week season timeseries
_RAINFALL_2023 = [38, 42, 18, 12, 22, 28, 15, 10, 8, 20, 25, 18, 12, 10, 8, 7, 6, 8]
_RAINFALL_2020 = [82, 108, 95, 118, 138, 92, 85, 78, 52, 88, 102, 95, 78, 65, 55, 48, 42, 38]

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


def _validate_season(season: str):
    valid = ("Kharif_2020", "Kharif_2023")
    if season not in valid:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid season '{season}'. Valid values: {valid}",
        )

# ---------------------------------------------------------------------------
# ENDPOINTS
# ---------------------------------------------------------------------------

@router.get("/overview")
def get_district_overview(season: str = Query(...)):
    """District-level aggregated overview for a Kharif season."""
    _validate_season(season)

    mandals = get_all_mandals()
    total_area_ha = sum(m["area_ha"] for m in mandals)
    affected_area_ha = 0
    mandals_affected = 0
    mandals_above_threshold = 0

    for mandal in mandals:
        try:
            ts = get_ndvi_timeseries(mandal["mandal_id"], season)
            series = ts["timeseries"]
            ndvi_values = [w["ndvi"] for w in series]
            ndvi_current = ndvi_values[-1]
            ndvi_5yr_min = ts.get("ndvi_5yr_min", 0.15)
            ndvi_5yr_max = ts.get("ndvi_5yr_max", 0.82)

            vci = compute_vci(ndvi_current, ndvi_5yr_min, ndvi_5yr_max)
            baseline_mean = ts["timeseries"][-1]["baseline_mean"]
            anomaly = compute_ndvi_anomaly(ndvi_current, baseline_mean)
            sat_loss = estimate_satellite_loss(vci, anomaly)

            if vci < 60.0:
                mandals_affected += 1
                affected_area_ha += mandal["area_ha"]
            if sat_loss > 43.0:
                mandals_above_threshold += 1
        except Exception:
            continue

    district_spi = _DISTRICT_SPI.get(season, 0.0)
    spi_class = classify_spi(district_spi)

    return make_response({
        "district":                   "Kurnool",
        "season":                     season,
        "total_mandals":              len(mandals),
        "mandals_affected":           mandals_affected,
        "mandals_above_threshold":    mandals_above_threshold,
        "total_area_ha":              total_area_ha,
        "total_affected_area_ha":     affected_area_ha,
        "dominant_peril":             _DOMINANT_PERIL.get(season, "None"),
        "assessment_status":          "COMPLETE",
        "assessment_completed_hours": 58,
        "spi_district_average":       district_spi,
        "alert_level":                spi_class["category"],
    })


@router.get("/mandals")
def get_district_mandals(season: str = Query(...)):
    """Per-mandal VCI, SPI, loss estimate and threshold status for map rendering."""
    _validate_season(season)

    mandals = get_all_mandals()
    zone_spi_map = _ZONE_SPI_2023 if season == "Kharif_2023" else _ZONE_SPI_2020

    result = []
    for mandal in mandals:
        try:
            ts = get_ndvi_timeseries(mandal["mandal_id"], season)
            series = ts["timeseries"]
            ndvi_values  = [w["ndvi"] for w in series]
            ndvi_current = ndvi_values[-1]
            ndvi_5yr_min  = ts.get("ndvi_5yr_min", 0.15)
            ndvi_5yr_max  = ts.get("ndvi_5yr_max", 0.82)
            baseline_mean = series[-1]["baseline_mean"]

            vci         = compute_vci(ndvi_current, ndvi_5yr_min, ndvi_5yr_max)
            vci_info    = classify_vci(vci)
            anomaly_pct = compute_ndvi_anomaly(ndvi_current, baseline_mean)
            sat_loss    = estimate_satellite_loss(vci, anomaly_pct)
            threshold   = sat_loss > 43.0
            affected_ha = round(mandal["area_ha"] * (sat_loss / 100.0))
            spi_val     = zone_spi_map.get(mandal["zone"], -1.5 if season == "Kharif_2023" else 0.3)
            spi_class   = classify_spi(spi_val)

            result.append({
                "mandal_id":        mandal["mandal_id"],
                "mandal_name":      mandal["mandal_name"],
                "ndvi_current":     round(ndvi_current, 3),
                "ndvi_baseline":    round(baseline_mean, 3),
                "ndvi_anomaly_pct": round(anomaly_pct, 1),
                "vci":              round(vci, 1),
                "vci_status":       vci_info["status"],
                "ndwi_current":     round(ndvi_current * 0.3, 3),
                "spi_value":        round(spi_val, 2),
                "spi_category":     spi_class["category"],
                "estimated_loss_pct":  round(sat_loss, 1),
                "threshold_breached":  threshold,
                "affected_area_ha":    affected_ha,
                "dominant_crop":       mandal["dominant_crop"],
                "zone":                mandal["zone"],
                "map_color":           vci_info["map_color"],
            })
        except Exception:
            continue

    return make_response({"season": season, "mandals": result})


@router.get("/satellite-timeseries")
def get_satellite_timeseries(
    mandal_id: str = Query(...),
    season: str   = Query(...),
):
    """Full 18-week NDVI/VCI/NDWI timeseries for a single mandal."""
    _validate_season(season)

    try:
        get_mandal(mandal_id)
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Mandal '{mandal_id}' not found.")

    ts_data = get_ndvi_timeseries(mandal_id, season)
    series  = ts_data["timeseries"]

    ndvi_5yr_min  = ts_data.get("ndvi_5yr_min", 0.15)
    ndvi_5yr_max  = ts_data.get("ndvi_5yr_max", 0.82)
    rainfall_list = _RAINFALL_2023 if season == "Kharif_2023" else _RAINFALL_2020

    timeseries_out = []
    for i, week in enumerate(series):
        vci  = compute_vci(week["ndvi"], ndvi_5yr_min, ndvi_5yr_max)
        ndwi = round(week["ndvi"] * 0.3, 3)
        rainfall_mm = rainfall_list[i] if i < len(rainfall_list) else 0

        timeseries_out.append({
            "week":        week["week"],
            "date":        week["date"],
            "ndvi":        week["ndvi"],
            "vci":         round(vci, 1),
            "ndwi":        ndwi,
            "rainfall_mm": rainfall_mm,
        })

    mandal_info = get_mandal(mandal_id)
    return make_response({
        "mandal_id":    mandal_id,
        "mandal_name":  mandal_info["mandal_name"],
        "season":       season,
        "timeseries":   timeseries_out,
        "baseline_band": ts_data["baseline_band"],
    })


@router.get("/pipeline-status")
def get_pipeline_status(season: str = Query(...)):
    """72-hour disaster response pipeline status for a season."""
    _validate_season(season)

    if season == "Kharif_2023":
        stages        = _PIPELINE_STAGES_2023
        event_name    = "Kharif 2023 Drought — Kurnool District"
        detected_at   = "2023-09-12T06:00:00Z"
        hours_taken   = 60
    else:
        stages        = _PIPELINE_STAGES_2020
        event_name    = "Kharif 2020 — Normal Season Monitoring"
        detected_at   = "2020-07-01T06:00:00Z"
        hours_taken   = 54

    return make_response({
        "event_name":        event_name,
        "event_detected_at": detected_at,
        "pipeline_stages":   stages,
        "total_hours_taken": hours_taken,
        "target_hours":      72,
        "within_target":     True,
    })
