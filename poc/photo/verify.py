"""POC photo verification (Module B): is this photo valid evidence for this parcel, crop and event?

Checks, each reported separately:
  1. geotag      - GPS from EXIF (manual coordinates accepted but marked lower trust)
  2. location    - pilot-district mandal (geoBoundaries ADM3); in YSR Kadapa the APAIMS cadastral parcel
  3. survey      - parcel survey number matches the claimed one (when claimed)
  4. booked crop - e-Panta crop(s) booked on that parcel for the season of the photo
  5. timing      - photo taken after the event started and within the verification window
  6. vision      - crop seen, damage class, confidence (zero-shot vision-language model, not a validated classifier)
  7. crop match  - crop seen agrees with the e-Panta booking
Verdict: INVALID EVIDENCE (field visit) / PHOTO CONFIRMS LOSS / PHOTO DOES NOT CONFIRM LOSS.
"""
import io
import json
import sys
from datetime import datetime, timedelta
from functools import lru_cache
from pathlib import Path

import geopandas as gpd
import pandas as pd
from PIL import Image
from shapely.geometry import Point

POC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(POC / "pipeline"))
from common import DERIVED, base_survey, norm_survey  # noqa: E402

LOG = POC / "data" / "photo_evidence.jsonl"
VERIFY_WINDOW_DAYS = 30   # policy setting: photos accepted from event start to 30 days after event end
CROP_ALIASES = {
    "Paddy": ["paddy", "rice"],
    "Cotton": ["cotton"],
    "Red Chillies": ["chilli", "chili", "pepper", "capsicum"],
    "Groundnut": ["groundnut", "peanut"],
    "Red gram": ["red gram", "pigeon pea", "pigeonpea", "tur", "arhar"],
    "Black gram": ["black gram", "urad"],
    "Maize": ["maize", "corn"],
    "Banana": ["banana"],
    "Mango": ["mango"],
    "Sweet Orange": ["sweet orange", "orange", "citrus", "mosambi"],
}


@lru_cache(maxsize=1)
def layers():
    m = gpd.read_file(DERIVED / "poc_mandals.geojson")
    m = m[m.ok].drop_duplicates("adm3_id")
    cad = pd.read_parquet(DERIVED / "ysr_cadastral_farm.parquet")
    cad = gpd.GeoDataFrame(cad.drop(columns="geometry"), geometry=gpd.GeoSeries.from_wkb(cad.geometry), crs=4326)
    ep = pd.read_parquet(DERIVED / "ysr_epanta_parcel_join.parquet",
                         columns=["cv", "sv", "sb", "season", "year", "crop_name", "variety", "sowing_date", "area"])
    events = pd.read_csv(DERIVED / "flood_events_gee3.csv", dtype={"district_code": str})
    assess = pd.read_csv(DERIVED / "assessment_pilot.csv", dtype={"district_code": str})
    return m, cad, ep, events, assess


def _dms(v):
    d, mi, s = (float(x) for x in v)
    return d + mi / 60 + s / 3600


def read_exif(image_bytes):
    out = {"lat": None, "lon": None, "taken": None}
    try:
        img = Image.open(io.BytesIO(image_bytes))
        ex = img.getexif()
        gps = ex.get_ifd(0x8825)
        if gps and 2 in gps and 4 in gps:
            lat, lon = _dms(gps[2]), _dms(gps[4])
            out["lat"] = -lat if gps.get(1) == "S" else lat
            out["lon"] = -lon if gps.get(3) == "W" else lon
        t = ex.get_ifd(0x8769).get(36867) or ex.get(306)
        if t:
            out["taken"] = datetime.strptime(str(t), "%Y:%m:%d %H:%M:%S")
    except Exception:
        pass
    return out


def seasons_of(dt):
    """Seasons whose crops can be in the field on this date (Kharif Jun-Jan, Rabi Oct-Mar)."""
    out = []
    if dt.month >= 6 or dt.month == 1:
        out.append(("Kharif", dt.year if dt.month >= 6 else dt.year - 1))
    if dt.month >= 10 or dt.month <= 3:
        out.append(("Rabi", dt.year if dt.month >= 10 else dt.year - 1))
    return out


def crop_matches(seen, booked):
    s = (seen or "").lower()
    return any(a in s for a in CROP_ALIASES.get(booked, [booked.lower()]))


def verify(image_bytes, claimed_crop=None, claimed_survey=None, lat=None, lon=None, event_id=None,
           taken=None, vision=None):
    """vision: callable(image_bytes, crop) -> dict (the backend's assess_photo). None skips the vision step."""
    m, cad, ep, events, assess = layers()
    checks, ctx = [], {}
    ex = read_exif(image_bytes)

    # 1. geotag
    if ex["lat"] is not None:
        lat, lon, src = ex["lat"], ex["lon"], "EXIF"
    elif lat is not None and lon is not None:
        src = "manual"
    else:
        src = None
    checks.append(dict(check="geotag", ok=src == "EXIF",
                       detail=f"{src} {lat:.5f}, {lon:.5f}" if src else "no GPS in photo and none entered",
                       note=None if src == "EXIF" else "manual coordinates: lower trust" if src else None))
    taken = ex["taken"] or (pd.Timestamp(taken).to_pydatetime() if taken else None)

    # 2. location
    mandal = parcel = None
    if src:
        pt = Point(lon, lat)
        hit = m[m.contains(pt)]
        if len(hit):
            mandal = hit.iloc[0]
            ctx.update(district_code=mandal.district_code, mandal=mandal.adm3_name, adm3_id=mandal.adm3_id)
        ph = cad.iloc[list(cad.sindex.query(pt, predicate="within"))] if mandal is not None and mandal.district_code == "11" else cad.iloc[0:0]
        if len(ph):
            parcel = ph.iloc[0]
            ctx.update(survey=parcel.parcel_num, village=parcel.VILL_NAME, cadastral_mandal=parcel.MANDAL_NM)
    checks.append(dict(check="location", ok=mandal is not None,
                       detail=(f"{ctx['mandal']} mandal" + (f", parcel {ctx['survey']} ({ctx['village']})" if parcel is not None else
                               " (no cadastral parcel here)" if mandal is not None and mandal.district_code == "11" else
                               " (parcel boundaries not available for this district)")) if mandal is not None
                       else "outside the POC districts"))

    # 3. survey number
    if claimed_survey:
        ok = parcel is not None and (norm_survey(claimed_survey) == parcel.sv or base_survey(claimed_survey) == parcel.sb)
        checks.append(dict(check="survey number", ok=ok, detail=f"claimed {claimed_survey}; photo falls in "
                           + (str(parcel.parcel_num) if parcel is not None else "no known parcel")))

    # 4. booked crop
    booked = []
    if parcel is not None and taken:
        ss = seasons_of(taken)
        b = ep[(ep.cv == parcel.cv) & (ep.sb == parcel.sb)
               & pd.Series(list(zip(ep.season, ep.year)), index=ep.index).isin(ss)]
        booked = sorted(b.crop_name.dropna().unique())
        ctx.update(season=" / ".join(f"{a} {y}" for a, y in ss), booked_crops=booked)
    checks.append(dict(check="e-Panta booking", ok=bool(booked) if parcel is not None else None,
                       detail=", ".join(booked) if booked else "no booking found" if parcel is not None else "needs a cadastral parcel"))

    # 5. timing
    ev = events[events.id == event_id].iloc[0] if event_id and (events.id == event_id).any() else None
    if ev is not None and taken:
        s, e = pd.Timestamp(ev.start), pd.Timestamp(ev.end) + timedelta(days=VERIFY_WINDOW_DAYS)
        checks.append(dict(check="timing", ok=bool(s <= pd.Timestamp(taken) <= e),
                           detail=f"taken {taken:%Y-%m-%d %H:%M}; window {s.date()} to {e.date()}"))
    else:
        checks.append(dict(check="timing", ok=None, detail="no event selected" if ev is None else "no timestamp in photo"))

    # 6-7. vision + crop match
    expect = claimed_crop or (booked[0] if booked else None)
    # Blind identification: the model is NOT told the claimed / booked crop, otherwise it tends to echo it
    # (a plain green image was reported as "Paddy, healthy, 0.96" when the prompt named Paddy).
    vis = vision(image_bytes, "Unknown (identify it from the photo)") if vision else None
    if vis and (vis.get("fallback_used") == "rule_based" or "fallback" in str(vis.get("analysis_source", "")).lower()):
        # the demo engine's rule-based fallback echoes the expected crop and a fixed damage value: never evidence
        checks.append(dict(check="vision model", ok=None, detail="vision service unavailable: no image analysis was done"))
        vis = None
        vision_down = True
    else:
        vision_down = False
    if vis:
        checks.append(dict(check="vision model", ok=True, detail=f"{vis.get('crop_identified')} · {vis.get('damage_class')} · "
                           f"confidence {vis.get('confidence_score', 0):.2f} · {vis.get('analysis_source')}"))
        target = booked or ([claimed_crop] if claimed_crop else [])
        if target:
            match = any(crop_matches(vis.get("crop_identified"), c) for c in target)
            checks.append(dict(check="crop match", ok=match, detail=f"seen '{vis.get('crop_identified')}' vs "
                               + ("booked " if booked else "claimed ") + ", ".join(target)))

    # pest / disease suggestion from the trained classifier (informational; never part of the verdict)
    sug = pest_suggestion(image_bytes) if vis else None
    if sug:
        checks.append(dict(check="pest/disease (trained model)", ok=None,
                           detail="; ".join(f"{s['label']} {s['prob']:.0%}" for s in sug),
                           note="suggestion for the officer: 60% held-out accuracy on 8 post-flood paddy/cotton classes"))

    # verdict
    hard =[c for c in checks if c["check"] in ("location", "survey number", "timing", "crop match", "e-Panta booking") and c["ok"] is False]
    if not src or hard:
        verdict = "INVALID EVIDENCE: FIELD VISIT"
    elif vis is None:
        verdict = "CHECKS PASSED: VISION UNAVAILABLE, FIELD VISIT" if vision_down else "CHECKS PASSED: VISION PENDING"
    elif vis.get("damage_class") in ("Partially Damaged", "Severely Damaged"):
        # typed-in coordinates can be copied from any parcel, so they cannot confirm a loss on their own
        verdict = "PHOTO CONFIRMS LOSS" if src == "EXIF" else "PHOTO SHOWS DAMAGE: MANUAL GPS, OFFICER TO VERIFY"
    else:
        verdict = "PHOTO DOES NOT CONFIRM LOSS"
    case = None
    if ev is not None and "mandal" in ctx:
        a = assess[(assess.event_id == event_id) & (assess.mandal == ctx["mandal"])]
        case = a[["crop", "action"]].to_dict("records")
    resolution = None
    if case:
        acts = {c["action"] for c in case if not expect or c["crop"] == expect} or {c["action"] for c in case}
        if verdict.startswith("INVALID"):
            resolution = "Evidence not usable: send field officer."
        elif verdict == "PHOTO CONFIRMS LOSS":
            resolution = ("Loss confirmed by photo: case can be closed for payment." if "FIELD / PHOTO VERIFICATION" in acts else
                          "Photo contradicts 'no payout': refer for field verification (basis-risk catch)." if "NO PAYOUT" in acts else
                          "Consistent with parametric payout.")
        elif verdict.startswith("PHOTO SHOWS DAMAGE: MANUAL GPS"):
            resolution = "Damage visible but location typed in by hand: AEO to verify the field before any payment."
        elif verdict == "PHOTO DOES NOT CONFIRM LOSS":
            resolution = ("Photo shows no damage: verification case closed without payment." if "FIELD / PHOTO VERIFICATION" in acts else
                          "Photo contradicts payout: flag for audit." if "PARAMETRIC PAYOUT" in acts else "Consistent with no payout.")
    rec = dict(time=datetime.now().isoformat(timespec="seconds"), event_id=event_id, lat=lat, lon=lon, gps_source=src,
               taken=taken.isoformat() if taken else None, context=ctx, checks=checks, verdict=verdict,
               estimated_photo_loss_pct=vis.get("estimated_photo_loss_pct") if vis else None,
               disease=vis.get("disease_details") if vis else None, case=case, resolution=resolution)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, default=str, ensure_ascii=False) + "\n")
    return rec


_PEST = {}


def pest_suggestion(image_bytes, top=3):
    """Top-k suggestions from the classifier trained on the Department's labelled images (pest_train.py).
    Held-out accuracy 60% over 8 post-flood paddy/cotton classes; a suggestion for the officer, not a diagnosis."""
    mdl_f = POC / "data" / "pest_model" / "model.joblib"
    if not mdl_f.exists():
        return None
    if not _PEST:
        import joblib
        import torch
        from torchvision import models, transforms
        net = models.efficientnet_b0(weights=models.EfficientNet_B0_Weights.DEFAULT)
        net.classifier = torch.nn.Identity()
        net.eval()
        _PEST.update(torch=torch, net=net, model=joblib.load(mdl_f), tf=transforms.Compose([
            transforms.Resize(320), transforms.CenterCrop(320), transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])]))
    t = _PEST["torch"]
    with t.no_grad():
        x = _PEST["net"](_PEST["tf"](Image.open(io.BytesIO(image_bytes)).convert("RGB")).unsqueeze(0)).numpy()
    clf = _PEST["model"]["clf"]
    p = clf.predict_proba(x)[0]
    order = p.argsort()[::-1][:top]
    return [dict(label=str(clf.classes_[i]).replace("_", " "), prob=float(p[i])) for i in order]


def evidence_log(limit=50):
    if not LOG.exists():
        return []
    lines = LOG.read_text(encoding="utf-8").strip().splitlines()
    return [json.loads(x) for x in lines[-limit:]][::-1]
