"""GPM IMERG V07 daily rainfall per POC mandal (areal mean), June 2000 onward, computed directly (no assets).

Usage: py -3.13 imerg.py <project> [workers]
Output: data/derived/rain_imerg_chunks/YYYY-MM.parquet, merged into data/derived/rain_imerg_daily.parquet
        (same columns as rain_chirps_daily.parquet: adm3_id, district_code, rain_mm, date).

Why IMERG: CHIRPS and ERA5 both under-read the Nov 2021 YSR floods (POC_REPORT 7.4). IMERG merges passive-microwave
and IR satellite rain retrievals with GPCC gauges (Huffman et al., IMERG V07 ATBD), 0.1 deg, half-hourly.
Daily total = sum of half-hourly rates (mm/hr) x 0.5 h, day = UTC calendar day (same convention as CHIRPS).
"""
import json
import sys
from concurrent.futures import ThreadPoolExecutor

import ee
import geopandas as gpd
import pandas as pd
from pathlib import Path

POC = Path(__file__).resolve().parent.parent
DERIVED = POC / "data" / "derived"
CHUNKS = DERIVED / "rain_imerg_chunks"
CHUNKS.mkdir(parents=True, exist_ok=True)
PROJECT = sys.argv[1]
WORKERS = int(sys.argv[2]) if len(sys.argv) > 2 else 6
ee.Initialize(project=PROJECT)

m = gpd.read_file(DERIVED / "poc_mandals.geojson")
m = m[m.ok].drop_duplicates("adm3_id")
m["geometry"] = m.geometry.simplify(0.002)
feats = [ee.Feature(ee.Geometry(json.loads(gpd.GeoSeries([r.geometry]).to_json())["features"][0]["geometry"], geodesic=False),
                    {"adm3_id": r.adm3_id, "district_code": r.district_code}) for r in m.itertuples()]
FC = ee.FeatureCollection(feats)
IM = ee.ImageCollection("NASA/GPM_L3/IMERG_V07").select("precipitation")


def month(start):
    out = CHUNKS / f"{start:%Y-%m}.parquet"
    if out.exists():
        return
    end = start + pd.offsets.MonthBegin(1)
    days = pd.date_range(start, end - pd.Timedelta(days=1))
    col = IM.filterDate(str(start.date()), str(end.date()))
    if col.size().getInfo() == 0:
        print("no data yet", start.date(), flush=True)
        return
    imgs = [col.filterDate(str(d.date()), str((d + pd.Timedelta(days=1)).date())).sum().multiply(0.5).rename(f"d{d:%Y%m%d}")
            for d in days]
    stack = ee.Image.cat(imgs)
    fc = stack.reduceRegions(collection=FC, reducer=ee.Reducer.mean(), scale=11132).map(lambda f: f.setGeometry(None))
    df = ee.data.computeFeatures({"expression": fc, "fileFormat": "PANDAS_DATAFRAME"})
    df = df.drop(columns=["geo"], errors="ignore").melt(id_vars=["adm3_id", "district_code"], var_name="d", value_name="rain_mm")
    df["date"] = pd.to_datetime(df.d.str[1:], format="%Y%m%d")
    # the latest month is partial: keep it out of the cache so the next run refreshes it
    last = (pd.Timestamp.now() - pd.Timedelta(days=120)).to_period("M").to_timestamp()
    target = out if start < last else CHUNKS / f"_partial_{start:%Y-%m}.parquet"
    df.drop(columns="d").to_parquet(target, index=False)
    print("done", start.date(), len(df), flush=True)


months = list(pd.date_range("2000-06-01", pd.Timestamp.now().normalize(), freq="MS"))
with ThreadPoolExecutor(WORKERS) as ex:
    for f in [ex.submit(month, s) for s in months]:
        try:
            f.result()
        except Exception as e:  # keep going; a rerun fills gaps
            print("error:", str(e)[:200], flush=True)

parts = sorted(CHUNKS.glob("*.parquet"))
d = pd.concat([pd.read_parquet(p) for p in parts]).drop_duplicates(["adm3_id", "date"], keep="last")
d = d.dropna(subset=["rain_mm"]).sort_values(["adm3_id", "date"])
d.to_parquet(DERIVED / "rain_imerg_daily.parquet", index=False)
print("IMERG daily:", len(d), "rows", d.adm3_id.nunique(), "mandals", d.date.min().date(), "to", d.date.max().date())
