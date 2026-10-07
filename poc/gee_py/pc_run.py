"""Positive control (see poc/POSITIVE_CONTROL.md): Budameru / Krishna floods, 31 Aug - 2 Sep 2024.

Usage: py -3.13 pc_run.py <project> run       start the 3 export tasks (event + 2 dry controls)
       py -3.13 pc_run.py <project> direct    compute interactively (no assets), save locally
       py -3.13 pc_run.py <project> report    download (if exported) and apply the declared pass rule
"""
import json
import sys

import geopandas as gpd
import numpy as np
import pandas as pd

PROJECT, CMD = sys.argv[1], sys.argv[2]
sys.argv = ["ee_run", PROJECT, "none"]
import ee  # noqa: E402
import ee_run as R  # noqa: E402

CENTER = (80.648, 16.506)          # Vijayawada
RADIUS_KM = 30
RUNS = [("PC_BUDAMERU_2024", "2024-08-31", "2024-09-02"),
        ("PC_CTRL_20240215", "2024-02-15", "2024-02-15"),
        ("PC_CTRL_20240301", "2024-03-01", "2024-03-01")]


def aoi_gdf():
    g = gpd.read_file(R.POC / "data" / "open" / "gb_ind_adm3.geojson")
    g = g.cx[79.9:81.4, 15.8:17.2].copy()
    c = g.to_crs(32644).centroid
    ctr = gpd.GeoSeries(gpd.points_from_xy([CENTER[0]], [CENTER[1]]), crs=4326).to_crs(32644).iloc[0]
    g["dist_km"] = c.distance(ctr) / 1000
    g = g[g.dist_km <= RADIUS_KM].copy()
    g["geometry"] = g.geometry.simplify(0.0003)
    return g[["shapeName", "shapeID", "dist_km", "geometry"]]


def aoi_fc(g):
    feats = []
    for r in g.itertuples():
        geom = json.loads(gpd.GeoSeries([r.geometry]).to_json())["features"][0]["geometry"]
        feats.append(ee.Feature(ee.Geometry(geom, geodesic=False), {"unit": r.shapeName, "uid": r.shapeID, "dist_km": float(r.dist_km)}))
    return ee.FeatureCollection(feats)


if CMD == "run":
    R.ensure_folder()
    g = aoi_gdf()
    print("AOI units:", len(g), sorted(g.shapeName))
    fc = aoi_fc(g)
    for eid, s, e in RUNS:
        table, _ = R.flood_event(fc, s, e, eid)
        R.to_asset(table, f"out_{eid}")

elif CMD == "direct":
    fc = aoi_fc(aoi_gdf())
    for eid, s, e in RUNS:
        table, _ = R.flood_event(fc, s, e, eid)
        df = ee.data.computeFeatures({"expression": table, "fileFormat": "PANDAS_DATAFRAME"})
        df.drop(columns=["geo"], errors="ignore").to_parquet(R.OUT / f"out_{eid}.parquet", index=False)
        print("computed", eid, len(df), flush=True)

if CMD in ("report", "direct"):
    rows = []
    for eid, _, _ in RUNS:
        f = R.OUT / f"out_{eid}.parquet"
        if not f.exists():
            df = ee.data.computeFeatures({"expression": ee.FeatureCollection(R.asset(f"out_{eid}")), "fileFormat": "PANDAS_DATAFRAME"})
            df.to_parquet(f, index=False)
        rows.append(pd.read_parquet(f))
    d = pd.concat(rows)
    d["share_pct"] = 100 * d.crop_flood_ha / d.cropland_ha.replace(0, np.nan)
    ev = d[d.event_id == RUNS[0][0]].set_index("unit")
    ctrl = d[d.event_id != RUNS[0][0]].groupby("unit").share_pct.max()
    ev["ctrl_max_pct"] = ctrl
    ev["excess_pct"] = ev.share_pct - ev.ctrl_max_pct
    aoi_event = ev.crop_flood_ha.sum() / ev.cropland_ha.sum() * 100
    c = d[d.event_id != RUNS[0][0]]
    aoi_ctrl = max(c[c.event_id == x].crop_flood_ha.sum() / c[c.event_id == x].cropland_ha.sum() * 100 for x in c.event_id.unique())
    print(f"post-event image: {ev.post_image_time.iloc[0]} ({ev.hours_after_event_end.iloc[0]:.0f} h after 2 Sep); "
          f"Otsu water threshold {ev.t_post_db.iloc[0]:.1f} dB; orbit matched: {bool(ev.orbit_matched.iloc[0])}")
    print(f"AOI flooded cropland: event {aoi_event:.2f}% vs dry-control max {aoi_ctrl:.2f}%  ->  "
          f"{'PASS' if aoi_event > aoi_ctrl else 'FAIL'} (declared rule: event share > control share)")
    print(ev.sort_values("dist_km")[["dist_km", "cropland_ha", "crop_flood_ha", "share_pct", "ctrl_max_pct", "excess_pct"]].round(2).to_string())
    print("excess vs distance from Vijayawada, Spearman:", round(ev.excess_pct.corr(ev.dist_km, method="spearman"), 2))
