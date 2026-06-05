"""
AP-CropGuard — Photo Anti-Fraud Validation Engine
==================================================
Photo anti-fraud validation engine.
Implements geofence verification using mandal
centroid bounding boxes, EXIF timestamp cross-
validation against satellite stress window,
and edit software signature detection.
EXIF extraction: piexif + Pillow libraries.
Geofence: bounding box approximation — Phase 1
production upgrade uses full mandal boundary
polygons from AP State GIS portal.
"""

import io
import json
from datetime import datetime, timedelta, timezone

from PIL import Image
import piexif

from data.mandals import get_mandal

# ---------------------------------------------------------------------------
# INTERNAL HELPERS
# ---------------------------------------------------------------------------

_EDIT_SOFTWARE_SIGNATURES = [
    "photoshop", "lightroom", "gimp", "snapseed",
    "facetune", "meitu", "picsart", "adobe",
]


def _rational_to_float(rational: tuple) -> float:
    """Convert a piexif rational (numerator, denominator) to float."""
    num, denom = rational
    return float(num) / float(denom) if denom != 0 else 0.0


def _gps_to_decimal(gps_dms: tuple, hemisphere_ref) -> float:
    """Convert GPS degrees/minutes/seconds rationals to decimal degrees."""
    degrees = _rational_to_float(gps_dms[0])
    minutes = _rational_to_float(gps_dms[1])
    seconds = _rational_to_float(gps_dms[2])
    decimal = degrees + (minutes / 60.0) + (seconds / 3600.0)
    if isinstance(hemisphere_ref, bytes):
        hemisphere_ref = hemisphere_ref.decode("utf-8", errors="ignore")
    if hemisphere_ref.strip().upper() in ("S", "W"):
        decimal = -decimal
    return decimal


def _decode_bytes(value) -> str:
    """Safely decode a bytes tag value to a string."""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="ignore").strip("\x00").strip()
    return str(value).strip()


# ---------------------------------------------------------------------------
# PUBLIC FUNCTIONS
# ---------------------------------------------------------------------------

def extract_exif(image_bytes: bytes) -> dict:
    """
    Extract EXIF metadata from raw image bytes using piexif and Pillow.

    Returns a normalised dict with GPS coordinates, capture timestamp,
    software tag, and camera make/model. All fields default to None on
    any extraction failure so callers do not need to handle exceptions.
    """
    safe_defaults = {
        "gps_embedded":        False,
        "latitude":            None,
        "longitude":           None,
        "datetime_original":   None,
        "software":            None,
        "camera_make":         None,
        "camera_model":        None,
        "raw_exif_available":  False,
    }

    try:
        img = Image.open(io.BytesIO(image_bytes))
        raw_exif = img.info.get("exif")
        if not raw_exif:
            return safe_defaults

        exif_dict = piexif.load(raw_exif)
        safe_defaults["raw_exif_available"] = True

        # --- GPS ---
        gps_ifd = exif_dict.get("GPS", {})
        lat_dms = gps_ifd.get(piexif.GPSIFD.GPSLatitude)
        lat_ref = gps_ifd.get(piexif.GPSIFD.GPSLatitudeRef)
        lon_dms = gps_ifd.get(piexif.GPSIFD.GPSLongitude)
        lon_ref = gps_ifd.get(piexif.GPSIFD.GPSLongitudeRef)

        if lat_dms and lat_ref and lon_dms and lon_ref:
            safe_defaults["latitude"]    = round(_gps_to_decimal(lat_dms, lat_ref), 6)
            safe_defaults["longitude"]   = round(_gps_to_decimal(lon_dms, lon_ref), 6)
            safe_defaults["gps_embedded"] = True

        # --- DateTimeOriginal (0x9003) ---
        exif_ifd = exif_dict.get("Exif", {})
        dt_original = exif_ifd.get(0x9003)
        if dt_original:
            dt_str = _decode_bytes(dt_original)
            # EXIF datetime format: "YYYY:MM:DD HH:MM:SS"
            try:
                dt_parsed = datetime.strptime(dt_str, "%Y:%m:%d %H:%M:%S")
                safe_defaults["datetime_original"] = dt_parsed.strftime("%Y-%m-%dT%H:%M:%SZ")
            except ValueError:
                safe_defaults["datetime_original"] = dt_str

        # --- Software (0x0131), Make (0x010F), Model (0x0110) ---
        zeroth_ifd = exif_dict.get("0th", {})
        software = zeroth_ifd.get(0x0131)
        make     = zeroth_ifd.get(0x010F)
        model    = zeroth_ifd.get(0x0110)

        if software:
            safe_defaults["software"]     = _decode_bytes(software)
        if make:
            safe_defaults["camera_make"]  = _decode_bytes(make)
        if model:
            safe_defaults["camera_model"] = _decode_bytes(model)

    except Exception:
        return safe_defaults

    return safe_defaults


def check_geofence(
    latitude,
    longitude,
    claimed_mandal_id: str,
) -> dict:
    """
    Verify that photo GPS coordinates fall within the claimed mandal's
    bounding box (centroid ± 0.15°, approximately 15–17 km).

    Returns WARNING if GPS is absent, PASS/FAIL based on bounding box check.
    """
    if latitude is None or longitude is None:
        return {
            "status":                    "WARNING",
            "gps_embedded":              False,
            "gps_missing_note":          (
                "GPS metadata not embedded in photo. "
                "Manual coordinate entry required for geofence validation."
            ),
            "coordinates_inside_mandal": None,
        }

    mandal = get_mandal(claimed_mandal_id)
    c_lat  = mandal["centroid_lat"]
    c_lon  = mandal["centroid_lon"]
    radius = 0.15

    inside = (
        (c_lat - radius) <= float(latitude)  <= (c_lat + radius) and
        (c_lon - radius) <= float(longitude) <= (c_lon + radius)
    )

    lat_dist = abs(float(latitude)  - c_lat)
    lon_dist = abs(float(longitude) - c_lon)

    if inside:
        distance_note = (
            f"Coordinates ({latitude:.4f}, {longitude:.4f}) are within "
            f"{mandal['mandal_name']} mandal boundary (Δlat={lat_dist:.3f}°, "
            f"Δlon={lon_dist:.3f}°)."
        )
    else:
        distance_note = (
            f"Coordinates ({latitude:.4f}, {longitude:.4f}) are OUTSIDE "
            f"{mandal['mandal_name']} mandal boundary (Δlat={lat_dist:.3f}°, "
            f"Δlon={lon_dist:.3f}° — threshold ±0.15°)."
        )

    return {
        "status":                    "PASS" if inside else "FAIL",
        "gps_embedded":              True,
        "exif_lat":                  float(latitude),
        "exif_lon":                  float(longitude),
        "claimed_mandal":            mandal["mandal_name"],
        "centroid_lat":              c_lat,
        "centroid_lon":              c_lon,
        "coordinates_inside_mandal": inside,
        "distance_note":             distance_note,
    }


def check_timestamp(
    datetime_original_str,
    claimed_disaster_date_str: str,
    window_days_before: int = 2,
    window_days_after: int = 10,
) -> dict:
    """
    Validate that the photo's EXIF timestamp falls within a reasonable
    window around the claimed disaster date.

    Valid window: [disaster_date - window_days_before, disaster_date + window_days_after]
    Returns WARNING if no EXIF timestamp is available.
    """
    if datetime_original_str is None:
        return {
            "status":  "WARNING",
            "note":    (
                "No timestamp in EXIF. "
                "Cannot verify photo was taken after disaster."
            ),
        }

    try:
        # Handle both "YYYY-MM-DDTHH:MM:SSZ" and "YYYY-MM-DD" formats
        if "T" in datetime_original_str:
            photo_dt = datetime.strptime(
                datetime_original_str[:19], "%Y-%m-%dT%H:%M:%S"
            )
        else:
            photo_dt = datetime.strptime(datetime_original_str[:10], "%Y-%m-%d")

        disaster_dt = datetime.strptime(
            claimed_disaster_date_str[:10], "%Y-%m-%d"
        )

        window_start = disaster_dt - timedelta(days=window_days_before)
        window_end   = disaster_dt + timedelta(days=window_days_after)

        within_window = window_start <= photo_dt <= window_end
        days_from_disaster = (photo_dt.date() - disaster_dt.date()).days

        return {
            "status":             "PASS" if within_window else "FAIL",
            "photo_timestamp":    photo_dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "disaster_date":      disaster_dt.strftime("%Y-%m-%d"),
            "window_start":       window_start.strftime("%Y-%m-%dT00:00:00Z"),
            "window_end":         window_end.strftime("%Y-%m-%dT23:59:59Z"),
            "within_window":      within_window,
            "days_from_disaster": days_from_disaster,
        }

    except (ValueError, TypeError) as exc:
        return {
            "status":  "WARNING",
            "note":    f"Could not parse timestamp: {exc}",
        }


def check_edit_signature(software_str) -> dict:
    """
    Detect known image editing software in the EXIF Software tag.

    Flags Photoshop, Lightroom, GIMP, Snapseed, and other editing apps
    that indicate the image may have been manipulated.
    Returns PASS if no editing software is detected or Software tag is absent.
    """
    if software_str is None:
        return {
            "status":          "PASS",
            "editor_detected": None,
            "flag":            False,
        }

    lower = software_str.lower()
    for signature in _EDIT_SOFTWARE_SIGNATURES:
        if signature in lower:
            return {
                "status":          "FLAGGED",
                "editor_detected": software_str,
                "flag":            True,
                "note":            (
                    "Image editing software detected in metadata. "
                    "Manual review required."
                ),
            }

    return {
        "status":          "PASS",
        "editor_detected": None,
        "flag":            False,
    }


def run_full_fraud_check(
    image_bytes: bytes,
    claimed_mandal_id: str,
    claimed_disaster_date_str: str,
) -> dict:
    """
    Run the complete anti-fraud pipeline on an uploaded photo.

    Checks performed (in order):
      1. EXIF extraction      — GPS, timestamp, software, camera
      2. Geofence check       — photo location vs claimed mandal boundary
      3. Timestamp check      — photo date vs declared disaster window
      4. Edit signature check — editing software detection

    Overall status priority: FLAGGED > FAIL > WARNING > CLEAN
    """
    exif = extract_exif(image_bytes)

    geofence_result   = check_geofence(
        exif["latitude"], exif["longitude"], claimed_mandal_id
    )
    timestamp_result  = check_timestamp(
        exif["datetime_original"], claimed_disaster_date_str
    )
    edit_result       = check_edit_signature(exif["software"])

    statuses = {
        "geofence":  geofence_result["status"],
        "timestamp": timestamp_result["status"],
        "edit":      edit_result["status"],
    }

    if statuses["edit"] == "FLAGGED":
        overall_status = "FLAGGED"
        summary = (
            f"FLAGGED: Editing software '{exif['software']}' detected. "
            "Photo integrity cannot be confirmed."
        )
    elif "FAIL" in statuses.values():
        overall_status = "FAIL"
        failed = [k for k, v in statuses.items() if v == "FAIL"]
        summary = f"FAIL: Fraud check failed on {', '.join(failed)} validation."
    elif "WARNING" in statuses.values():
        overall_status = "WARNING"
        warned = [k for k, v in statuses.items() if v == "WARNING"]
        summary = (
            f"WARNING: Incomplete validation — {', '.join(warned)} check(s) "
            "could not be completed due to missing EXIF metadata."
        )
    else:
        overall_status = "CLEAN"
        summary = (
            "CLEAN: GPS within mandal boundary, timestamp within disaster "
            "window, no editing software detected."
        )

    return {
        "overall_status":       overall_status,
        "gps_embedded":         exif["gps_embedded"],
        "geofence_check":       geofence_result,
        "temporal_check":       timestamp_result,
        "edit_signature_check": edit_result,
        "summary":              summary,
    }
