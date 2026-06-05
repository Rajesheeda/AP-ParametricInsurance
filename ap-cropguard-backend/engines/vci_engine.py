"""
AP-CropGuard — VCI Engine
=========================
VCI: Kogan (1995), Remote Sensing of Environment.
NDWI: Gao (1996), Remote Sensing of Environment.
Loss estimation methodology calibrated to APSDMA
Kurnool district damage assessment reports.
"""

import numpy as np


def compute_vci(ndvi_current: float, ndvi_min: float, ndvi_max: float) -> float:
    """
    Compute the Vegetation Condition Index (VCI).

    Formula: VCI = ((ndvi_current - ndvi_min) / (ndvi_max - ndvi_min)) * 100

    Returns 50.0 if ndvi_max == ndvi_min (degenerate range).
    Result is clamped to [0.0, 100.0].
    """
    if ndvi_max == ndvi_min:
        return 50.0

    vci = ((float(ndvi_current) - float(ndvi_min)) /
           (float(ndvi_max) - float(ndvi_min))) * 100.0

    return float(np.clip(vci, 0.0, 100.0))


def classify_vci(vci_value: float) -> dict:
    """
    Classify a VCI value into a vegetation stress category.

    Returns dict with keys: status, description, map_color.
    """
    v = float(vci_value)

    if v >= 60.0:
        return {
            "status": "NORMAL",
            "description": "Healthy vegetation",
            "map_color": "#16A34A",
        }
    elif v >= 40.0:
        return {
            "status": "MODERATE_STRESS",
            "description": "Moderate vegetation stress",
            "map_color": "#CA8A04",
        }
    elif v >= 20.0:
        return {
            "status": "SEVERE_DROUGHT",
            "description": "Severe agricultural drought",
            "map_color": "#EA580C",
        }
    else:
        return {
            "status": "EXTREME_DROUGHT",
            "description": "Extreme drought — critical crop failure risk",
            "map_color": "#DC2626",
        }


def compute_ndvi_anomaly(ndvi_current: float, ndvi_baseline_mean: float) -> float:
    """
    Compute NDVI anomaly as percentage deviation from the baseline mean.

    Formula: anomaly = ((ndvi_current - ndvi_baseline_mean) / ndvi_baseline_mean) * 100

    Returns 0.0 if ndvi_baseline_mean is zero.
    Negative values indicate vegetation stress; positive values indicate above-normal growth.
    """
    if float(ndvi_baseline_mean) == 0.0:
        return 0.0

    anomaly = ((float(ndvi_current) - float(ndvi_baseline_mean)) /
               float(ndvi_baseline_mean)) * 100.0

    return round(float(anomaly), 2)


def compute_ndwi(green_band: float, nir_band: float) -> float:
    """
    Compute the Normalized Difference Water Index (NDWI).

    Formula: NDWI = (green - nir) / (green + nir)

    Positive NDWI indicates water presence or high canopy water content.
    Negative NDWI indicates dry/stressed vegetation.

    Returns 0.0 if the denominator is zero.
    Result is clamped to [-1.0, 1.0].
    """
    denominator = float(green_band) + float(nir_band)

    if denominator == 0.0:
        return 0.0

    ndwi = (float(green_band) - float(nir_band)) / denominator

    return float(np.clip(ndwi, -1.0, 1.0))


def estimate_satellite_loss(vci_value: float, ndvi_anomaly_pct: float) -> float:
    """
    Estimate crop loss percentage from VCI and NDVI anomaly.

    Loss tiers:
      VCI >= 60       : base_loss = 0.0
      40 <= VCI < 60  : base_loss = 20.0 + (60 - vci) * 1.0
      20 <= VCI < 40  : base_loss = 40.0 + (40 - vci) * 1.5
      VCI < 20        : base_loss = 70.0 + (20 - vci) * 1.0

    Anomaly adjustment: +5.0 if ndvi_anomaly_pct < -30.

    Result is clamped to [0.0, 100.0].
    """
    v = float(vci_value)

    if v >= 60.0:
        base_loss = 0.0
    elif v >= 40.0:
        base_loss = 20.0 + (60.0 - v) * 1.0
    elif v >= 20.0:
        base_loss = 40.0 + (40.0 - v) * 1.5
    else:
        base_loss = 70.0 + (20.0 - v) * 1.0

    if float(ndvi_anomaly_pct) < -30.0:
        base_loss += 5.0

    return float(np.clip(base_loss, 0.0, 100.0))


def check_flood_indicator(ndwi_current: float, ndwi_baseline: float) -> dict:
    """
    Detect flood conditions by comparing current NDWI against a baseline.

    A positive flood_signal indicates anomalous water presence.

    Severity thresholds:
      flood_signal <= 0.15 : NONE
      0.15 < signal <= 0.30: MODERATE
      signal > 0.30        : SEVERE
    """
    flood_signal = float(ndwi_current) - float(ndwi_baseline)

    if flood_signal > 0.30:
        severity = "SEVERE"
    elif flood_signal > 0.15:
        severity = "MODERATE"
    else:
        severity = "NONE"

    return {
        "flood_detected": flood_signal > 0.15,
        "flood_signal": round(flood_signal, 4),
        "severity": severity,
    }
