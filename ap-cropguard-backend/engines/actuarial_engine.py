"""
AP-CropGuard — Actuarial Engine
================================
Actuarial methodology: GoI PMFBY guidelines,
FAO Actuarial Guidelines for Agricultural Insurance.
Premium loading factors based on AP Agriculture Dept
Kharif insurance scheme historical loss ratios.
"""

import numpy as np
from scipy import stats
from datetime import datetime

from data.crops import CROPS, THRESHOLD_LOSS_PCT, get_kc_and_stage, compute_das


_SCIENTIFIC_BASIS = {
    "phenomenon": (
        "Satellite NDVI underestimates crop yield loss at reproductive growth stages "
        "because canopy greenness lags physiological and yield decline."
    ),
    "references": [
        {
            "citation": "Qiu et al. (2022), Agricultural and Forest Meteorology, Vol. 323, 109038",
            "finding": (
                "During the 2012 US Midwest drought, crop yield fell 25% but MODIS NDVI "
                "declined only 4% — NDVI captured a fraction of actual loss."
            ),
        },
        {
            "citation": "Ding et al. (2022), Catena, Vol. 219, 106328",
            "finding": (
                "NDVI drought-propagation time is longer than physiological stress indicators — "
                "canopy greenness responds to drought after yield damage has begun."
            ),
        },
        {
            "citation": "Becker & Schmidhalter (2017), Frontiers in Plant Science, 8:379",
            "finding": (
                "At wheat reproductive stage (anthesis/grain-fill), NDVI showed weaker "
                "drought-yield correlation than water-content indices."
            ),
        },
    ],
}


def compute_sensor_divergence_coefficient(
    satellite_loss_pct: float,
    weather_loss_pct: float,
    kc_multiplier: float,
    crop_stage_label: str,
) -> dict:
    """
    Sensor Divergence Coefficient (SDC) — quantifies how much the weather signal
    exceeds the satellite signal, scaled by crop-stage vulnerability (Kc).

    SDC = (raw_divergence / 100.0) * kc_multiplier

    Grounded in peer-reviewed evidence that NDVI lags actual yield loss during
    reproductive-stage drought (Qiu et al. 2022; Ding et al. 2022;
    Becker & Schmidhalter 2017).
    """
    raw_divergence = float(weather_loss_pct) - float(satellite_loss_pct)
    sdc = (raw_divergence / 100.0) * float(kc_multiplier)

    if raw_divergence > 30 and float(kc_multiplier) >= 1.5:
        interpretation = "SATELLITE_BLIND_TO_REPRODUCTIVE_LOSS"
        sensor_decision = "WEATHER_PRIMARY"
    elif raw_divergence > 30:
        interpretation = "WEATHER_LEADS_SATELLITE"
        sensor_decision = "BALANCED"
    elif raw_divergence < -30:
        interpretation = "NON_WEATHER_VEGETATION_STRESS"
        sensor_decision = "SATELLITE_PRIMARY"
    else:
        interpretation = "SENSORS_CONVERGENT"
        sensor_decision = "BALANCED"

    return {
        "sdc_value":       round(sdc, 3),
        "raw_divergence":  round(raw_divergence, 1),
        "interpretation":  interpretation,
        "sensor_decision": sensor_decision,
    }


def compute_parametric_loss(
    satellite_loss_pct: float,
    weather_loss_pct: float,
    kc_multiplier: float,
) -> float:
    """
    Combine satellite and weather loss signals, weighted and scaled by Kc.

    raw_loss       = satellite_loss_pct * 0.6 + weather_loss_pct * 0.4
    adjusted_loss  = raw_loss * kc_multiplier

    Result clamped to [0.0, 100.0].
    """
    raw_loss = (float(satellite_loss_pct) * 0.6) + (float(weather_loss_pct) * 0.4)
    adjusted_loss = raw_loss * float(kc_multiplier)
    return float(np.clip(adjusted_loss, 0.0, 100.0))


def compute_weather_loss(
    spi_value: float,
    cdd_value: float,
    max_temp: float,
    peril: str,
) -> float:
    """
    Estimate weather-driven crop loss percentage for a given peril.

    Drought  : tiered SPI loss + CDD bonus (capped at 20 pts)
    Flood    : duration-based loss (cdd_value used as flood_duration_days)
    DrySpell : CDD excess above 15-day threshold
    Heatwave : temperature tier lookup
    """
    peril = peril.strip()

    if peril == "Drought":
        spi = float(spi_value)
        if spi <= -2.0:
            base = 80.0
        elif spi <= -1.5:
            base = 60.0
        elif spi <= -1.0:
            base = 40.0
        elif spi <= -0.5:
            base = 20.0
        else:
            base = 0.0
        cdd_bonus = min(float(cdd_value) * 1.2, 20.0)
        return min(base + cdd_bonus, 100.0)

    elif peril == "Flood":
        return min(max(0.0, (float(cdd_value) - 5.0) * 8.0), 100.0)

    elif peril == "DrySpell":
        return min(max(0.0, (float(cdd_value) - 15.0) * 3.5), 100.0)

    elif peril == "Heatwave":
        temp = float(max_temp)
        if temp >= 45.0:
            return 70.0
        elif temp >= 43.0:
            return 50.0
        elif temp >= 41.0:
            return 30.0
        else:
            return 0.0

    return 0.0


def compute_payout(crop_name: str, loss_pct: float) -> tuple:
    """
    Compute parametric payout for a given crop and loss percentage.

    Returns (payout_per_ha, threshold_breached):
      - payout_per_ha      : 0.0 if loss_pct < THRESHOLD_LOSS_PCT (43%)
      - threshold_breached : False if below threshold, True otherwise
    """
    crop = CROPS[crop_name]
    sum_insured = float(crop["sum_insured_per_ha"])
    loss = float(loss_pct)

    if loss < THRESHOLD_LOSS_PCT:
        return 0.0, False

    payout = sum_insured * (loss / 100.0)
    return round(payout, 2), True


def build_payout_curve(crop_name: str) -> list:
    """
    Build a payout curve for display as a chart.

    Returns a list of {loss_pct, payout_per_ha} dicts at key loss levels.
    Payouts below 43% are zero; at and above 43% they scale with loss_pct.
    """
    breakpoints = [0, 10, 20, 30, 43, 50, 60, 70, 80, 90, 100]
    curve = []
    for lp in breakpoints:
        payout, _ = compute_payout(crop_name, float(lp))
        curve.append({
            "loss_pct": lp,
            "payout_per_ha": int(round(payout)),
        })
    return curve


def compute_premium(
    crop_name: str,
    peril: str,
    historical_event_frequency: float,
) -> dict:
    """
    Compute actuarial premium for a crop-peril combination.

    Formula:
      pure_premium       = sum_insured * (freq/10) * (max_kc/2) * 0.08
      commercial_premium = pure_premium * (1 + 0.15 + 0.10)
      premium_rate_pct   = (commercial_premium / sum_insured) * 100

    Loading factors:
      expense_loading = 15%  (GoI PMFBY administrative cost cap)
      risk_margin     = 10%  (AP Kharif historical volatility buffer)
    """
    crop = CROPS[crop_name]
    sum_insured = float(crop["sum_insured_per_ha"])

    max_kc = max(stage["kc"] for stage in crop["kc_stages"].values())

    expense_loading = 0.15
    risk_margin = 0.10

    pure_premium = sum_insured * (float(historical_event_frequency) / 10.0) * (max_kc / 2.0) * 0.08
    commercial_premium = pure_premium * (1.0 + expense_loading + risk_margin)
    premium_rate_pct = (commercial_premium / sum_insured) * 100.0

    return {
        "sum_insured": round(sum_insured, 2),
        "pure_premium": round(pure_premium, 2),
        "commercial_premium": round(commercial_premium, 2),
        "premium_rate_pct": round(premium_rate_pct, 2),
        "expense_loading": round(expense_loading, 2),
        "risk_margin": round(risk_margin, 2),
    }


_STRIKE_LEVELS = {
    "Drought":  "SPI ≤ -1.0 OR CDD > 15 days",
    "Flood":    "NDWI anomaly > 0.15 OR rainfall > 100mm/24hr",
    "DrySpell": "CDD > 15 days during critical crop stage",
    "Heatwave": "Max temp > 41°C for 5+ consecutive days",
}

_EXIT_LEVELS = {
    "Drought":  "SPI ≤ -2.0 OR CDD > 30 days",
    "Flood":    "NDWI anomaly > 0.30 OR inundation > 72hrs",
    "DrySpell": "CDD > 30 days",
    "Heatwave": "Max temp > 45°C for 5+ consecutive days",
}


def build_term_sheet(
    crop_name: str,
    peril: str,
    loss_pct: float,
    spi_value: float,
    cdd_value: float,
    historical_event_frequency: float,
) -> dict:
    """
    Build a complete insurance term sheet for a crop-peril event.

    Calls compute_payout() and compute_premium() internally.
    Payout reference levels (43%, 60%, 80%, 100%) are always computed
    against the crop's sum_insured regardless of current loss_pct.
    """
    premium_info = compute_premium(crop_name, peril, historical_event_frequency)
    current_payout, threshold_breached = compute_payout(crop_name, loss_pct)

    payout_43, _ = compute_payout(crop_name, 43.0)
    payout_60, _ = compute_payout(crop_name, 60.0)
    payout_80, _ = compute_payout(crop_name, 80.0)
    payout_100, _ = compute_payout(crop_name, 100.0)

    return {
        "crop": crop_name,
        "peril": peril,
        "sum_insured_per_ha": int(premium_info["sum_insured"]),
        "premium_rate_pct": premium_info["premium_rate_pct"],
        "premium_per_ha": int(round(premium_info["commercial_premium"])),
        "strike_level": _STRIKE_LEVELS.get(peril, "N/A"),
        "exit_level": _EXIT_LEVELS.get(peril, "N/A"),
        "payout_at_43_pct": int(round(payout_43)),
        "payout_at_60_pct": int(round(payout_60)),
        "payout_at_80_pct": int(round(payout_80)),
        "payout_at_100_pct": int(round(payout_100)),
        "current_estimated_payout_per_ha": int(round(current_payout)),
        "threshold_43_breached": threshold_breached,
        "currency": "INR",
    }
