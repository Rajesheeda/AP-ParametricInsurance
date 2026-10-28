"""Monthly soil moisture per POC mandal from Earth Engine (direct compute, no assets).

ERA5-Land  (ECMWF/ERA5_LAND/DAILY_AGGR): root-zone 0-100 cm = depth-weighted layers 1-3 (7, 21, 72 cm), 2000-2025.
SMAP L3 E  (NASA/SMAP/SPL3SMP_E/006): surface soil moisture (AM pass), satellite L-band radiometer, 2016-2025.
Months Jun-Dec of year y and Jan of y+1. Output: poc/data/derived/soil_moisture_monthly.parquet
Usage: py -3.13 soil_moisture.py <project>
"""
import json
import sys
from pathlib import Path

import ee
import geopandas as gpd
import pandas as pd

ee.Initialize(project=sys.argv[1])
DERIVED = Path(__file__).resolve().parents[1] / "data" / "derived"

m = gpd.read_file(DERIVED / "poc_mandals.geojson")
m = m[m.ok].drop_duplicates("adm3_id")
m["geometry"] = m.geometry.simplify(0.002)
fc = ee.FeatureCollection([ee.Feature(ee.Geometry(json.loads(gpd.GeoSeries([g]).to_json())["features"][0]["geometry"], geodesic=False),
                                      {"mid": i}) for i, g in zip(m.adm3_id, m.geometry)])


def months(y0, y1):
    for y in range(y0, y1 + 1):
        for mo in list(range(6, 13)) + [13]:
            yy, mm = (y + 1, 1) if mo == 13 else (y, mo)
            yield y, f"{yy}-{mm:02d}-01", (pd.Timestamp(yy, mm, 1) + pd.offsets.MonthBegin(1)).strftime("%Y-%m-%d"), f"{yy}{mm:02d}"


def stack(col, fn, y0, y1, prefix):
    return ee.Image.cat([fn(col.filterDate(a, b)).rename(f"{prefix}_{tag}") for _, a, b, tag in months(y0, y1)])


era = ee.ImageCollection("ECMWF/ERA5_LAND/DAILY_AGGR")
root = lambda c: c.map(lambda i: i.select("volumetric_soil_water_layer_1").multiply(0.07)
                       .add(i.select("volumetric_soil_water_layer_2").multiply(0.21))
                       .add(i.select("volumetric_soil_water_layer_3").multiply(0.72))).mean()
smap = ee.ImageCollection("NASA/SMAP/SPL3SMP_E/006").select("soil_moisture_am")
frames = []
for name, img, scale in [("era5land_root", stack(era, root, 2000, 2025, "e"), 11000),
                         ("smap_surface", stack(smap, lambda c: c.mean(), 2016, 2025, "s"), 9000)]:
    out = img.reduceRegions(collection=fc, reducer=ee.Reducer.mean(), scale=scale, tileScale=4)
    df = ee.data.computeFeatures({"expression": out.map(lambda f: f.setGeometry(None)), "fileFormat": "PANDAS_DATAFRAME"})
    long = df.melt(id_vars=["mid"], value_vars=[c for c in df.columns if c[:2] in ("e_", "s_")], var_name="k", value_name="sm").dropna()
    long["month"] = pd.to_datetime(long.k.str[2:], format="%Y%m")
    long["source"] = name
    frames.append(long.drop(columns="k").rename(columns={"mid": "adm3_id"}))
    print(name, len(long), "rows", flush=True)
pd.concat(frames).to_parquet(DERIVED / "soil_moisture_monthly.parquet", index=False)
print("saved")
