"""
AP-CropGuard — MODIS Satellite Data Loader
Reads real NASA MODIS MOD13Q1 16-day composite data exported from Google Earth Engine.
Data: data/satellite/kurnool_modis_{year}.csv
"""

import os
import pandas as pd
from datetime import datetime
from functools import lru_cache

# Path relative to this file: engines/ -> ../../data/satellite/ (project root)
_DATA_DIR = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'data', 'satellite')
)

_SEASON_FILE = {
    "Kharif_2020": os.path.join(_DATA_DIR, "kurnool_modis_2020.csv"),
    "Kharif_2023": os.path.join(_DATA_DIR, "kurnool_modis_2023.csv"),
}

_SEASONS = list(_SEASON_FILE.keys())


def _parse_gee_date(date_str: str) -> str:
    """
    Normalise a date string from the MODIS CSV export to ISO YYYY-MM-DD.

    Two formats are handled:
      ISO (already correct): "2023-06-10"  → returned unchanged.
      GEE Joda-Time artifact: "2023-06-161" where uppercase 'DD' in the GEE
        format string emits the day-of-year (161 = Julian day 161 = Jun 10).
        These are identified by the last segment being > 31 (impossible as a
        day-of-month).  Parsed via year + doy only.

    Example GEE: "2023-06-161" -> "2023-06-10"
    Example ISO:  "2023-06-10"  -> "2023-06-10"
    """
    parts = str(date_str).split("-")
    year = parts[0]
    last = parts[-1]
    if int(last) > 31:
        # GEE Joda-Time day-of-year artifact
        return datetime.strptime(f"{year}-{last}", "%Y-%j").strftime("%Y-%m-%d")
    # Already ISO format
    return date_str


@lru_cache(maxsize=2)
def load_modis_data(season: str) -> pd.DataFrame:
    """
    Load, clean, and cache MODIS data for a season.

    Returns a DataFrame with columns:
      mandal_id, mandal_name, date (ISO YYYY-MM-DD), ndvi_value, evi_value,
      ndwi_value, pixel_count, cloud_quality_flag, no_data (bool)
    """
    if season not in _SEASON_FILE:
        raise ValueError(
            f"Season '{season}' not available. Valid seasons: {_SEASONS}"
        )

    df = pd.read_csv(_SEASON_FILE[season])

    # Fix GEE Joda-Time date format to ISO
    df["date"] = df["date"].apply(_parse_gee_date)

    # Mark no-data: null NDVI or zero valid pixels after cloud masking
    df["no_data"] = df["ndvi_value"].isna() | (df["pixel_count"] == 0)

    df = df.sort_values(["mandal_id", "date"]).reset_index(drop=True)
    return df


def get_mandal_timeseries(mandal_id: str, season: str) -> list:
    """
    Returns composite observations for one mandal, sorted by date.

    No-data composites (cloud-masked) are included with ndvi/evi/ndwi=None
    so charts render a gap rather than a zero. The no_data flag is always set.
    """
    df = load_modis_data(season)
    rows = df[df["mandal_id"] == mandal_id].sort_values("date")

    result = []
    for i, (_, row) in enumerate(rows.iterrows()):
        is_nodata = bool(row["no_data"])
        result.append({
            "composite":   i + 1,
            "date":        row["date"],
            "ndvi":        None if is_nodata else round(float(row["ndvi_value"]), 4),
            "evi":         None if is_nodata else round(float(row["evi_value"]),  4),
            "ndwi":        None if is_nodata else round(float(row["ndwi_value"]), 4),
            "pixel_count": int(row["pixel_count"]),
            "cloud_quality": (
                round(float(row["cloud_quality_flag"]), 3)
                if pd.notna(row["cloud_quality_flag"]) else None
            ),
            "no_data": is_nodata,
        })
    return result


def get_mandal_season_mean(mandal_id: str, season: str):
    """
    Mean NDVI for a mandal over a season, excluding cloud-masked composites.
    Returns None if no valid data exists.
    """
    df = load_modis_data(season)
    valid = df[(df["mandal_id"] == mandal_id) & ~df["no_data"]]
    if valid.empty:
        return None
    return round(float(valid["ndvi_value"].mean()), 4)


def get_all_mandals_latest(season: str) -> dict:
    """
    Returns {mandal_id: latest_valid_ndvi} for all mandals.
    'Latest' = chronologically last composite with non-masked data.
    Used for map tile coloring.
    """
    df = load_modis_data(season)
    valid = df[~df["no_data"]].copy()
    latest = valid.sort_values("date").groupby("mandal_id").last()
    return {
        mid: round(float(row["ndvi_value"]), 4)
        for mid, row in latest.iterrows()
    }


def get_mandal_ndvi_bounds(mandal_id: str) -> tuple:
    """
    Per-mandal NDVI (min, max) derived from all valid 2020+2023 composites.
    Replaces the generic district-wide 0.15/0.82 bounds with Kurnool-calibrated
    values that make VCI sensitive to each mandal's actual vegetation range.

    Enforces a minimum range of 0.20 to prevent hypersensitive VCI on
    mandals with narrow observed variability.
    Falls back to (0.15, 0.82) if no data is available.
    """
    frames = []
    for season in _SEASONS:
        try:
            df = load_modis_data(season)
            valid = df[(df["mandal_id"] == mandal_id) & ~df["no_data"]]
            if not valid.empty:
                frames.append(valid[["ndvi_value"]])
        except Exception:
            pass

    if not frames:
        return (0.15, 0.82)

    combined = pd.concat(frames)
    lo = round(float(combined["ndvi_value"].min()), 4)
    hi = round(float(combined["ndvi_value"].max()), 4)

    if (hi - lo) < 0.20:
        mid = (hi + lo) / 2
        lo = round(mid - 0.10, 4)
        hi = round(mid + 0.10, 4)

    return (lo, hi)


def get_nearest_composite(mandal_id: str, season: str, disaster_date: str) -> dict | None:
    """
    Return the nearest valid (non-cloud-masked) MODIS composite on or before
    disaster_date for a mandal.

    Returns a dict with date, ndvi, evi, ndwi, cloud_quality, or None if no
    valid composite exists on or before disaster_date.
    """
    df = load_modis_data(season)
    valid = df[
        (df["mandal_id"] == mandal_id)
        & ~df["no_data"]
        & (df["date"] <= disaster_date)
    ]
    if valid.empty:
        return None
    row = valid.sort_values("date").iloc[-1]
    return {
        "date":          row["date"],
        "ndvi":          round(float(row["ndvi_value"]), 4),
        "evi":           round(float(row["evi_value"]),  4),
        "ndwi":          round(float(row["ndwi_value"]), 4),
        "cloud_quality": round(float(row["cloud_quality_flag"]), 3),
        "pixel_count":   int(row["pixel_count"]) if pd.notna(row["pixel_count"]) else None,
    }


def get_data_provenance() -> dict:
    return {
        "source":           "NASA MODIS MOD13Q1",
        "resolution":       "250m",
        "composite":        "16-day",
        "access":           "Google Earth Engine",
        "buffer":           "2km radius per mandal centroid",
        "total_composites": 11,
        "note":             "Cloud-masked composites excluded from aggregation",
    }
