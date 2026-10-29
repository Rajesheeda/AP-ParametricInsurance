"""POC Lane 1 per-farmer payout look-up. Data: poc/data/derived/farmer_payouts.parquet (p23, gitignored)."""
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Optional

import pandas as pd
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/poc/farmer", tags=["poc-farmer"])
SRC = Path(__file__).resolve().parents[2] / "poc" / "data" / "derived" / "farmer_payouts.parquet"
COLS = ["mandal", "village_en", "survey", "crop_name", "sowing_date", "area", "year", "covered", "coverA_pct", "calendar_pct",
        "vci", "coverA_paid", "coverB_pct", "coverB_event", "total_pct"]


def ok(data):
    return {"success": True, "data": data, "error": None,
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}


@lru_cache(maxsize=1)
def table():
    if not SRC.exists():
        raise HTTPException(503, "Farmer payouts not built: run poc/pipeline/p23_farmer_payouts.py")
    d = pd.read_parquet(SRC)[COLS]
    d["sowing_date"] = d.sowing_date.astype(str).str[:10]
    d["survey"] = d.survey.astype(str)
    return d


@router.get("/villages")
def villages(mandal: str, year: int):
    d = table()
    d = d[(d.mandal == mandal) & (d.year == year)]
    return ok(sorted(d.village_en.dropna().astype(str).unique()))


@router.get("/payouts")
def payouts(mandal: str, year: int, village: Optional[str] = None, survey: Optional[str] = None, limit: int = 200):
    d = table()
    d = d[(d.mandal == mandal) & (d.year == year)]
    if village:
        d = d[d.village_en == village]
    if survey:
        d = d[d.survey.str.upper().str.contains(survey.strip().upper(), regex=False)]
    d = d.sort_values(["total_pct", "village_en"], ascending=[False, True])
    summary = dict(bookings=int(len(d)), acres=float(d.area.sum()), paid=int((d.total_pct > 0).sum()),
                   payout_acres=float((d.area * d.total_pct / 100).sum()))
    rows = d.head(min(max(limit, 1), 1000)).astype(object).where(d.head(min(max(limit, 1), 1000)).notna(), None)
    return ok(dict(summary=summary, rows=rows.to_dict("records")))
