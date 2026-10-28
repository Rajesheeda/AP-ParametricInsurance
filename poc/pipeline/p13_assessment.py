"""Integrated loss assessment for the pilot mandals: rainfall trigger + satellite confirmation -> action.

Acute events (extreme / unseasonal rain, cyclone):
  Weather trigger: the event's max 3-day rainfall in the mandal exceeds the mandal's own 99th percentile
  (CHIRPS 1995-2024; ERA5 for days CHIRPS has not published yet, flagged provisional), or an IBTrACS
  cyclone >= 34 kt passed within 150 km. Return period of the 3-day total is reported.
  Satellite: flooded cropland (Sentinel-1, GEE-3 method) x share of each crop STANDING on the event date
  (standing = e-Panta sowing date <= event <= sowing + FAO-56 duration) -> affected acres by crop.
  If e-Panta shows paddy being sown within 30 days before to 15 days after the event, flood-like SAR
  signal may be puddling / transplanting water, so it cannot confirm loss on its own.
Season events (drought): season payout % (p10) confirmed by MODIS VCI < 35 (Kogan 1995).
Action:
  trigger AND satellite      -> PARAMETRIC PAYOUT
  exactly one of the two     -> FIELD / PHOTO VERIFICATION   (basis-risk catch, either direction)
  neither                    -> NO PAYOUT
Satellite confirmation for acute events = flooded share of cropland above the mandal's SAR false-alarm floor
(same algorithm on dry control dates), from a post-event image acquired within 72 h; later images are
reported but cannot confirm within the PPT window. Affected acres are net of the false-alarm floor.
Mandal-level flood is assumed spread over cropland in proportion to crop area (parcel level only in YSR).
"""
import glob

import numpy as np
import pandas as pd

from common import DERIVED, POC, ac

DUR = {"Paddy": 150, "Cotton": 195, "Groundnut": 130, "Red Chillies": 120}
CROPS = {"22": ["Cotton", "Red Chillies", "Paddy"], "11": ["Paddy", "Cotton", "Groundnut"],
         "14": ["Paddy"], "10": ["Paddy", "Groundnut"]}

pil = pd.read_csv(DERIVED / "pilot_mandals.csv", dtype={"district_code": str})
ev = pd.read_csv(DERIVED / "flood_events_gee3.csv", dtype={"district_code": str})
fl = pd.concat([pd.read_parquet(f) for f in glob.glob(str(POC / "data" / "gee_out" / "out_flood_mandal_*.parquet"))])
fl = fl.rename(columns={"mid": "adm3_id"})
# SAR false-alarm floor per mandal: same algorithm on dry control dates (Feb 15 / Mar 1 2024, < 21 mm in 45 days)
ctrl = fl[fl.event_id.str.startswith("CTRL_")]
NOISE = (ctrl.crop_flood_ha / ctrl.cropland_ha).groupby(ctrl.adm3_id).max().to_dict()
fl = fl[~fl.event_id.str.startswith("CTRL_")]
trig = pd.read_parquet(DERIVED / "trigger_annual_payouts.parquet")
phase = pd.read_parquet(DERIVED / "trigger_phase_stress.parquet")
vci = pd.read_csv(DERIVED / "validation_trigger_vs_vci.csv")[["adm3_id", "year", "vci"]]
# Rabi VCI (Chittoor) from MODIS Dec-Mar peak, same Kogan scaling
_m = pd.read_parquet(POC / "data" / "gee_out" / "out_modis_ndvi_2001_2026.parquet")
_r = _m.melt(id_vars=["mid"], value_vars=[c for c in _m.columns if c.startswith("rpeak_")], var_name="k", value_name="ndvi").dropna()
_r["year"] = _r.k.str[-4:].astype(int)
_g = _r.groupby("mid").ndvi
_r["vci"] = 100 * (_r.ndvi - _g.transform("min")) / (_g.transform("max") - _g.transform("min"))
vci_rabi = _r.rename(columns={"mid": "adm3_id"})[["adm3_id", "year", "vci"]]
chirps = pd.read_parquet(DERIVED / "rain_chirps_daily.parquet")
era5 = pd.read_parquet(DERIVED / "rain_era5_daily.parquet")
cat = pd.read_csv(DERIVED / "event_catalogue_era5.csv", dtype={"district_code": str})


def r3_series(src, mid):
    s = src[src.adm3_id == mid].set_index("date").rain_mm.sort_index()
    return s.rolling(3).sum()


def acute_trigger(mid, e_start, e_end):
    """(triggered, max 3-day mm, return period yrs, source) for the event window in this mandal."""
    src, tag = (chirps, "CHIRPS") if e_end <= chirps.date.max() else (era5, "ERA5 provisional")
    r3 = r3_series(src, mid)
    base = r3[(r3.index.year >= 1995) & (r3.index.year <= 2024)]
    annual_max = base.groupby(base.index.year).max()
    x = r3.loc[e_start - pd.Timedelta(days=2): e_end + pd.Timedelta(days=2)].max()
    rp = 1 / max(1e-9, 1 - (annual_max < x).mean()) if len(annual_max) else np.nan
    cyc = cat[(cat.adm3_id == mid) & (cat.type == "cyclone") & (pd.to_datetime(cat.start) <= e_end + pd.Timedelta(days=2))
              & (pd.to_datetime(cat.end) >= e_start - pd.Timedelta(days=2))]
    return bool(x > base.quantile(0.99) or len(cyc)), round(float(x), 1), round(float(rp), 1), tag, len(cyc) > 0


def epanta(code):
    d = pd.read_parquet(ac.extract_path("parametric", f"epanta_crop_parcel_{code}.parquet"),
                        columns=["mandal", "season", "year", "crop_name", "sowing_date", "area"])
    d = d[d.crop_name.isin(CROPS[code])].copy()
    d["sow"] = pd.to_datetime(d.sowing_date, errors="coerce")
    return d.dropna(subset=["sow"])


EP = {c: epanta(c) for c in CROPS}

rows = []
for r in ev.itertuples():
    e_start, e_end = pd.Timestamp(r.start), pd.Timestamp(r.end)
    for p in pil[pil.district_code == r.district_code].itertuples():
        f = fl[(fl.event_id == r.id) & (fl.adm3_id == p.adm3_id)]
        if f.empty:
            continue
        f = f.iloc[0]
        TRIG = globals().setdefault("TRIG", {})
        if (p.adm3_id, r.id) not in TRIG:
            TRIG[(p.adm3_id, r.id)] = acute_trigger(p.adm3_id, e_start, e_end)
        flood_share = f.crop_flood_ha / f.cropland_ha if f.cropland_ha else 0.0
        hrs = float(f.hours_after_event_end)
        d = EP[r.district_code]
        yr = e_end.year if e_end.year >= 2023 else 2025          # e-Panta exists 2023-2026
        season_year = yr - 1 if e_end.month <= 3 else yr
        d = d[(d.mandal == p.mandal_te) & (d.year == season_year)]
        for crop in CROPS[r.district_code]:
            c = d[d.crop_name == crop]
            if c.empty:
                continue
            # calendar transferred from the e-Panta year when the event predates e-Panta
            shift = pd.DateOffset(years=e_end.year - season_year) if e_end.year < 2023 else pd.DateOffset(years=0)
            sow = c.sow + shift
            standing = (sow <= e_start) & (sow + pd.to_timedelta(DUR[crop], unit="D") >= e_start)
            standing_ac = c.area[standing.values].sum()
            paddy = d[d.crop_name == "Paddy"]
            psow = paddy.sow + shift
            planting = bool(((psow >= e_start - pd.Timedelta(days=30)) & (psow <= e_end + pd.Timedelta(days=15))).any())
            weather, r3mm, rp, rsrc, cyc = TRIG[(p.adm3_id, r.id)]
            noise = NOISE.get(p.adm3_id, 0.0)
            sat_signal = bool(standing_ac > 0 and flood_share > noise and hrs <= 72)
            sat = sat_signal and not planting
            action = ("PARAMETRIC PAYOUT" if weather and sat else
                      "FIELD / PHOTO VERIFICATION" if weather or sat_signal else "NO PAYOUT")
            rows.append(dict(event_id=r.id, kind="acute", district_code=r.district_code, mandal=p.adm3_name,
                             start=e_start.date(), end=e_end.date(), crop=crop,
                             crop_acres=round(c.area.sum(), 1), standing_acres=round(standing_ac, 1),
                             post_image=f.post_image_time, hours_after_event=round(hrs, 1), within_72h=hrs <= 72,
                             flooded_cropland_ha=round(f.crop_flood_ha, 1), flood_share_pct=round(100 * flood_share, 2),
                             sar_noise_floor_pct=round(100 * NOISE.get(p.adm3_id, np.nan), 2),
                             affected_acres_est=round(standing_ac * max(0.0, flood_share - NOISE.get(p.adm3_id, 0.0)), 1),
                             rain_3day_mm=r3mm, return_period_yr=rp, rain_source=rsrc, cyclone=cyc,
                             paddy_planting_window=planting,
                             weather_trigger=weather, satellite_confirms=sat, action=action))

# Season (drought) assessment, pilot mandals x crops x 2020-2025
for p in pil.itertuples():
    for crop in CROPS[p.district_code]:
        for y in range(2020, 2026):
            tr = trig[(trig.adm3_id == p.adm3_id) & (trig.crop == crop) & (trig.year == y)]
            v = (vci_rabi if p.season == "Rabi" else vci)
            v = v[(v.adm3_id == p.adm3_id) & (v.year == y)]
            if tr.empty:
                continue
            t = tr.iloc[0]
            if t.driver_peril not in ("deficit", "dry"):
                continue
            weather = bool(t.pay_pct > 0)
            sat = bool(len(v) and v.vci.iloc[0] < 35)
            action = ("PARAMETRIC PAYOUT" if weather and sat else
                      "FIELD / PHOTO VERIFICATION" if weather or sat else "NO PAYOUT")
            rows.append(dict(event_id=f"{p.district_code}_{y}_season", kind="season", district_code=p.district_code,
                             mandal=p.adm3_name, start=f"{y}-06-01", end=f"{y}-12-31", crop=crop,
                             phase_driver=f"{t.driver_peril} ({t.driver_phase})", season_payout_pct=round(t.pay_pct, 1),
                             vci=round(float(v.vci.iloc[0]), 1) if len(v) else None,
                             weather_trigger=weather, satellite_confirms=sat, action=action))

a = pd.DataFrame(rows)

# Estimated yield loss from the CCE calibration (p18, YSR Kadapa 2019-2025), by which trigger fired
import json  # noqa: E402

cal_f = DERIVED / "loss_calibration.json"
if cal_f.exists():
    cal = json.loads(cal_f.read_text(encoding="utf-8"))
    kind = np.where(a.weather_trigger.fillna(False).astype(bool), np.where(a.kind == "acute", "acute", "drought"), "none")
    a["est_loss_basis"] = kind
    a["est_loss_median_pct"] = [cal[k]["median"] for k in kind]
    a["est_loss_iqr"] = [f"{cal[k]['q25']:.0f}-{cal[k]['q75']:.0f}" for k in kind]
    a["est_loss_n"] = [cal[k]["n"] for k in kind]
# Soil moisture percentile for season rows (p17); evidence only, does not change the decision (see report 7.5)
sm_f = DERIVED / "soil_moisture_index.parquet"
if sm_f.exists():
    smi = pd.read_parquet(sm_f)
    mp = pil.set_index("adm3_name").adm3_id.to_dict()
    a["year"] = pd.to_datetime(a.start).dt.year
    a = a.merge(smi.rename(columns={"era5land_root": "sm_root_pct", "smap_surface": "sm_smap_pct"})[
        ["adm3_id", "crop", "year", "sm_root_pct", "sm_smap_pct"]].assign(mandal=lambda d: d.adm3_id.map({v: k for k, v in mp.items()})),
        on=["mandal", "crop", "year"], how="left").drop(columns=["adm3_id"])
a.to_csv(DERIVED / "assessment_pilot.csv", index=False, encoding="utf-8-sig")
print(a.groupby(["kind", "action"]).size().to_string())
print("\nacute events with any trigger or satellite signal:")
cols = ["event_id", "mandal", "crop", "rain_3day_mm", "return_period_yr", "cyclone", "hours_after_event",
        "flood_share_pct", "sar_noise_floor_pct", "paddy_planting_window", "affected_acres_est", "action"]
print(a[(a.kind == "acute") & (a.action != "NO PAYOUT")][cols].to_string(index=False))
print("\nseason (drought) decisions:")
print(a[(a.kind == "season") & (a.action != "NO PAYOUT")][["event_id", "mandal", "crop", "phase_driver", "season_payout_pct", "vci", "action"]].to_string(index=False))
