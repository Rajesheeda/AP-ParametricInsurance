"""Sentinel-1 flood index for every YSR Kadapa acute-rain window 2019-2025, so the dual trigger can be tested on CCE.

Windows: every extreme / unseasonal rain event (peak day >= IMD heavy) or cyclone in YSR during the crop season
(Jun-Jan) flagged by ANY of CHIRPS, ERA5 or IMERG, merged when they start within 5 days of each other.
Method: ee_run.flood_event, unchanged (frozen; same as the positive control). Computed directly, no assets.

Usage: py -3.13 sar_cce.py <project>      -> data/gee_out/out_sarcce_<start>.parquet + data/derived/sar_cce_windows.csv
"""
import json
import sys
from concurrent.futures import ThreadPoolExecutor

import geopandas as gpd
import pandas as pd

PROJECT = sys.argv[1]
sys.argv = ["ee_run", PROJECT, "none"]
import ee  # noqa: E402
import ee_run as R  # noqa: E402

fr = []
for s in ["chirps", "era5", "imerg"]:
    e = pd.read_csv(R.DERIVED / f"event_catalogue_{s}.csv", dtype={"district_code": str})
    e = e[(e.district_code == "11") & e.type.isin(["extreme_rain", "unseasonal_rain", "cyclone"])].copy()
    e["start"], e["end"] = pd.to_datetime(e.start), pd.to_datetime(e.end)
    e = e[((e.start.dt.month >= 6) | (e.start.dt.month == 1)) & ((e.type == "cyclone") | (e.peak_day_mm >= 64.5))]
    fr.append(e.assign(src=s))
e = pd.concat(fr).sort_values("start")
e = e[e.start.dt.year.between(2019, 2025)]
e["grp"] = (e.start.diff().dt.days > 5).cumsum()
win = e.groupby("grp").agg(start=("start", "min"), end=("end", "max"), mandals=("adm3_id", "nunique"),
                           sources=("src", lambda s: "+".join(sorted(set(s))))).reset_index(drop=True)
win["id"] = "SARCCE_" + win.start.dt.strftime("%Y%m%d")
win.to_csv(R.DERIVED / "sar_cce_windows.csv", index=False)

m = gpd.read_file(R.DERIVED / "poc_mandals.geojson")
m = m[m.ok & (m.district_code == "11")].drop_duplicates("adm3_id")
m["geometry"] = m.geometry.simplify(0.0003)
fc = ee.FeatureCollection([ee.Feature(ee.Geometry(json.loads(gpd.GeoSeries([r.geometry]).to_json())["features"][0]["geometry"], geodesic=False),
                                      {"mid": r.adm3_id, "mandal": r.adm3_name}) for r in m.itertuples()])


def run(r):
    out = R.OUT / f"out_sarcce_{r.id}.parquet"
    if out.exists():
        return
    table, _ = R.flood_event(fc, str(r.start.date()), str(r.end.date()), r.id)
    df = ee.data.computeFeatures({"expression": table, "fileFormat": "PANDAS_DATAFRAME"})
    df.drop(columns=["geo"], errors="ignore").to_parquet(out, index=False)
    print("done", r.id, len(df), flush=True)


with ThreadPoolExecutor(3) as ex:
    for f in [ex.submit(run, r) for r in win.itertuples()]:
        try:
            f.result()
        except Exception as err:
            print("error:", str(err)[:300], flush=True)
