"""Daily non-rain weather parameters for the WBCIS term sheet (pilot mandals), 1995 onward.

Source : ERA5 reanalysis (ECMWF, 0.25 deg, one homogeneous model 1940-present, ~5-day lag),
         Open-Meteo archive API, at each pilot mandal's centroid.
Fields : 10 m wind speed daily max, 10 m wind gust daily max (km/h), 2 m relative humidity daily
         mean and max (%), 2 m temperature daily max and min (deg C).
Why    : WBCIS covers wind, disease-congenial weather (RH x temperature) and heat, not only rain.
         Rain itself stays on CHIRPS (areal, gauge-blended) as in p10.
Limit  : reanalysis smooths peaks; cyclone gusts are underestimated, so the wind cover's trigger
         and exit come from the same ERA5 history (internally consistent), and the live product
         should read the Reference Weather Station (APSDPS AWS / IMD).
"""
import time
import sys

import pandas as pd
import requests

from common import DERIVED

sys.stdout.reconfigure(encoding="utf-8")
START, END = "1995-01-01", sys.argv[1] if len(sys.argv) > 1 else "2026-11-12"
VARS = ["wind_speed_10m_max", "wind_gusts_10m_max", "relative_humidity_2m_mean",
        "relative_humidity_2m_max", "temperature_2m_max", "temperature_2m_min"]
COLS = ["wind_kmh", "gust_kmh", "rh_mean", "rh_max", "tmax", "tmin"]

pilot = pd.read_csv(DERIVED / "pilot_mandals.csv", dtype={"district_code": str})
cent = pd.read_csv(DERIVED / "poc_mandal_centroids.csv", dtype={"district_code": str})
m = pilot.merge(cent[["adm3_id", "lat", "lon"]], on="adm3_id")
CH = DERIVED / "weather_era5_chunks"
CH.mkdir(exist_ok=True)
for row in m.itertuples():
    f = CH / f"{row.adm3_id}.parquet"
    if f.exists():
        continue
    params = dict(latitude=row.lat, longitude=row.lon, start_date=START, end_date=END,
                  daily=",".join(VARS), models="era5", timezone="Asia/Kolkata", wind_speed_unit="kmh")
    for attempt in range(12):
        r = requests.get("https://archive-api.open-meteo.com/v1/archive", params=params, timeout=300)
        if r.status_code == 200:
            break
        print("retry", r.status_code, r.text[:160], flush=True)
        if "Daily" in r.text:
            raise SystemExit("Open-Meteo daily quota used up; rerun tomorrow (finished mandals are kept).")
        time.sleep(900 if "Hourly" in r.text else 65)
    r.raise_for_status()
    d = r.json()["daily"]
    df = pd.DataFrame({c: d[v] for v, c in zip(VARS, COLS)})
    df.insert(0, "date", pd.to_datetime(d["time"]))
    df.insert(0, "district_code", row.district_code)
    df.insert(0, "adm3_id", row.adm3_id)
    df.to_parquet(f, index=False)
    print(row.adm3_name, len(df), flush=True)
    time.sleep(20)
w = pd.concat([pd.read_parquet(f) for f in sorted(CH.glob("*.parquet"))], ignore_index=True)
for c in COLS:
    w[c] = pd.to_numeric(w[c])
w = w.dropna(subset=COLS, how="all")
w.to_parquet(DERIVED / "weather_era5_daily.parquet", index=False)
print(w.groupby("district_code")[COLS].describe().T.round(1).to_string())
print("last date:", w.date.max().date())
