"""Live refresh for the current season: latest rainfall, new events, radar flood maps for new events.

Usage: py -3.13 p20_live_refresh.py <earth-engine-project>
  1. ERA5 daily rainfall (Open-Meteo) from 1 Aug of this year to yesterday, all POC mandals; replaces overlap.
  2. CHIRPS daily from Earth Engine for the same window, where already published.
  3. Event catalogues (p05) and the radar event list (p08) are rebuilt by run_all.py after this step.
  4. Any event in the list without a flood output gets mapped now (same frozen method, ee_run.flood_event).
"""
import json
import subprocess
import sys
import time
from datetime import date, timedelta

import geopandas as gpd
import pandas as pd
import requests

from common import DERIVED, POC

PROJECT = sys.argv[1]
START = f"{date.today().year}-08-01"
END = str(date.today() - timedelta(days=1))
cent = pd.read_csv(DERIVED / "poc_mandal_centroids.csv", dtype={"district_code": str})

# 1. ERA5 via Open-Meteo
frames = []
for i in range(0, len(cent), 20):
    b = cent.iloc[i:i + 20]
    params = dict(latitude=",".join(map(str, b.lat)), longitude=",".join(map(str, b.lon)), start_date=START, end_date=END,
                  daily="precipitation_sum", models="era5", timezone="Asia/Kolkata")
    for attempt in range(8):
        r = requests.get("https://archive-api.open-meteo.com/v1/archive", params=params, timeout=300)
        if r.status_code == 200:
            break
        time.sleep(65)
    r.raise_for_status()
    js = r.json() if isinstance(r.json(), list) else [r.json()]
    for (_, row), j in zip(b.iterrows(), js):
        frames.append(pd.DataFrame({"adm3_id": row.adm3_id, "district_code": row.district_code,
                                    "date": pd.to_datetime(j["daily"]["time"]), "rain_mm": j["daily"]["precipitation_sum"]}))
    time.sleep(5)
new = pd.concat(frames)
new["rain_mm"] = pd.to_numeric(new.rain_mm)
new = new.dropna(subset=["rain_mm"])
old = pd.read_parquet(DERIVED / "rain_era5_daily.parquet")
old = old[old.date < new.date.min()]
pd.concat([old, new]).to_parquet(DERIVED / "rain_era5_daily.parquet", index=False)
print(f"ERA5 updated to {new.date.max().date()} ({len(new)} new rows)", flush=True)

# 2. CHIRPS via Earth Engine (direct compute)
sys.argv = ["ee_run", PROJECT, "none"]
sys.path.insert(0, str(POC / "gee_py"))
import ee  # noqa: E402
import ee_run as R  # noqa: E402

m = gpd.read_file(DERIVED / "poc_mandals.geojson")
m = m[m.ok].drop_duplicates("adm3_id")
m["geometry"] = m.geometry.simplify(0.002)


def fc_of(gdf):
    return ee.FeatureCollection([ee.Feature(ee.Geometry(json.loads(gpd.GeoSeries([g]).to_json())["features"][0]["geometry"], geodesic=False),
                                            {"mid": i, "dist": d}) for i, d, g in zip(gdf.adm3_id, gdf.district_code, gdf.geometry)])


chirps = ee.ImageCollection("UCSB-CHG/CHIRPS/DAILY").filterDate(START, END).select("precipitation")
n = chirps.size().getInfo()
if n:
    img = chirps.toBands().rename(chirps.aggregate_array("system:index").map(lambda s: ee.String("d").cat(ee.String(s))))
    df = ee.data.computeFeatures({"expression": img.reduceRegions(collection=fc_of(m), reducer=ee.Reducer.mean(), scale=5566)
                                  .map(lambda f: f.setGeometry(None)), "fileFormat": "PANDAS_DATAFRAME"})
    days = [c for c in df.columns if c[1:].isdigit()]
    long = df.melt(id_vars=["mid", "dist"], value_vars=days, var_name="d", value_name="rain_mm").dropna()
    long["date"] = pd.to_datetime(long.d.str[1:], format="%Y%m%d")
    long = long.rename(columns={"mid": "adm3_id", "dist": "district_code"}).drop(columns="d")
    oldc = pd.read_parquet(DERIVED / "rain_chirps_daily.parquet")
    oldc = oldc[oldc.date < long.date.min()]
    pd.concat([oldc, long]).to_parquet(DERIVED / "rain_chirps_daily.parquet", index=False)
    print(f"CHIRPS updated to {long.date.max().date()}", flush=True)
else:
    print("CHIRPS: nothing new published yet", flush=True)

# 2b. GPM IMERG: fetch months not yet cached (the most recent months are always refetched)
subprocess.run([sys.executable, str(POC / "gee_py" / "imerg.py"), sys.argv[1]], check=True, stdout=subprocess.DEVNULL)

# 3. rebuild catalogues and the radar event list
for args in (["p05_event_catalogue.py"], ["p05_event_catalogue.py", "rain_chirps_daily.parquet"],
             ["p05_event_catalogue.py", "rain_imerg_daily.parquet"], ["p08_flood_event_list.py"]):
    subprocess.run([sys.executable, *args], check=True, stdout=subprocess.DEVNULL)

# 4. radar flood maps for events that have no output yet
ev = pd.read_csv(DERIVED / "flood_events_gee3.csv", dtype={"district_code": str})
out_dir = POC / "data" / "gee_out"
for r in ev.itertuples():
    f = out_dir / f"out_flood_mandal_{r.id}.parquet"
    if f.exists():
        continue
    table, _ = R.flood_event(fc_of(m[m.district_code == r.district_code]), str(r.start)[:10], str(r.end)[:10], r.id)
    try:
        d = ee.data.computeFeatures({"expression": table, "fileFormat": "PANDAS_DATAFRAME"})
        d.drop(columns=["geo"], errors="ignore").to_parquet(f, index=False)
        print("mapped new event", r.id, flush=True)
    except ee.EEException as e:
        print("radar not available yet for", r.id, "-", str(e)[:80], flush=True)
