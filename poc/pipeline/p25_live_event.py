"""Live event run: Cyclone Arnab (very severe cyclonic storm; crossed the Andhra Pradesh / Yanam coast early on
28 Oct 2026, then moved north-west towards south Odisha). Everything here uses the contract and methods as frozen
before the storm (p13 two-lane rules, p22 term-sheet levels, ee_run.flood_event radar method); nothing is tuned to it.

Usage: py -3.13 p25_live_event.py [--radar <ee-project>]
  1. Rain at every POC mandal centroid, 22 Oct to yesterday (Open-Meteo, Asia/Kolkata days):
       ERA5        - the contract's index (p22 qualification gate); published about 5-6 days late.
       ECMWF IFS   - operational 0.25 deg model of the same family ERA5 is built from; GFS and ICON as the spread.
     Until ERA5 covers the window the rainfall side is PROVISIONAL (ECMWF IFS read against the ERA5 levels).
     Index = maximum 3-day total in the event window +/- 2 days (p13 / p22 convention).
  2. Standing crop: e-Panta Kharif 2026 bookings with sowing <= window start <= sowing + FAO-56 duration;
     paddy planting window (sowing from 30 days before to 15 days after) blocks radar confirmation (p13).
  3. Radar (--radar): frozen flood method per district with a rain signal; floor = dry-date control (CTRL_*).
  4. Lane 1 (index only) and Lane 2 (relief) with the p13 rules; expected yield loss from p18 (YSR CCE).
Outputs (gitignored): live_event_mandals.csv, live_event_rain.parquet, live_event_arnab.json; gee_out/out_live_*.parquet
"""
import json
import sys
import time
from datetime import date, datetime, timedelta

import numpy as np
import pandas as pd
import requests

from common import DERIVED, POC, ac

EVENT = dict(id="ARNAB_2026", name="Cyclone Arnab", category="Very severe cyclonic storm (IMD)",
             landfall="Crossed the Andhra Pradesh / Yanam coast near Yanam, early 28 Oct 2026 (IMD: between 02:00 and 08:00 IST)",
             landfall_ts="2026-10-28 08:00", start="2026-10-27", end="2026-10-29")
DUR = {"Paddy": 150, "Cotton": 195, "Groundnut": 130, "Red Chillies": 120}
CROPS = {"22": ["Cotton", "Red Chillies", "Paddy"], "11": ["Paddy", "Cotton", "Groundnut"], "14": ["Paddy"], "10": ["Paddy", "Groundnut"]}
MODELS = {"ecmwf_ifs025": "ECMWF IFS", "gfs_seamless": "GFS", "icon_seamless": "ICON"}
S, E = pd.Timestamp(EVENT["start"]), pd.Timestamp(EVENT["end"])
W0, W1 = S - pd.Timedelta(days=2), E + pd.Timedelta(days=2)
T72 = pd.Timestamp(EVENT["landfall_ts"]) + pd.Timedelta(hours=72)

cent = pd.read_csv(DERIVED / "poc_mandal_centroids.csv", dtype={"district_code": str})
cent = cent[cent.ok].drop_duplicates("adm3_id")
pil = pd.read_csv(DERIVED / "pilot_mandals.csv", dtype={"district_code": str})


# ------------------------------------------------------------------ 1. rain
def fetch(url, extra):
    out = []
    for i in range(0, len(cent), 20):
        b = cent.iloc[i:i + 20]
        p = dict(latitude=",".join(map(str, b.lat)), longitude=",".join(map(str, b.lon)), daily="precipitation_sum",
                 start_date="2026-10-22", end_date=str(date.today() - timedelta(days=1)), timezone="Asia/Kolkata", **extra)
        for _ in range(6):
            r = requests.get(url, params=p, timeout=300)
            if r.status_code == 200:
                break
            time.sleep(30)
        r.raise_for_status()
        js = r.json() if isinstance(r.json(), list) else [r.json()]
        for mid, j in zip(b.adm3_id, js):
            d = j["daily"]
            for k, v in d.items():
                if k.startswith("precipitation_sum"):
                    src = k.replace("precipitation_sum_", "") if k != "precipitation_sum" else "era5"
                    out.append(pd.DataFrame({"adm3_id": mid, "src": src, "date": pd.to_datetime(d["time"]), "rain_mm": v}))
        time.sleep(3)
    return pd.concat(out)


rain = pd.concat([fetch("https://archive-api.open-meteo.com/v1/archive", dict(models="era5")),
                  fetch("https://api.open-meteo.com/v1/forecast", dict(models=",".join(MODELS)))])
rain["rain_mm"] = pd.to_numeric(rain.rain_mm)
rain.to_parquet(DERIVED / "live_event_rain.parquet", index=False)
era5_last = rain[(rain.src == "era5") & rain.rain_mm.notna()].date.max()
era5_complete = era5_last >= W1
print(f"ERA5 published to {era5_last.date()}; window {W0.date()}..{W1.date()} -> {'complete' if era5_complete else 'PROVISIONAL'}")

lv = pd.read_parquet(DERIVED / "cat_cover_levels.parquet")
lv = lv[lv.src == "era5"].drop_duplicates("adm3_id")[["adm3_id", "L5", "L25"]]
# p13 weather trigger: 3-day total above the mandal's own 99th percentile (ERA5 1995-2024)
h = pd.read_parquet(DERIVED / "rain_era5_daily.parquet").sort_values(["adm3_id", "date"])
h["r3"] = h.groupby("adm3_id").rain_mm.transform(lambda s: s.rolling(3).sum())
p99 = h[h.date.dt.year.between(1995, 2024)].groupby("adm3_id").r3.quantile(0.99).rename("p99_3day")


def r3max(src):
    x = rain[(rain.src == src) & rain.date.between(W0, W1)].sort_values(["adm3_id", "date"])
    x["r3"] = x.groupby("adm3_id").rain_mm.transform(lambda s: s.rolling(3, min_periods=3).sum())
    return x.groupby("adm3_id").r3.max()


m = cent[["district_code", "adm3_id", "adm3_name", "mandal_te", "lat", "lon"]].merge(lv, on="adm3_id", how="left")
m = m.join(p99, on="adm3_id")
for k in ["era5", *MODELS]:
    m[f"{k}_3day_mm"] = m.adm3_id.map(r3max(k)).round(1)
mods = [f"{k}_3day_mm" for k in MODELS]
m["models_min"], m["models_max"] = m[mods].min(axis=1), m[mods].max(axis=1)
m["index_mm"] = m.era5_3day_mm if era5_complete else m.ecmwf_ifs025_3day_mm
m["index_source"] = "ERA5" if era5_complete else "ECMWF IFS (provisional until ERA5 publishes)"
m["rain_side_pct"] = (100 * np.clip((m.index_mm - m.L5) / (m.L25 - m.L5), 0, 1)).round(1)
m["models_above_L5"] = (m[mods].values > m[["L5"]].values).sum(axis=1)
m["weather_trigger"] = m.index_mm > m.p99_3day

# ------------------------------------------------------------------ 2. standing crop (e-Panta Kharif 2026)
st = []
for code, crops in CROPS.items():
    d = pd.read_parquet(ac.extract_path("parametric", f"epanta_crop_parcel_{code}.parquet"),
                        columns=["mandal", "season", "year", "crop_name", "sowing_date", "area"])
    d = d[(d.year == 2026) & (d.season == "Kharif") & d.crop_name.isin(crops)].copy()
    d["sow"] = pd.to_datetime(d.sowing_date, errors="coerce")
    d = d.dropna(subset=["sow"])
    d["standing"] = (d.sow <= S) & (d.sow + pd.to_timedelta(d.crop_name.map(DUR), unit="D") >= S)
    d["planting"] = (d.crop_name == "Paddy") & d.sow.between(S - pd.Timedelta(days=30), E + pd.Timedelta(days=15))
    g = d.groupby("mandal").agg(standing_acres=("area", lambda a: a[d.loc[a.index, "standing"]].sum()),
                                crop_acres=("area", "sum"), planting=("planting", "any")).reset_index()
    g["district_code"] = code
    st.append(g)
st = pd.concat(st).rename(columns={"mandal": "mandal_te"})
m = m.merge(st, on=["district_code", "mandal_te"], how="left")
m[["standing_acres", "crop_acres"]] = m[["standing_acres", "crop_acres"]].fillna(0).round(0)
m["planting"] = m.planting.fillna(False).astype(bool)

# ------------------------------------------------------------------ 3. radar
OUT = POC / "data" / "gee_out"
if "--radar" in sys.argv:
    proj = sys.argv[sys.argv.index("--radar") + 1]
    import geopandas as gpd
    sys.argv = ["ee_run", proj, "none"]
    sys.path.insert(0, str(POC / "gee_py"))
    import ee  # noqa: E402
    import ee_run as R  # noqa: E402
    g = gpd.read_file(DERIVED / "poc_mandals.geojson")
    g = g[g.ok].drop_duplicates("adm3_id")
    g["geometry"] = g.geometry.simplify(0.002)
    for code in sorted(m[(m.rain_side_pct > 0) | m.weather_trigger].district_code.unique()):
        gg = g[g.district_code == code]
        fc = ee.FeatureCollection([ee.Feature(ee.Geometry(json.loads(gpd.GeoSeries([x]).to_json())["features"][0]["geometry"], geodesic=False),
                                              {"mid": i, "dist": code}) for i, x in zip(gg.adm3_id, gg.geometry)])
        table, _ = R.flood_event(fc, EVENT["start"], EVENT["end"], f"{EVENT['id']}_{code}")
        try:
            df = ee.data.computeFeatures({"expression": table, "fileFormat": "PANDAS_DATAFRAME"})
            df.drop(columns=["geo"], errors="ignore").to_parquet(OUT / f"out_live_{EVENT['id']}_{code}.parquet", index=False)
            print("radar mapped", code, df.post_image_time.iloc[0], flush=True)
        except ee.EEException as e:
            print("radar not available yet for district", code, "-", str(e)[:100], flush=True)

ctrl = pd.concat([pd.read_parquet(f) for f in OUT.glob("out_flood_mandal_CTRL_*.parquet")])
noise = (ctrl.crop_flood_ha / ctrl.cropland_ha).groupby(ctrl.mid).max()
rad = list(OUT.glob(f"out_live_{EVENT['id']}_*.parquet"))
if rad:
    r = pd.concat([pd.read_parquet(f) for f in rad]).rename(columns={"mid": "adm3_id"})
    r["flood_share_pct"] = 100 * r.crop_flood_ha / r.cropland_ha
    m = m.merge(r[["adm3_id", "flood_share_pct", "crop_flood_ha", "cropland_ha", "post_image_time", "orbit", "orbit_matched"]],
                on="adm3_id", how="left")
    m["post_ts"] = pd.to_datetime(m.post_image_time) + pd.Timedelta(hours=5, minutes=30)          # UTC -> IST
    m["hours_after_landfall"] = ((m.post_ts - pd.Timestamp(EVENT["landfall_ts"])).dt.total_seconds() / 3600).round(0)
else:
    m["flood_share_pct"] = np.nan
    m["post_image_time"] = None
    m["hours_after_landfall"] = np.nan
    m["orbit_matched"] = None
m["sar_floor_pct"] = (100 * m.adm3_id.map(noise)).round(2)
m["radar_mapped"] = m.flood_share_pct.notna()
m["within_72h"] = m.hours_after_landfall <= 72
m["sat_signal"] = m.radar_mapped & (m.standing_acres > 0) & (m.flood_share_pct > m.sar_floor_pct.fillna(0))
m["sat_confirms"] = m.sat_signal & ~m.planting
m["affected_acres_est"] = (m.standing_acres * np.clip(m.flood_share_pct.fillna(0) - m.sar_floor_pct.fillna(0), 0, None) / 100).round(0)

# ------------------------------------------------------------------ 4. two lanes (p13 rules)
cal = json.loads((DERIVED / "loss_calibration.json").read_text())["acute"]


def lane1(r):
    if r.rain_side_pct <= 0:
        return "NO PAYOUT", 0.0
    if not r.radar_mapped:
        return "AWAITING RADAR", 0.0
    if not r.sat_confirms:
        return "NO PAYOUT (radar does not confirm)", 0.0
    return ("INDEX PAYOUT" if era5_complete else "INDEX PAYOUT (provisional, final on ERA5)"), float(r.rain_side_pct)


m[["lane1_decision", "lane1_payout_pct"]] = m.apply(lambda r: pd.Series(lane1(r)), axis=1)
m["lane2_action"] = np.where(m.sat_signal & m.within_72h & ~m.planting, "PRIORITY ENUMERATION: RADAR-MAPPED",
                    np.where(m.weather_trigger | (m.rain_side_pct > 0) | m.sat_signal, "ENUMERATION: PHOTO / AEO", "MONITOR"))
m["expected_loss"] = np.where(m.lane2_action != "MONITOR",
                              f"median {cal['median']:.0f}% (IQR {cal['q25']:.0f}-{cal['q75']:.0f}%, n={cal['n']}, YSR CCE)", None)
m["basis_risk_flag"] = np.where(m.lane1_decision.str.startswith("NO PAYOUT") & m.lane2_action.str.startswith("PRIORITY"),
                                "relief signal, no index payout", None)
m["pilot"] = m.adm3_id.isin(pil.adm3_id)
DN = {"10": "Chittoor", "11": "YSR Kadapa", "14": "Parvathipuram Manyam", "22": "Palnadu"}
m["district"] = m.district_code.map(DN)
m.drop(columns=["mandal_te"]).to_csv(DERIVED / "live_event_mandals.csv", index=False)

keep = ["district", "adm3_name", "pilot", "standing_acres", "era5_3day_mm", "ecmwf_ifs025_3day_mm", "gfs_seamless_3day_mm",
        "icon_seamless_3day_mm", "models_min", "models_max", "L5", "L25", "p99_3day", "index_mm", "rain_side_pct", "models_above_L5",
        "weather_trigger", "planting", "radar_mapped", "post_image_time", "hours_after_landfall", "within_72h", "flood_share_pct",
        "sar_floor_pct", "affected_acres_est", "sat_confirms", "lane1_decision", "lane1_payout_pct", "lane2_action",
        "expected_loss", "basis_risk_flag"]
show = m[(m.lane2_action != "MONITOR") | m.pilot].sort_values(["district", "rain_side_pct", "index_mm"], ascending=[True, False, False])
out = dict(event=EVENT, t72=str(T72), generated=datetime.now().strftime("%Y-%m-%d %H:%M"),
           era5_published_to=str(era5_last.date()), era5_complete=bool(era5_complete),
           window=[str(W0.date()), str(W1.date())], rows=json.loads(show[keep].to_json(orient="records")),
           counts=dict(mandals=int(len(m)), enumeration=int((m.lane2_action != "MONITOR").sum()),
                       priority=int(m.lane2_action.str.startswith("PRIORITY").sum()),
                       rain_side=int((m.rain_side_pct > 0).sum()), awaiting_radar=int((m.lane1_decision == "AWAITING RADAR").sum()),
                       index_payout=int(m.lane1_decision.str.startswith("INDEX PAYOUT").sum()),
                       standing_acres_enumeration=float(m.loc[m.lane2_action != "MONITOR", "standing_acres"].sum())),
           calibration=cal)
(DERIVED / "live_event_arnab.json").write_text(json.dumps(out, indent=1, default=str), encoding="utf-8")
pd.set_option("display.width", 250)
print(show[["district", "adm3_name", "pilot", "standing_acres", "era5_3day_mm", "ecmwf_ifs025_3day_mm", "models_min", "models_max",
            "L5", "p99_3day", "rain_side_pct", "flood_share_pct", "sar_floor_pct", "hours_after_landfall", "lane1_decision",
            "lane2_action"]].round(1).to_string(index=False))
print(out["counts"])
