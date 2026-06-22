"""
AP-CropGuard — Parametric Router
==================================
Screen 2 endpoints: insurance calculation, scenario
simulation, back-testing, and premium table.
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from datetime import datetime, timezone
from typing import Optional

from data.crops import (
    CROPS, CROP_NAMES, PERILS,
    get_kc_and_stage, compute_das, THRESHOLD_LOSS_PCT,
)
from data.mandals import get_mandal
from data.historical import get_disaster_history
from engines.spi_engine import (
    compute_spi, classify_spi, compute_cdd, check_drought_triggers,
)
from engines.weather_loader import (
    compute_real_spi as _compute_real_spi,
    get_rainfall_provenance,
)
from engines.vci_engine import (
    compute_vci, classify_vci, compute_ndvi_anomaly, estimate_satellite_loss,
)
from engines.satellite_loader import (
    get_nearest_composite, get_mandal_ndvi_bounds, get_mandal_season_mean,
)
from engines.actuarial_engine import (
    compute_weather_loss, compute_parametric_loss,
    compute_payout, build_payout_curve,
    compute_premium, build_term_sheet,
    compute_sensor_divergence_coefficient, _SCIENTIFIC_BASIS,
)
from engines.backtest_engine import run_full_backtest, run_all_crops_backtest

router = APIRouter(prefix="/parametric", tags=["parametric"])

# ---------------------------------------------------------------------------
# CONSTANTS
# ---------------------------------------------------------------------------

# Synthetic 30-value baseline rainfall series centred around 80 mm
# Used when no pre-computed SPI is supplied in the request
_SPI_BASELINE = [
    55, 62, 45, 90, 110, 75, 40, 85, 95, 120,
    65, 30, 80, 95, 115, 130, 70, 45, 88, 100,
    125, 140, 85, 50, 75, 90, 105, 120, 60, 35,
]

_PERIL_EVENT_FREQUENCY = {
    "Drought":  3,
    "Flood":    1,
    "DrySpell": 2,
    "Heatwave": 1,
}

# ---------------------------------------------------------------------------
# REQUEST MODELS
# ---------------------------------------------------------------------------

class WeatherInputs(BaseModel):
    rainfall_deficit_pct: float
    consecutive_dry_days: int
    max_temp_celsius: float
    spi_value: Optional[float] = None


class CalculateRequest(BaseModel):
    crop: str
    peril: str
    mandal_id: str
    season: str
    sowing_date: str
    disaster_date: str
    weather_inputs: WeatherInputs


class SimulateRequest(BaseModel):
    crop: str
    peril: str
    mandal_id: str
    sowing_date: str
    disaster_date: str
    rainfall_deficit_pct: float
    consecutive_dry_days: int
    max_temp_celsius: float

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


def _validate_crop(crop: str):
    if crop not in CROP_NAMES:
        raise HTTPException(
            status_code=400,
            detail=f"Crop '{crop}' not recognised. Valid crops: {CROP_NAMES}",
        )


def _validate_peril(peril: str):
    if peril not in PERILS:
        raise HTTPException(
            status_code=400,
            detail=f"Peril '{peril}' not recognised. Valid perils: {PERILS}",
        )


def _validate_mandal(mandal_id: str) -> dict:
    try:
        return get_mandal(mandal_id)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Mandal '{mandal_id}' not found. Valid IDs: KNL_001 to KNL_027",
        )


def _compute_spi_from_deficit(rainfall_deficit_pct: float) -> float:
    proxy_rainfall = 100.0 * (1.0 - float(rainfall_deficit_pct) / 100.0)
    return compute_spi(proxy_rainfall, _SPI_BASELINE)

# ---------------------------------------------------------------------------
# ENDPOINTS
# ---------------------------------------------------------------------------

@router.post("/calculate")
def post_parametric_calculate(req: CalculateRequest):
    """
    Full parametric insurance calculation for a crop-peril event.
    Computes DAS, Kc, SPI, weather loss, satellite loss, payout, and term sheet.
    """
    _validate_crop(req.crop)
    _validate_peril(req.peril)
    mandal = _validate_mandal(req.mandal_id)

    # DAS and crop stage
    das = compute_das(req.sowing_date, req.disaster_date)
    kc, crop_stage = get_kc_and_stage(req.crop, das)

    # SPI — use supplied value, then real rainfall, then synthetic proxy
    wi = req.weather_inputs
    spi_source = "provided"
    spi_detail = {}

    if wi.spi_value is not None:
        spi_val = float(wi.spi_value)
        spi_source = "provided"
    else:
        try:
            real = _compute_real_spi(
                req.mandal_id, req.season,
                crop=req.crop, sowing_date=req.sowing_date,
            )
            spi_val = real["spi"]
            spi_source = "real_rainfall"
            spi_detail = {
                "cumulative_rainfall_mm": real["cumulative_rainfall_mm"],
                "baseline_mean_mm":       real["baseline_mean_mm"],
                "window_months":          real["window_months"],
                "window_derivation":      real["window_derivation"],
                "critical_stage":         real.get("critical_stage"),
                "critical_stage_dates":   real.get("critical_stage_dates"),
                "data_source":            get_rainfall_provenance()["source"],
            }
        except (ValueError, KeyError):
            spi_val = _compute_spi_from_deficit(wi.rainfall_deficit_pct)
            spi_source = "rainfall_deficit_proxy"

    cdd_val = int(wi.consecutive_dry_days)
    triggers = check_drought_triggers(spi_val, cdd_val)

    # Weather loss (from SPI / CDD / temperature)
    weather_loss = compute_weather_loss(spi_val, cdd_val, wi.max_temp_celsius, req.peril)

    # Satellite loss — real MODIS VCI for the mandal, nearest composite <= disaster_date
    sat_detail: dict = {}
    sat_loss_source = "weather_proxy"
    try:
        composite = get_nearest_composite(req.mandal_id, req.season, req.disaster_date)
        if composite is not None:
            ndvi_min, ndvi_max = get_mandal_ndvi_bounds(req.mandal_id)
            baseline_mean = get_mandal_season_mean(req.mandal_id, "Kharif_2020") or composite["ndvi"]
            vci_val  = compute_vci(composite["ndvi"], ndvi_min, ndvi_max)
            vci_cls  = classify_vci(vci_val)
            anomaly  = compute_ndvi_anomaly(composite["ndvi"], baseline_mean)
            satellite_loss = estimate_satellite_loss(vci_val, anomaly)
            sat_loss_source = "modis_vci"
            sat_detail = {
                "composite_date":     composite["date"],
                "ndvi":               composite["ndvi"],
                "evi":                composite["evi"],
                "ndwi":               composite["ndwi"],
                "cloud_quality":      composite["cloud_quality"],
                "vci":                round(vci_val, 1),
                "vci_status":         vci_cls["status"],
                "ndvi_anomaly_pct":   anomaly,
                "ndvi_min":           ndvi_min,
                "ndvi_max":           ndvi_max,
                "baseline_mean_ndvi": round(float(baseline_mean), 4),
            }
        else:
            satellite_loss = weather_loss * 0.95
            sat_loss_source = "weather_proxy_no_composite"
    except Exception:
        satellite_loss = weather_loss * 0.95
        sat_loss_source = "weather_proxy_fallback"

    # Divergence analysis — classify the relationship between weather and satellite signals
    signal_divergence = round(abs(satellite_loss - weather_loss), 1)
    if weather_loss >= 30.0 and satellite_loss < 20.0:
        divergence_analysis = "LAGGED_DAMAGE"
        divergence_message = (
            "Weather indices show drought stress at the critical crop stage, but canopy "
            "greenness (NDVI) has not yet collapsed. This is characteristic of "
            "flowering/reproductive-stage drought, where yield loss precedes visible canopy "
            "decline. Satellite-only assessment would miss this event. Parametric weather "
            "triggers capture it."
        )
        # Trust weather more: canopy lag means satellite under-represents damage
        raw_loss = weather_loss * 0.75 + satellite_loss * 0.25
    elif weather_loss >= 30.0 and satellite_loss >= 30.0:
        divergence_analysis = "CONFIRMED_LOSS"
        divergence_message = (
            "Both weather indices and satellite vegetation confirm crop loss."
        )
        raw_loss = satellite_loss * 0.5 + weather_loss * 0.5
    elif satellite_loss >= 30.0 and weather_loss < 20.0:
        divergence_analysis = "NON_WEATHER_STRESS"
        divergence_message = (
            "Vegetation decline not explained by weather — possible pest, disease, or "
            "non-climatic cause. Flag for field review."
        )
        raw_loss = satellite_loss * 0.6 + weather_loss * 0.4
    else:
        divergence_analysis = "NO_SIGNIFICANT_LOSS"
        divergence_message = (
            "No significant loss signal in either weather or satellite indicators."
        )
        raw_loss = satellite_loss * 0.6 + weather_loss * 0.4

    parametric_loss = float(min(raw_loss * kc, 100.0))
    payout, threshold_breached = compute_payout(req.crop, parametric_loss)

    sdc = compute_sensor_divergence_coefficient(
        satellite_loss, weather_loss, kc, crop_stage
    )

    freq = _PERIL_EVENT_FREQUENCY.get(req.peril, 1)
    term_sheet   = build_term_sheet(req.crop, req.peril, parametric_loss, spi_val, cdd_val, freq)
    payout_curve = build_payout_curve(req.crop)

    return make_response({
        "crop":                          req.crop,
        "peril":                         req.peril,
        "mandal":                        mandal["mandal_name"],
        "das_at_event":                  das,
        "crop_stage":                    crop_stage,
        "kc_multiplier":                 kc,
        "satellite_loss_pct":            round(satellite_loss, 1),
        "weather_loss_pct":              round(weather_loss, 1),
        "signal_divergence":             signal_divergence,
        "divergence_analysis":           divergence_analysis,
        "divergence_message":            divergence_message,
        "sensor_divergence_coefficient": sdc,
        "scientific_basis":              _SCIENTIFIC_BASIS,
        "sat_loss_source":               sat_loss_source,
        "satellite_detail":              sat_detail,
        "parametric_loss_pct":           round(parametric_loss, 1),
        "final_loss_pct":                round(parametric_loss, 1),
        "threshold_43_breached":         threshold_breached,
        "trigger_activated":             triggers["overall_trigger"],
        "trigger_details":               triggers,
        "spi_source":                    spi_source,
        "spi_detail":                    spi_detail,
        "term_sheet":                    term_sheet,
        "payout_curve":                  payout_curve,
    })


@router.post("/simulate")
def post_parametric_simulate(req: SimulateRequest):
    """
    Lightweight simulation for real-time slider updates.
    Returns only the key output fields — no term sheet or payout curve.
    """
    _validate_crop(req.crop)
    _validate_peril(req.peril)
    _validate_mandal(req.mandal_id)

    das = compute_das(req.sowing_date, req.disaster_date)
    kc, crop_stage = get_kc_and_stage(req.crop, das)

    spi_val = _compute_spi_from_deficit(req.rainfall_deficit_pct)
    cdd_val = int(req.consecutive_dry_days)

    weather_loss    = compute_weather_loss(spi_val, cdd_val, req.max_temp_celsius, req.peril)
    satellite_loss  = weather_loss * 0.95
    parametric_loss = compute_parametric_loss(satellite_loss, weather_loss, kc)

    payout, threshold_breached = compute_payout(req.crop, parametric_loss)

    return make_response({
        "spi_computed":       round(spi_val, 3),
        "estimated_loss_pct": round(parametric_loss, 1),
        "threshold_breached": threshold_breached,
        "payout_per_ha":      int(round(payout)),
        "trigger_status":     "ACTIVATED" if threshold_breached else "NOT_ACTIVATED",
        "crop_stage":         crop_stage,
        "kc_multiplier":      kc,
    })


@router.get("/backtest/results")
def get_backtest_results(crop: Optional[str] = Query(None)):
    """
    Run historical back-test and return Pearson correlation.
    Correlation is computed live via scipy.stats.pearsonr — not hardcoded.
    """
    if crop:
        _validate_crop(crop)
        result = run_full_backtest(crop)
    else:
        result = run_all_crops_backtest()

    result["note"] = (
        "Correlation computed live using "
        "scipy.stats.pearsonr — not hardcoded."
    )
    return make_response(result)


@router.get("/insurance/premium-table")
def get_premium_table():
    """
    Premium table for all 5 crops × 4 perils using GoI PMFBY actuarial guidelines.
    """
    table = []

    for crop_name in CROP_NAMES:
        for peril in PERILS:
            freq = _PERIL_EVENT_FREQUENCY.get(peril, 1)
            premium_info = compute_premium(crop_name, peril, freq)
            rate = premium_info["premium_rate_pct"]

            if rate > 5.0:
                risk_level = "HIGH"
            elif rate >= 3.0:
                risk_level = "MEDIUM"
            else:
                risk_level = "LOW"

            table.append({
                "crop":                      crop_name,
                "peril":                     peril,
                "sum_insured_per_ha":        int(premium_info["sum_insured"]),
                "premium_rate_pct":          rate,
                "premium_per_ha":            int(round(premium_info["commercial_premium"])),
                "historical_event_frequency": freq,
                "risk_level":                risk_level,
            })

    return make_response({
        "district": "Kurnool",
        "season":   "Kharif_2026",
        "table":    table,
        "note": (
            "Premium rates calculated using GoI PMFBY actuarial guidelines. "
            "Commercial loading: 15% expense + 10% risk margin."
        ),
        "actuarial_basis": (
            "Premiums derived from GoI PMFBY actuarial methodology — historical event "
            "frequency × crop-stage vulnerability × sum insured. "
            "Loading: 15% expense + 10% risk margin per standard reinsurance practice."
        ),
    })
