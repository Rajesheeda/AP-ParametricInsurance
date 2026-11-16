"""POC photo verification (Module B): is this photo valid evidence for this parcel, crop and event?

Role (two-lane design): photos are evidence for Lane 2 (disaster relief / SDRF damage enumeration) and for the
basis-risk log. They NEVER change a Lane 1 insurance payout, which is decided by the index alone.

Checks, each reported separately:
  0. quality     - blur / exposure / resolution gate, thresholds measured on Department field photos (quality.py)
  1. geotag      - GPS from EXIF, or the phone's GPS read by the capture page at the moment of capture (browsers on
                   Android strip EXIF location from uploads) when its accuracy is within the median YSR parcel's
                   equivalent radius (measured from APAIMS cadastral); manual coordinates accepted but lower trust
  2. location    - pilot-district mandal (geoBoundaries ADM3); in YSR Kadapa the APAIMS cadastral parcel
  3. survey      - parcel survey number matches the claimed one (when claimed)
  4. booked crop - e-Panta crop(s) booked on that parcel for the season of the photo
  5. timing      - photo taken after the event started and within the verification window
  6. vision      - crop seen, damage class, confidence (zero-shot vision-language model, not a validated classifier)
  7. crop match  - crop seen agrees with the e-Panta booking
Verdict: RETAKE PHOTO / INVALID EVIDENCE (field visit) / PHOTO CONFIRMS LOSS / PHOTO DOES NOT CONFIRM LOSS.
"""
import io
import json
import sys
from datetime import datetime, timedelta
from functools import lru_cache
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
from PIL import Image
from shapely.geometry import Point

POC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(POC / "pipeline"))
from common import DERIVED, base_survey, norm_survey  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
import quality  # noqa: E402
from advisory import advice  # noqa: E402

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
    # live event (p25): its window and per-mandal lane decisions, same columns as the pilot assessment
    lf = DERIVED / "live_event_arnab.json"
    if lf.exists():
        e = json.loads(lf.read_text(encoding="utf-8"))["event"]
        events = pd.concat([events, pd.DataFrame([dict(id=e["id"], start=e["start"], end=e["end"], district_code="14")])])
        lm = pd.read_csv(DERIVED / "live_event_mandals.csv", dtype={"district_code": str})
        crops = {"14": ["Paddy"], "22": ["Cotton", "Red Chillies", "Paddy"], "11": ["Paddy", "Cotton", "Groundnut"], "10": ["Paddy", "Groundnut"]}
        lm = lm.assign(event_id=e["id"], mandal=lm.adm3_name, crop=lm.district_code.map(crops)).explode("crop")
        assess = pd.concat([assess, lm[["event_id", "district_code", "mandal", "crop", "lane1_decision", "lane1_payout_pct", "lane2_action"]]])
    return m, cad, ep, events, assess


@lru_cache(maxsize=1)
def gps_accuracy_limit_m():
    """Equivalent radius of the median YSR cadastral parcel (m): a device fix less precise than this cannot place
    the photo in one parcel."""
    cad = layers()[1]
    a = cad.geometry.to_crs(32644).area.median()
    return float(np.sqrt(a / np.pi))


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
           taken=None, vision=None, gps_source=None, gps_accuracy_m=None):
    """vision: callable(image_bytes, crop) -> dict (the backend's assess_photo). None skips the vision step."""
    m, cad, ep, events, assess = layers()
    checks, ctx = [], {}
    ex = read_exif(image_bytes)
    try:
        q = quality.check(Image.open(io.BytesIO(image_bytes)).convert("RGB"))
    except Exception as e:  # unreadable file
        q = dict(ok=False, detail=f"unreadable image ({type(e).__name__})", measures=None)
    checks.append(dict(check="photo quality", ok=q["ok"], detail=q["detail"],
                       note="limits = percentiles of the Department's own field photos"))

    # 1. geotag
    dev_note = None
    if ex["lat"] is not None:
        lat, lon, src = ex["lat"], ex["lon"], "EXIF"
    elif lat is not None and lon is not None and gps_source == "device" and gps_accuracy_m is not None:
        lim = gps_accuracy_limit_m()
        src = "device" if gps_accuracy_m <= lim else "manual"
        dev_note = (f"phone GPS at capture, accuracy {gps_accuracy_m:.0f} m (limit {lim:.0f} m = median parcel radius)"
                    + ("" if src == "device" else ": too coarse to place the photo in one parcel, treated as manual"))
    elif lat is not None and lon is not None:
        src = "manual"
    else:
        src = None
    checks.append(dict(check="geotag", ok=src in ("EXIF", "device"),
                       detail=f"{src} {lat:.5f}, {lon:.5f}" if src else "no GPS in photo and none entered",
                       note=dev_note if dev_note
                       else None if src == "EXIF" else "manual coordinates: lower trust" if src else None))
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
    # a photo refused by the quality gate is not analysed: no crop, damage or pest reading from an unusable image
    vis = vision(image_bytes, "Unknown (identify it from the photo)") if vision and q["ok"] else None
    if vision and not q["ok"]:
        checks.append(dict(check="vision model", ok=None, detail="not run: photo refused by the quality gate"))
    if vis and (vis.get("fallback_used") == "rule_based" or "fallback" in str(vis.get("analysis_source", "")).lower()):
        # the demo engine's rule-based fallback echoes the expected crop and a fixed damage value: never evidence
        checks.append(dict(check="vision model", ok=None, detail="vision service unavailable: no image analysis was done"))
        vis = None
        vision_down = True
    else:
        vision_down = False
    if vis:
        checks.append(dict(check="vision model", ok=True, detail=f"{vis.get('crop_identified')} · {vis.get('damage_class')} · "
                           f"confidence {vis.get('confidence_score', 0):.2f} · photo loss estimate "
                           f"{vis.get('estimated_photo_loss_pct', '–')}% · {vis.get('analysis_source')}",
                           note="general vision model, measured on 218 Department photos of diseased paddy / cotton: "
                                "called 90% of them damaged (CI 85-93%); its false-alarm rate on healthy crop and its loss % "
                                "are unmeasured (no healthy or severity labels exist), so the officer confirms the >= 33% SDRF line"))
        target = booked or ([claimed_crop] if claimed_crop else [])
        if target:
            match = any(crop_matches(vis.get("crop_identified"), c) for c in target)
            checks.append(dict(check="crop match", ok=match, detail=f"seen '{vis.get('crop_identified')}' vs "
                               + ("booked " if booked else "claimed ") + ", ".join(target)))

    # pest / disease suggestion from the trained classifier (informational; never part of the verdict)
    sug = pest_suggestion(image_bytes) if vis else None
    adv = None
    if sug:
        checks.append(dict(check="pest/disease (trained model)", ok=None,
                           detail="; ".join(f"{s['label']} {s['prob']:.0%}" for s in sug),
                           note="suggestion for the officer: 60% held-out accuracy on 8 post-flood paddy/cotton classes"))
        adv = advice(sug[0]["label"])

    # verdict
    hard = [c for c in checks if c["check"] in ("location", "survey number", "timing", "crop match", "e-Panta booking") and c["ok"] is False]
    if q["ok"] is False:
        verdict = "RETAKE PHOTO: " + q["detail"]
    elif not src or hard:
        verdict = "INVALID EVIDENCE: FIELD VISIT"
    elif vis is None:
        verdict = "CHECKS PASSED: VISION UNAVAILABLE, FIELD VISIT" if vision_down else "CHECKS PASSED: VISION PENDING"
    elif vis.get("damage_class") in ("Partially Damaged", "Severely Damaged"):
        # typed-in coordinates can be copied from any parcel, so they cannot confirm a loss on their own
        verdict = "PHOTO CONFIRMS LOSS" if src in ("EXIF", "device") else "PHOTO SHOWS DAMAGE: MANUAL GPS, OFFICER TO VERIFY"
    else:
        verdict = "PHOTO DOES NOT CONFIRM LOSS"
    case = None
    if ev is not None and "mandal" in ctx:
        a = assess[(assess.event_id == event_id) & (assess.mandal == ctx["mandal"])]
        keep = [c for c in ["crop", "lane1_decision", "lane1_payout_pct", "lane2_action"] if c in a]
        case = a[keep].to_dict("records")
    resolution = None
    if case:
        rows = [c for c in case if not expect or c["crop"] == expect] or case
        paid = any(str(c.get("lane1_decision")).startswith("INDEX PAYOUT") for c in rows)
        ins = ("Insurance (Lane 1) is decided by the index only and is unchanged: "
               + ("index payout " + ", ".join(f"{c['crop']} {c['lane1_payout_pct']:.0f}%" for c in rows if str(c.get("lane1_decision")).startswith("INDEX PAYOUT"))
                  if paid else "no index payout" + (" yet (awaiting radar)" if any(c.get("lane1_decision") == "AWAITING RADAR" for c in rows) else "")) + ".")
        if verdict.startswith("RETAKE"):
            resolution = "Photo rejected before any check: farmer asked to retake it in the app. " + ins
        elif verdict.startswith("INVALID"):
            resolution = "Relief (Lane 2): photo not usable, AEO enumeration visit. " + ins
        elif verdict == "PHOTO CONFIRMS LOSS":
            resolution = ("Relief (Lane 2): damage evidence recorded for SDRF enumeration. " + ins
                          + ("" if paid else " Loss seen where the index did not pay: logged as a basis-risk case for recalibration."))
        elif verdict.startswith("PHOTO SHOWS DAMAGE: MANUAL GPS"):
            resolution = "Relief (Lane 2): damage visible but location typed by hand, AEO to verify before enumeration. " + ins
        elif verdict == "PHOTO DOES NOT CONFIRM LOSS":
            resolution = ("Relief (Lane 2): no damage evidence for enumeration. " + ins
                          + (" Index paid where the photo shows no loss: logged as a basis-risk case for recalibration." if paid else ""))
    rec = dict(time=datetime.now().isoformat(timespec="seconds"), event_id=event_id, lat=lat, lon=lon, gps_source=src,
               taken=taken.isoformat() if taken else None, context=ctx, checks=checks, verdict=verdict,
               estimated_photo_loss_pct=vis.get("estimated_photo_loss_pct") if vis else None,
               disease=vis.get("disease_details") if vis else None, advisory=adv, case=case, resolution=resolution)
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
