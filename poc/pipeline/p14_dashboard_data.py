"""Build the POC dashboard: one self-contained HTML file with the data embedded (mandal-level aggregates only).
Output goes to poc/data/dashboard/ (gitignored: derived from department data)."""
import glob
import json

import geopandas as gpd
import numpy as np
import pandas as pd
from scipy.stats import spearmanr

from common import DERIVED, POC

OUT = POC / "data" / "dashboard"
OUT.mkdir(parents=True, exist_ok=True)
DIST = {"22": "Palnadu", "11": "YSR Kadapa", "14": "Parvathipuram Manyam", "10": "Chittoor"}


def clean(o):
    if isinstance(o, dict):
        return {k: clean(v) for k, v in o.items()}
    if isinstance(o, list):
        return [clean(v) for v in o]
    if isinstance(o, (np.floating, float)):
        return None if np.isnan(o) else round(float(o), 3)
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.bool_,)):
        return bool(o)
    if isinstance(o, (pd.Timestamp,)):
        return str(o.date())
    return o


pil = pd.read_csv(DERIVED / "pilot_mandals.csv", dtype={"district_code": str})
geo = gpd.read_file(DERIVED / "poc_mandals.geojson")
geo = geo[geo.adm3_id.isin(pil.adm3_id)].drop_duplicates("adm3_id")
geo["geometry"] = geo.geometry.simplify(0.002)
mandals = json.loads(geo[["adm3_id", "adm3_name", "district_code", "geometry"]].to_json())
# all POC-district mandals as context for the offline SVG map (no tiles, no map library)
ctx = gpd.read_file(DERIVED / "poc_mandals.geojson")
ctx = ctx[ctx.ok].drop_duplicates("adm3_id")
ctx["geometry"] = ctx.geometry.simplify(0.004)
ctx_mandals = json.loads(ctx[["adm3_id", "adm3_name", "district_code", "geometry"]].to_json())

a = pd.read_csv(DERIVED / "assessment_pilot.csv", dtype={"district_code": str})
ev = pd.read_csv(DERIVED / "flood_events_gee3.csv", dtype={"district_code": str})
fl = pd.concat([pd.read_parquet(f) for f in glob.glob(str(POC / "data" / "gee_out" / "out_flood_mandal_*.parquet"))])
fl = fl[~fl.event_id.str.startswith("CTRL_")]
# each mandal has its own pass; NOT IMAGED mandals carry no time, so take the earliest pass over imaged rows
fl["post_ts"] = pd.to_datetime(fl.post_image_time, errors="coerce")
fl["hours_after_event_end"] = pd.to_numeric(fl.hours_after_event_end, errors="coerce")
fe = fl.groupby("event_id").agg(post_ts=("post_ts", "min"), hours=("hours_after_event_end", "min"),
                                orbit_matched=("orbit_matched", "first"), t_post=("t_post_db", "first"),
                                flood_ha=("crop_flood_ha", "sum"), crop_ha=("cropland_ha", "sum"),
                                mandals=("mid", "size"), imaged=("imaged", "sum")).reset_index()
fe["post"] = fe.post_ts.dt.strftime("%Y-%m-%d %H:%M")
fe = fe.drop(columns="post_ts")
fe["within_72h"] = fe.hours <= 72

trig = pd.read_parquet(DERIVED / "trigger_annual_payouts.parquet")
burn = (trig[trig.year.between(1995, 2024)].groupby(["district_code", "crop"]).agg(
    burn_cost_pct=("pay_pct", "mean"), payout_freq=("pay_pct", lambda s: (s > 0).mean())).reset_index())
pilot_pay = trig[trig.adm3_id.isin(pil.adm3_id) & (trig.year >= 2015)].merge(pil[["adm3_id", "adm3_name"]], on="adm3_id")

val = pd.read_csv(DERIVED / "validation_trigger_vs_vci.csv", dtype={"dist": str})
vstats = []
for label, df in [("All Kharif seasons", val), ("Deficit / dry-spell driven", val[val.driver.isin(["deficit", "dry"])])]:
    rho, p = spearmanr(df.S, df.vci)
    fired, stressed = df.pay > 0, df.vci < 35
    vstats.append(dict(scope=label, level="mandal-season", n=len(df), spearman=rho, p=p,
                       pod=(fired & stressed).sum() / max(1, stressed.sum()), far=(fired & ~stressed).sum() / max(1, fired.sum())))
dy = val.groupby(["dist", "year"]).agg(S=("S", "mean"), vci=("vci", "mean")).reset_index()
for d, sub in dy.groupby("dist"):
    rho, p = spearmanr(sub.S, sub.vci)
    vstats.append(dict(scope=DIST.get(d, d), level="district-year", n=len(sub), spearman=rho, p=p, pod=None, far=None))

cross = pd.read_parquet(DERIVED / "crosscheck_michaung_2023.parquet")
flagged = cross[cross.flood_frac > 0]
crosscheck = dict(event="Cyclone Michaung, YSR Kadapa, Dec 2023", parcels=len(cross), flagged=len(flagged),
                  standing=int(flagged.standing.sum()), gated_out=int((~flagged.standing).sum()),
                  anom_flagged_standing=float(flagged[flagged.standing].anom.median()),
                  anom_unflagged=float(cross[cross.flood_frac == 0].anom.median()))

pc = None
pcf = sorted(glob.glob(str(POC / "data" / "gee_out" / "out_PC_*.parquet")))
if len(pcf) == 3:
    d = pd.concat([pd.read_parquet(f) for f in pcf])
    d["share"] = 100 * d.crop_flood_ha / d.cropland_ha
    evd = d[d.event_id == "PC_BUDAMERU_2024"].copy()
    ctl = d[d.event_id != "PC_BUDAMERU_2024"]
    evd["ctrl"] = evd.unit.map(ctl.groupby("unit").share.max())
    pc = dict(event_share=100 * evd.crop_flood_ha.sum() / evd.cropland_ha.sum(),
              ctrl_share=max(100 * g.crop_flood_ha.sum() / g.cropland_ha.sum() for _, g in ctl.groupby("event_id")),
              post=evd.post_image_time.iloc[0], hours=float(evd.hours_after_event_end.iloc[0]),
              units=evd.sort_values("share", ascending=False)[["unit", "dist_km", "share", "ctrl"]].head(6).to_dict("records"))

cce_f = DERIVED / "validation_cce_summary.json"
cce = json.loads(cce_f.read_text(encoding="utf-8")) if cce_f.exists() else None

def _json(name):
    f = DERIVED / name
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else None


alerts_f = DERIVED / "alerts.csv"
alerts = pd.read_csv(alerts_f, dtype={"district_code": str}).to_dict("records") if alerts_f.exists() else []

# real images (p21): Sentinel-2 / Sentinel-1 thumbnails and Department field photos, embedded as data URIs
import base64  # noqa: E402

IMGDIR = OUT / "img"
media, img = None, {}
if (IMGDIR / "manifest.json").exists():
    media = json.loads((IMGDIR / "manifest.json").read_text(encoding="utf-8"))
    for f in IMGDIR.glob("*.jpg"):
        img[f.name] = "data:image/jpeg;base64," + base64.b64encode(f.read_bytes()).decode()

pm_f = POC / "data" / "pest_model" / "metrics.json"
pest_model = json.loads(pm_f.read_text(encoding="utf-8")) if pm_f.exists() else None
if pest_model:
    pest_model = {k: pest_model[k] for k in ("test_accuracy", "ci95", "n_test", "n_train", "removed_near_duplicates",
                                             "gemini_same_images", "model_same_images", "mcnemar_p") if k in pest_model}

# Lane 1 per-farmer payouts (p23): one row per e-Panta booking, short keys to keep the file small
# per-booking look-up is served by the backend (GET /api/v1/poc/farmer/payouts); only the summary is embedded
farmers = None
pq_f = POC / "data" / "photo_quality.json"
cat_f = DERIVED / "cat_cover_events.csv"

data = dict(
    dual=_json("dual_trigger_validation.json"),
    premium=_json("premium_lane1.json"),
    power=_json("evidence_power.json"),
    live=_json("live_event_arnab.json"),
    comp=_json("compensation.json"),
    wbcis=_json("wbcis.json"),
    farmer_summary=_json("farmer_payouts_summary.json"),
    farmers=farmers,
    cat_events=pd.read_csv(cat_f).replace({np.nan: None}).to_dict("records") if cat_f.exists() else [],
    photo_quality=json.loads(pq_f.read_text(encoding="utf-8")) if pq_f.exists() else None,
    pest_model=pest_model,
    media=media,
    img=img,
    soil=_json("validation_soil_summary.json"),
    loss_cal=_json("loss_calibration.json"),
    alerts=alerts,
    cce=cce,
    positive_control=pc,
    generated=str(pd.Timestamp.now().date()),
    districts=DIST,
    pilot=pil[["district_code", "season", "adm3_name", "adm3_id", "focus_ac", "n_events", "parcel_cov"]].to_dict("records"),
    mandals=mandals,
    ctx_mandals=ctx_mandals,
    events=ev[["id", "district_code", "start", "end", "types", "cyclone"]].merge(fe, left_on="id", right_on="event_id", how="left").to_dict("records"),
    assessment=a.replace({np.nan: None}).to_dict("records"),
    burn=burn.to_dict("records"),
    pilot_payouts=pilot_pay[["adm3_name", "crop", "year", "S", "pay_pct", "driver_peril", "driver_phase"]].to_dict("records"),
    validation=vstats,
    crosscheck=crosscheck,
    seventy_two=dict(events=len(fe), within=int(fe.within_72h.sum())),
)
# one self-contained file: the data is embedded where the template loads data.js
html = (POC / "dashboard_src" / "index.html").read_text(encoding="utf-8")
payload = json.dumps(clean(data), ensure_ascii=False).replace("</", "<\\/")
html = html.replace('<script src="data.js"></script>', f"<script>window.POC = {payload};</script>")
(OUT / "index.html").write_text(html, encoding="utf-8")
print("dashboard written:", OUT / "index.html", f"({(OUT / 'index.html').stat().st_size / 1024:.0f} KB)")
# phone capture page (Module B app): served next to the dashboard, talks to the same photo API
for f in ["capture.html", "manifest.json", "icon.svg"]:
    (OUT / f).write_bytes((POC / "dashboard_src" / f).read_bytes())
print("capture page written:", OUT / "capture.html")
