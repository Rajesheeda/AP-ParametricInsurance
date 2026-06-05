"""
AP-CropGuard — SPI Engine
=========================
SPI methodology: McKee et al. (1993).
GoI Drought Management Manual (2016) Chapter 4.
Dry day threshold: IMD definition (< 2.5mm/day).
"""

import numpy as np
from scipy import stats


def fit_gamma(rainfall_series: list) -> tuple:
    """
    Fit a Gamma distribution to a historical rainfall series.

    Zero values are excluded before fitting because the Gamma distribution
    is defined only for positive values (GoI Drought Manual 2016, §4.3.1).

    Returns (alpha, loc, beta) where loc is fixed at 0 (floc=0).
    Raises ValueError if fewer than 3 positive values remain after filtering.
    """
    data = np.array(rainfall_series, dtype=float)
    data = data[data > 0]

    if len(data) < 3:
        raise ValueError(
            f"Insufficient positive rainfall values for Gamma fit: "
            f"need >= 3, got {len(data)}."
        )

    alpha, loc, beta = stats.gamma.fit(data, floc=0)
    return float(alpha), float(loc), float(beta)


def compute_spi(current_rainfall: float, rainfall_series: list) -> float:
    """
    Compute the Standardized Precipitation Index (SPI) for a given rainfall
    observation against a historical baseline series.

    Steps (McKee et al. 1993):
      1. Fit Gamma distribution to historical series (zeros excluded).
      2. Compute CDF of current_rainfall under the fitted distribution.
      3. Convert CDF probability to standard normal quantile (Z-score = SPI).

    Zero or negative current_rainfall is treated as 0.001 to avoid
    undefined CDF at zero.
    """
    alpha, loc, beta = fit_gamma(rainfall_series)

    rainfall = max(0.001, float(current_rainfall))

    cdf_val = stats.gamma.cdf(rainfall, a=alpha, loc=loc, scale=beta)
    # Clip to open interval to prevent ±inf from norm.ppf at boundaries
    cdf_val = float(np.clip(cdf_val, 1e-6, 1 - 1e-6))

    spi_value = float(stats.norm.ppf(cdf_val))
    return round(spi_value, 3)


def classify_spi(spi_value: float) -> dict:
    """
    Classify an SPI value into a drought category per GoI Drought Manual 2016.

    Returns a dict with keys: category, description.
    """
    v = float(spi_value)

    if v >= -0.5:
        return {"category": "NORMAL", "description": "Normal conditions"}
    elif v >= -1.0:
        return {"category": "MODERATELY_DRY", "description": "Moderate drought"}
    elif v >= -1.5:
        return {"category": "SEVERELY_DRY", "description": "Severe drought — payout initiation threshold"}
    elif v >= -2.0:
        return {"category": "EXTREMELY_DRY", "description": "Extreme drought"}
    else:
        return {"category": "EXCEPTIONAL_DRY", "description": "Exceptional drought — maximum payout"}


def compute_cdd(daily_rainfall_list: list) -> int:
    """
    Compute the maximum Consecutive Dry Days (CDD) in a daily rainfall series.

    A dry day is defined as rainfall < 2.5 mm/day (IMD standard definition).

    Returns the length of the longest unbroken dry-day streak as an integer.
    """
    max_streak = 0
    current_streak = 0

    for rain in daily_rainfall_list:
        if float(rain) < 2.5:
            current_streak += 1
            if current_streak > max_streak:
                max_streak = current_streak
        else:
            current_streak = 0

    return max_streak


def check_drought_triggers(spi_value: float, cdd_value: int) -> dict:
    """
    Evaluate parametric trigger conditions for drought payout activation.

    Trigger rules (AP-CropGuard contract):
      SPI trigger  : spi_value <= -1.0
      CDD trigger  : cdd_value >= 15

    Severity is determined by SPI thresholds regardless of CDD.
    """
    spi_classification = classify_spi(spi_value)
    category = spi_classification["category"]

    spi_trigger = spi_value <= -1.0
    cdd_trigger = cdd_value >= 15
    overall_trigger = spi_trigger or cdd_trigger

    if category in ("EXCEPTIONAL_DRY",):
        severity = "EXTREME"
    elif category in ("EXTREMELY_DRY",):
        severity = "SEVERE"
    elif category in ("SEVERELY_DRY",):
        severity = "MODERATE"
    else:
        severity = "NONE"

    return {
        "spi_trigger": spi_trigger,
        "cdd_trigger": cdd_trigger,
        "overall_trigger": overall_trigger,
        "spi_value": float(spi_value),
        "cdd_value": int(cdd_value),
        "spi_category": category,
        "spi_description": spi_classification["description"],
        "trigger_severity": severity,
    }
