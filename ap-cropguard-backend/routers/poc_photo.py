"""POC photo verification endpoints (Module B). Logic lives in poc/photo/verify.py."""
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from engines.photo_engine import assess_photo

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "poc" / "photo"))
import verify as V  # noqa: E402

router = APIRouter(prefix="/poc/photo", tags=["poc-photo"])
MAX_BYTES = 15 * 1024 * 1024


def ok(data):
    return {"success": True, "data": data, "error": None,
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}


@router.post("/verify")
async def post_verify(file: UploadFile = File(...), event_id: Optional[str] = Form(None),
                      claimed_crop: Optional[str] = Form(None), claimed_survey: Optional[str] = Form(None),
                      lat: Optional[float] = Form(None), lon: Optional[float] = Form(None),
                      taken: Optional[str] = Form(None)):
    data = await file.read()
    if not data or len(data) > MAX_BYTES:
        raise HTTPException(400, "Photo is empty or larger than 15 MB.")
    if data[:3] != b"\xff\xd8\xff" and data[:4] != b"\x89PNG":
        raise HTTPException(400, "Only JPEG or PNG photos are accepted.")
    rec = V.verify(data, claimed_crop=claimed_crop or None, claimed_survey=claimed_survey or None, lat=lat, lon=lon,
                   event_id=event_id or None, taken=taken or None, vision=assess_photo)
    return ok(rec)


@router.get("/log")
def get_log(limit: int = 50):
    return ok(V.evidence_log(min(max(limit, 1), 500)))
