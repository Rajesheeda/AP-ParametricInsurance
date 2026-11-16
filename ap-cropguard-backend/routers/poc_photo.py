"""POC photo verification endpoints (Module B). Logic lives in poc/photo/verify.py."""
import sys
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from engines.photo_engine import assess_photo

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "poc" / "photo"))
import verify as V  # noqa: E402

router = APIRouter(prefix="/poc/photo", tags=["poc-photo"])


def _warm():
    """Load mandals, cadastral, e-Panta and the pest model in the background so the first photo is not slow."""
    try:
        V.layers()
        V.gps_accuracy_limit_m()
        V.pest_suggestion(b"")
    except Exception:
        pass


threading.Thread(target=_warm, daemon=True).start()
MAX_BYTES = 15 * 1024 * 1024


def ok(data):
    return {"success": True, "data": data, "error": None,
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}


@router.post("/verify")
async def post_verify(file: UploadFile = File(...), event_id: Optional[str] = Form(None),
                      claimed_crop: Optional[str] = Form(None), claimed_survey: Optional[str] = Form(None),
                      lat: Optional[float] = Form(None), lon: Optional[float] = Form(None),
                      taken: Optional[str] = Form(None), gps_source: Optional[str] = Form(None),
                      gps_accuracy: Optional[float] = Form(None)):
    data = await file.read()
    if not data or len(data) > MAX_BYTES:
        raise HTTPException(400, "Photo is empty or larger than 15 MB.")
    if data[:3] != b"\xff\xd8\xff" and data[:4] != b"\x89PNG":
        raise HTTPException(400, "Only JPEG or PNG photos are accepted.")
    rec = V.verify(data, claimed_crop=claimed_crop or None, claimed_survey=claimed_survey or None, lat=lat, lon=lon,
                   event_id=event_id or None, taken=taken or None, vision=assess_photo,
                   gps_source=gps_source or None, gps_accuracy_m=gps_accuracy)
    return ok(rec)


@router.get("/log")
def get_log(limit: int = 50):
    return ok(V.evidence_log(min(max(limit, 1), 500)))


@router.get("/events")
def get_events():
    """Events a photo can be filed against (live event first), for the phone capture page."""
    ev = V.layers()[3].sort_values("start", ascending=False)
    names = {"14": "Parvathipuram Manyam", "22": "Palnadu", "11": "YSR Kadapa", "10": "Chittoor"}
    out = [dict(id=r.id, start=str(r.start)[:10], district=names.get(str(r.district_code), str(r.district_code)),
                live=str(r.id).startswith("ARNAB"),
                name=("Cyclone Arnab" if str(r.id).startswith("ARNAB") else f"Cyclone {r.cyclone.title()}"
                      if isinstance(r.cyclone, str) else str(r.types).replace("_", " ").replace("+", " + ")))
           for r in ev.itertuples()]
    out.sort(key=lambda x: not x["live"])
    return ok(dict(events=out[:25], gps_accuracy_limit_m=round(V.gps_accuracy_limit_m())))
