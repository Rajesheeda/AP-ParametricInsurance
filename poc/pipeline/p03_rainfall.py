"""Daily ERA5 (0.25 deg, single homogeneous model) rainfall (Open-Meteo archive) at each POC mandal's centroid, 1995 onward.

Screening data for the event catalogue. Final triggers use areal CHIRPS/IMD means (GEE).
"""
import time

import geopandas as gpd
import pandas as pd
import requests

from common import DERIVED

START, END = "1995-01-01", "2026-09-27"
m = gpd.read_file(DERIVED / "poc_mandals.geojson")
m = m[m.ok].drop_duplicates("adm3_id").copy()
c = m.to_crs(32644).centroid.to_crs(4326)
m["lat"], m["lon"] = c.y.round(4), c.x.round(4)

out = DERIVED / "rain_era5_daily.parquet"
CHUNKS = DERIVED / "rain_era5_chunks"
CHUNKS.mkdir(exist_ok=True)
for i in range(0, len(m), 10):
    b = m.iloc[i:i + 10]
    chunk = CHUNKS / f"{i:04d}.parquet"
    if chunk.exists():
        continue
    frames = []
    params = dict(latitude=",".join(map(str, b.lat)), longitude=",".join(map(str, b.lon)),
                  start_date=START, end_date=END, daily="precipitation_sum",
                  models="era5", timezone="Asia/Kolkata")
    for attempt in range(12):
        r = requests.get("https://archive-api.open-meteo.com/v1/archive", params=params, timeout=300)
        if r.status_code == 200:
            break
        print("retry", r.status_code, r.text[:120])
        if "Daily" in r.text:
            raise SystemExit("Open-Meteo daily quota used up; rerun tomorrow (finished chunks are kept).")
        time.sleep(900 if "Hourly" in r.text else 65)
    r.raise_for_status()
    js = r.json()
    js = js if isinstance(js, list) else [js]
    for (_, row), j in zip(b.iterrows(), js):
        frames.append(pd.DataFrame({"adm3_id": row.adm3_id, "district_code": row.district_code,
                                    "date": pd.to_datetime(j["daily"]["time"]),
                                    "rain_mm": j["daily"]["precipitation_sum"]}))
    pd.concat(frames, ignore_index=True).to_parquet(chunk, index=False)
    print(f"{i + len(b)}/{len(m)}", flush=True)
    time.sleep(8)
df = pd.concat([pd.read_parquet(f) for f in sorted(CHUNKS.glob("*.parquet"))], ignore_index=True)
df["rain_mm"] = pd.to_numeric(df.rain_mm)
assert df.rain_mm.notna().mean() > 0.95, "rainfall mostly empty"
df.to_parquet(out, index=False)
m.drop(columns="geometry").to_csv(DERIVED / "poc_mandal_centroids.csv", index=False, encoding="utf-8-sig")
print(df.groupby("district_code").rain_mm.describe().round(1).to_string())
