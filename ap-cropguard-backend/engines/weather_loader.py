"""
AP-CropGuard — Weather / Rainfall Data Loader
Reads real daily rainfall from Open-Meteo ERA5-Land reanalysis exports
and the 30-year IMD-calibrated monthly baseline for Gamma SPI fitting.

Data files (project root /data/weather/):
  kurnool_rainfall_2020.csv          — daily, 27 mandals, Jun–Nov 2020
  kurnool_rainfall_2023.csv          — daily, 27 mandals, Jun–Nov 2023
  kurnool_rainfall_baseline_30yr.csv — monthly, 1990–2020, 6 Kharif months
"""

import os
import numpy as np
import pandas as pd
from datetime import datetime, date as _date, timedelta
from functools import lru_cache

from engines.spi_engine import compute_spi

# Path from engines/ → project root → data/weather/
_DATA_DIR = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'data', 'weather')
)

_SEASON_FILE = {
    "Kharif_2020": os.path.join(_DATA_DIR, "kurnool_rainfall_2020.csv"),
    "Kharif_2023": os.path.join(_DATA_DIR, "kurnool_rainfall_2023.csv"),
}

_BASELINE_FILE = os.path.join(_DATA_DIR, "kurnool_rainfall_baseline_30yr.csv")

_MONTH_MAP = {
    "Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4,
    "May": 5, "Jun": 6, "Jul": 7, "Aug": 8,
    "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12,
}


def _to_month_ints(months) -> list:
    """Accept month names ('Jun') or ints (6) and return a list of ints."""
    return [_MONTH_MAP[m] if isinstance(m, str) else int(m) for m in months]


@lru_cache(maxsize=2)
def load_rainfall(season: str) -> pd.DataFrame:
    """
    Load and cache daily rainfall for a season.

    Returns DataFrame with columns:
      mandal_id, mandal_name, date (Timestamp), rainfall_mm
    """
    if season not in _SEASON_FILE:
        raise ValueError(
            f"Season '{season}' not available. Valid: {list(_SEASON_FILE.keys())}"
        )
    df = pd.read_csv(_SEASON_FILE[season])
    df["date"] = pd.to_datetime(df["date"])
    return df


@lru_cache(maxsize=1)
def get_baseline_monthly() -> pd.DataFrame:
    """
    Load and cache the 30-year monthly baseline (1990–2020).

    Returns DataFrame with columns: year, month, monthly_rainfall_mm
    """
    return pd.read_csv(_BASELINE_FILE)


def get_mandal_rainfall(
    mandal_id: str,
    season: str,
    start_date: str,
    end_date: str,
) -> float:
    """
    Total rainfall for a mandal in an explicit date window [start, end] inclusive.

    start_date / end_date: ISO strings e.g. "2023-08-01"
    """
    df    = load_rainfall(season)
    start = pd.Timestamp(start_date)
    end   = pd.Timestamp(end_date)
    mask  = (
        (df["mandal_id"] == mandal_id)
        & (df["date"] >= start)
        & (df["date"] <= end)
    )
    return float(df.loc[mask, "rainfall_mm"].sum())


def get_cumulative_window(mandal_id: str, season: str, months) -> float:
    """
    Cumulative rainfall for a mandal across specified calendar months.

    months: list of month names ('Jun') or ints (6).
    Example: get_cumulative_window('KNL_022', 'Kharif_2023', ['Jun','Jul','Aug','Sep'])
    """
    month_ints = _to_month_ints(months)
    df   = load_rainfall(season)
    mask = (
        (df["mandal_id"] == mandal_id)
        & df["date"].dt.month.isin(month_ints)
    )
    return float(df.loc[mask, "rainfall_mm"].sum())


def get_all_mandals_latest(season: str) -> dict:
    """
    {mandal_id: season_total_rainfall_mm} — used for map rendering.
    """
    df = load_rainfall(season)
    totals = df.groupby("mandal_id")["rainfall_mm"].sum()
    return {mid: round(float(v), 1) for mid, v in totals.items()}


def _months_in_das_range(crop_name: str, sowing_date: str) -> list:
    """
    Derive calendar months covered by a crop's highest-Kc (critical) stage.

    Finds the stage with the maximum Kc, computes its start/end calendar dates
    from the sowing date + DAS range, then returns every month that overlaps.

    Example: Groundnut sown 2023-07-01, critical stage DAS 60-90
             → 2023-08-30 to 2023-09-29 → months [8, 9] (Aug, Sep)
    """
    from data.crops import get_crop
    crop   = get_crop(crop_name)
    stages = crop["kc_stages"]
    critical = max(stages.values(), key=lambda s: s["kc"])

    sowing   = datetime.strptime(sowing_date, "%Y-%m-%d").date()
    start_dt = sowing + timedelta(days=critical["das_start"])
    end_dt   = sowing + timedelta(days=critical["das_end"])

    months = set()
    y, m = start_dt.year, start_dt.month
    ey, em = end_dt.year, end_dt.month
    while (y, m) <= (ey, em):
        months.add(m)
        m += 1
        if m > 12:
            m = 1
            y += 1

    return {
        "month_ints":      sorted(months),
        "stage_label":     critical["label"],
        "das_start":       critical["das_start"],
        "das_end":         critical["das_end"],
        "start_date":      str(start_dt),
        "end_date":        str(end_dt),
    }


def _baseline_window_series(month_ints: list) -> list:
    """
    30-year annual cumulative rainfall series for the given months.
    Used as the historical sample for Gamma SPI fitting.
    """
    bl     = get_baseline_monthly()
    window = bl[bl["month"].isin(month_ints)]
    annual = window.groupby("year")["monthly_rainfall_mm"].sum()
    return annual.tolist()


def compute_real_spi(
    mandal_id: str,
    season: str,
    crop: str = None,
    sowing_date: str = None,
    window_months=None,
) -> dict:
    """
    Compute SPI from real rainfall for a mandal and season.

    Window resolution priority:
      1. window_months explicitly provided → use it directly
      2. crop + sowing_date provided → derive months from crop's critical Kc stage
      3. Neither → fall back to Aug-Oct (broad dry-break window for Kurnool Kharif)

    The phenology-derived window makes the SPI trigger defensible:
    "We measure rainfall deficit during THIS crop's critical growth stage" —
    not a hardcoded or cherry-picked date range.

    Returns:
      spi                   — Standardized Precipitation Index (float)
      cumulative_rainfall_mm — observed window total for this mandal/season
      baseline_mean_mm      — 30-year mean for the same window
      window_months         — list of month names used
      window_derivation     — 'phenology' | 'explicit' | 'default'
      critical_stage        — stage label if derived from crop phenology, else None
      critical_stage_dates  — {start, end} calendar dates if phenology-derived, else None
      mandal_id, season, crop (if provided)
    """
    _MONTH_NAMES = {1:"Jan",2:"Feb",3:"Mar",4:"Apr",5:"May",6:"Jun",
                    7:"Jul",8:"Aug",9:"Sep",10:"Oct",11:"Nov",12:"Dec"}

    phenology_meta = None
    window_derivation = "default"

    if window_months is not None:
        month_ints = _to_month_ints(window_months)
        window_months = [_MONTH_NAMES[m] for m in month_ints]
        window_derivation = "explicit"

    elif crop is not None and sowing_date is not None:
        phenology_meta = _months_in_das_range(crop, sowing_date)
        month_ints     = phenology_meta["month_ints"]
        window_months  = [_MONTH_NAMES[m] for m in month_ints]
        window_derivation = "phenology"

    else:
        # Fallback: Aug-Oct — covers the mid-season dry-break period
        # common across Kurnool Kharif crops sown around July 1.
        month_ints    = [8, 9, 10]
        window_months = ["Aug", "Sep", "Oct"]

    current_mm      = get_cumulative_window(mandal_id, season, month_ints)
    baseline_series = _baseline_window_series(month_ints)
    baseline_mean   = float(np.mean(baseline_series))

    spi_val = compute_spi(current_mm, baseline_series)

    result = {
        "spi":                    spi_val,
        "cumulative_rainfall_mm": round(current_mm, 1),
        "baseline_mean_mm":       round(baseline_mean, 1),
        "window_months":          window_months,
        "window_derivation":      window_derivation,
        "critical_stage":         phenology_meta["stage_label"] if phenology_meta else None,
        "critical_stage_dates":   (
            {"start": phenology_meta["start_date"], "end": phenology_meta["end_date"]}
            if phenology_meta else None
        ),
        "mandal_id":              mandal_id,
        "season":                 season,
    }
    if crop:
        result["crop"] = crop
    return result


def get_rainfall_provenance() -> dict:
    return {
        "source":     "Open-Meteo ERA5-Land Reanalysis (ECMWF)",
        "access":     "archive-api.open-meteo.com",
        "baseline":   "30-year (1990-2020)",
        "resolution": "daily, per-mandal centroid",
        "note":       "Free, non-authenticated, citable",
    }
