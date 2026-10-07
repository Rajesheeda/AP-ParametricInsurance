"""Shapefiles to upload as Earth Engine assets.

poc_mandals: mandal polygons for the 4 POC districts.
ysr_parcels: matched YSR cadastral parcels with dominant crop, purity and sowing date per Kharif season.
"""
import geopandas as gpd
import pandas as pd

from common import DERIVED

GEE = DERIVED / "gee_upload"
GEE.mkdir(exist_ok=True)

m = gpd.read_file(DERIVED / "poc_mandals.geojson")
m = m[m.ok].drop_duplicates("adm3_id")
m = m.rename(columns={"district_code": "dist", "adm3_name": "mandal", "adm3_id": "mid"})[["dist", "mandal", "mid", "geometry"]]
m.to_file(GEE / "poc_mandals.shp", encoding="utf-8")

ep = pd.read_parquet(DERIVED / "ysr_epanta_parcel_join.parquet")
ep = ep[ep.join_level.isin(["exact", "base"]) & (ep.season == "Kharif")].copy()
ep["sowing_date"] = pd.to_datetime(ep.sowing_date, errors="coerce")
by = ep.groupby(["objectid", "year", "crop_name"]).agg(ac=("area", "sum"), sow=("sowing_date", "median")).reset_index()
tot = by.groupby(["objectid", "year"]).ac.transform("sum")
by["purity"] = by.ac / tot
dom = by.sort_values("ac").groupby(["objectid", "year"]).tail(1)
wide = dom.pivot(index="objectid", columns="year", values=["crop_name", "purity", "sow"])
attrs = pd.DataFrame(index=wide.index)
for y in sorted(dom.year.unique()):
    yy = str(y)[2:]
    attrs[f"crop{yy}"] = wide[("crop_name", y)]
    attrs[f"pur{yy}"] = wide[("purity", y)].round(2)
    attrs[f"sow{yy}"] = wide[("sow", y)].dt.strftime("%Y-%m-%d")
cad = gpd.GeoDataFrame(pd.read_parquet(DERIVED / "ysr_cadastral_farm.parquet").pipe(
    lambda d: d.assign(geometry=gpd.GeoSeries.from_wkb(d.geometry))), crs=4326)
p = cad[["objectid", "MANDAL_NM", "VILL_NAME", "geometry"]].merge(attrs, left_on="objectid", right_index=True)
# APAIMS objectid is not unique (about 8.5k duplicates): keep it as src_id, use a row-based unique pid
p = p.rename(columns={"MANDAL_NM": "mandal", "VILL_NAME": "village", "objectid": "src_id"}).reset_index(drop=True)
p["pid"] = p.index.astype(int)
p["geometry"] = p.geometry.simplify(0.000005)
p.to_file(GEE / "ysr_parcels.shp", encoding="utf-8")
print("mandals:", len(m), " parcels:", len(p))
print(p.filter(like="crop").notna().sum().to_string())
print("dominant crops K2025:", p.crop25.value_counts().head(8).to_dict())
print("purity>=0.8 share K2025:", round((p.pur25 >= 0.8).mean(), 3))
