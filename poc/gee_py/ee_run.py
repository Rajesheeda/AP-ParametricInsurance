"""Run the POC Earth Engine work from Python (no Code Editor, no Drive).

Usage (py -3.13 ee_run.py <project> <command>):
  upload    upload poc_mandals and ysr_parcels (chunked) as table assets
  chirps    CHIRPS daily rainfall per mandal, one row per mandal-year (365/366 values)
  ts        Kharif 10-day NDVI / VH / VV per YSR parcel and per mandal cropland, 2023-2026
  flood     Sentinel-1 flood mapping for the events in data/derived/flood_events_gee3.csv
  status    list task states
  download  pull every finished output table into data/gee_out/*.parquet

Methods are identical to gee/GEE1-3 *.js (see their headers). Outputs are written as table
assets under projects/<project>/assets/ap_poc/ and downloaded with ee.data.computeFeatures.
"""
import json
import sys
from pathlib import Path

import ee
import geopandas as gpd
import pandas as pd

POC = Path(__file__).resolve().parent.parent
DERIVED = POC / "data" / "derived"
OUT = POC / "data" / "gee_out"
OUT.mkdir(parents=True, exist_ok=True)
PARCEL_CHUNK = 4000
YEARS_TS = [2023, 2024, 2025, 2026]

PROJECT = sys.argv[1]
ROOT = f"projects/{PROJECT}/assets/ap_poc"
ee.Initialize(project=PROJECT)


def asset(name):
    return f"{ROOT}/{name}"


def ensure_folder():
    try:
        ee.data.getAsset(ROOT)
    except ee.EEException:
        ee.data.createAsset({"type": "FOLDER"}, ROOT)


def exists(name):
    try:
        ee.data.getAsset(asset(name))
        return True
    except ee.EEException:
        return False


def active_tasks():
    return {t["description"] for t in ee.data.getTaskList() if t["state"] in ("READY", "RUNNING")}


_ACTIVE = None


def to_asset(fc, name):
    global _ACTIVE
    if _ACTIVE is None:
        _ACTIVE = active_tasks()
    if exists(name) or name[:100] in _ACTIVE:
        print("skip (exists or queued):", name)
        return
    t = ee.batch.Export.table.toAsset(collection=fc, description=name[:100], assetId=asset(name))
    t.start()
    print("started:", name)


def fc_from_gdf(gdf, props):
    feats = []
    for row in gdf.itertuples():
        geom = json.loads(gpd.GeoSeries([row.geometry]).to_json())["features"][0]["geometry"]
        feats.append(ee.Feature(ee.Geometry(geom, geodesic=False), {p: getattr(row, p) for p in props}))
    return ee.FeatureCollection(feats)


def mandals():
    return ee.FeatureCollection(asset("poc_mandals"))


def parcels():
    names = [a["name"].split("/")[-1] for a in ee.data.listAssets({"parent": ROOT})["assets"]
             if a["name"].split("/")[-1].startswith("ysr_parcels_")]
    return ee.FeatureCollection([ee.FeatureCollection(asset(n)) for n in sorted(names)]).flatten()


# ---------------------------------------------------------------- upload
def cmd_upload():
    ensure_folder()
    m = gpd.read_file(DERIVED / "poc_mandals.geojson")
    m = m[m.ok].drop_duplicates("adm3_id").rename(columns={"district_code": "dist", "adm3_name": "mandal", "adm3_id": "mid"})
    m["geometry"] = m.geometry.simplify(0.0003)
    to_asset(fc_from_gdf(m, ["dist", "mandal", "mid"]), "poc_mandals")
    p = gpd.read_file(DERIVED / "gee_upload" / "ysr_parcels.shp")[["pid", "geometry"]]
    p["pid"] = p.pid.astype(int)
    p["geometry"] = p.geometry.make_valid()
    for i in range(0, len(p), PARCEL_CHUNK):
        to_asset(fc_from_gdf(p.iloc[i:i + PARCEL_CHUNK], ["pid"]), f"ysr_parcels_{i // PARCEL_CHUNK:02d}")


# ---------------------------------------------------------------- GEE-1 CHIRPS
def cmd_chirps():
    ensure_folder()
    m = mandals()
    for y in range(1995, 2027):
        col = ee.ImageCollection("UCSB-CHG/CHIRPS/DAILY").filterDate(f"{y}-01-01", f"{y + 1}-01-01").select("precipitation")
        img = col.toBands().rename(col.aggregate_array("system:index").map(lambda s: ee.String("d").cat(ee.String(s))))
        fc = img.reduceRegions(collection=m, reducer=ee.Reducer.mean(), scale=5566).map(lambda f: f.setGeometry(f.geometry().centroid(10)).set("year", y))
        to_asset(fc, f"out_chirps_{y}")


# ---------------------------------------------------------------- GEE-2 time series
CROPLAND = ee.ImageCollection("ESA/WorldCover/v200").first().eq(40)


def s2_ndvi(start, end, region):
    sr = ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED").filterBounds(region).filterDate(start, end)
    prob = ee.ImageCollection("COPERNICUS/S2_CLOUD_PROBABILITY").filterBounds(region).filterDate(start, end)
    joined = ee.Join.saveFirst("cp").apply(sr, prob, ee.Filter.equals(leftField="system:index", rightField="system:index"))

    def f(img):
        img = ee.Image(img)
        cp = ee.Image(img.get("cp")).select("probability")
        scl = img.select("SCL")
        clear = cp.lt(40).And(scl.neq(3)).And(scl.neq(8)).And(scl.neq(9)).And(scl.neq(10))
        return img.normalizedDifference(["B8", "B4"]).rename("ndvi").updateMask(clear)
    return ee.ImageCollection(joined).map(f)


def s1(start, end, region):
    return (ee.ImageCollection("COPERNICUS/S1_GRD").filterBounds(region).filterDate(start, end)
            .filter(ee.Filter.eq("instrumentMode", "IW"))
            .filter(ee.Filter.listContains("transmitterReceiverPolarisation", "VH")).select(["VH", "VV"]))


def season_stack(year, region):
    """One image, 3 bands per 10-day window from 1 Jun to 31 Jan: ndvi_MMDD, VH_MMDD, VV_MMDD."""
    start = pd.Timestamp(year, 6, 1)
    bands = []
    for k in range(25):
        d = start + pd.Timedelta(days=10 * k)
        e = d + pd.Timedelta(days=10)
        tag = d.strftime("%m%d")
        # Empty windows (e.g. 12-day S1 revisit 2022-2024, or full cloud) become masked "no data", not zero.
        s2c = s2_ndvi(str(d.date()), str(e.date()), region)
        s1c = s1(str(d.date()), str(e.date()), region)
        ndvi = ee.Image(ee.Algorithms.If(s2c.size().gt(0), s2c.max(), ee.Image.constant(0).updateMask(0))).rename("ndvi").float()
        sar = ee.Image(ee.Algorithms.If(s1c.size().gt(0), s1c.mean(), ee.Image.constant([0, 0]).updateMask(0))).rename(["VH", "VV"]).float()
        win = ee.Image.cat([ndvi, sar])
        bands.append(win.rename([f"ndvi_{tag}", f"VH_{tag}", f"VV_{tag}"]))
    return ee.Image.cat(bands)


def parcel_chunks():
    return sorted(a["name"].split("/")[-1] for a in ee.data.listAssets({"parent": ROOT})["assets"]
                  if a["name"].split("/")[-1].startswith("ysr_parcels_"))


def cmd_ts():
    """Small tasks: parcels per upload chunk, mandals per district (whole-region tasks ran out of memory)."""
    ensure_folder()
    global _ACTIVE
    _ACTIVE = active_tasks()
    m = mandals()
    for y in YEARS_TS:
        if not (exists(f"out_ts_parcels_{y}") or f"out_ts_parcels_{y}" in _ACTIVE):
            for c in parcel_chunks():
                fc = ee.FeatureCollection(asset(c))
                img = season_stack(y, fc.geometry().bounds())
                to_asset(img.reduceRegions(collection=fc.select(["pid"]), reducer=ee.Reducer.median(), scale=10, tileScale=16)
                         .map(lambda f: f.setGeometry(f.geometry().centroid(10))), f"out_ts_parcels_{y}_{c[-2:]}")
        if not (exists(f"out_ts_mandals_{y}") or f"out_ts_mandals_{y}" in _ACTIVE):
            for d in ["10", "11", "14", "22"]:
                fc = m.filter(ee.Filter.eq("dist", d))
                img = season_stack(y, fc.geometry().bounds()).updateMask(CROPLAND)
                to_asset(img.reduceRegions(collection=fc, reducer=ee.Reducer.median(), scale=30, tileScale=16)
                         .map(lambda f: f.setGeometry(f.geometry().centroid(10))), f"out_ts_mandals_{y}_d{d}")


# ---------------------------------------------------------------- GEE-3 flood
def otsu(hist):
    hist = ee.Dictionary(hist)
    counts = ee.Array(hist.get("histogram"))
    means = ee.Array(hist.get("bucketMeans"))
    size = means.length().get([0])
    total = counts.reduce(ee.Reducer.sum(), [0]).get([0])
    s = means.multiply(counts).reduce(ee.Reducer.sum(), [0]).get([0])
    mean = s.divide(total)

    def bss(i):
        a_c = counts.slice(0, 0, i)
        a_n = a_c.reduce(ee.Reducer.sum(), [0]).get([0])
        a_m = means.slice(0, 0, i).multiply(a_c).reduce(ee.Reducer.sum(), [0]).get([0]).divide(a_n)
        b_n = total.subtract(a_n)
        b_m = s.subtract(a_n.multiply(a_m)).divide(b_n)
        return a_n.multiply(a_m.subtract(mean).pow(2)).add(b_n.multiply(b_m.subtract(mean).pow(2)))
    return means.sort(ee.List.sequence(1, size).map(bss)).get([-1])


JRC = ee.Image("JRC/GSW1_4/GlobalSurfaceWater").select("seasonality")
HND = ee.Image("MERIT/Hydro/v1_0_1").select("hnd")


def flood_event(aoi_fc, start_str, end_str, eid):
    """Frozen flood method. Returns (per-unit area table, flood image)."""
    aoi = aoi_fc.geometry()
    start, end = ee.Date(start_str), ee.Date(end_str)
    # only post-event images from an orbit that also has a pre-event image, so every pair is matched
    pre_orbits = s1(start.advance(-60, "day"), start, aoi).aggregate_array("relativeOrbitNumber_start").distinct()
    post_all = (s1(end, end.advance(12, "day"), aoi).select("VH")
                .filter(ee.Filter.inList("relativeOrbitNumber_start", pre_orbits)).sort("system:time_start"))
    first = ee.Image(post_all.first())
    orbit, pas = first.get("relativeOrbitNumber_start"), first.get("orbitProperties_pass")
    post_day = ee.Date(first.get("system:time_start"))
    post = (post_all.filter(ee.Filter.eq("relativeOrbitNumber_start", orbit))
            .filterDate(post_day, post_day.advance(1, "day")).mosaic().focalMedian(50, "circle", "meters"))
    pre_pass = s1(start.advance(-60, "day"), start, aoi).select("VH").filter(ee.Filter.eq("orbitProperties_pass", pas))
    pre_orbit = pre_pass.filter(ee.Filter.eq("relativeOrbitNumber_start", orbit))
    matched = pre_orbit.size().gt(0)
    pre = ee.ImageCollection(ee.Algorithms.If(matched, pre_orbit, pre_pass)).median().focalMedian(50, "circle", "meters")
    diff = post.subtract(pre).rename("diff")
    # Water threshold: Otsu on a balanced sample of known permanent water (JRC) and cropland, so the
    # histogram is bimodal by construction. Change criterion: >= 3 dB backscatter drop (Clement et al. 2018).
    cls = JRC.unmask(0).gte(10).toInt().rename("cls")
    strat = (post.rename("post").addBands(cls).updateMask(cls.Or(CROPLAND))
             .stratifiedSample(numPoints=2000, classBand="cls", region=aoi, scale=30, seed=1, geometries=False))
    n_water = strat.filter(ee.Filter.eq("cls", 1)).size()
    t_post = otsu(strat.reduceColumns(ee.Reducer.histogram(255, 0.1), ["post"]).get("histogram"))
    t_diff = ee.Number(-3)
    flood = (diff.lt(t_diff).And(post.lt(ee.Number(t_post)))
             .updateMask(JRC.unmask(0).lt(10)).updateMask(HND.lte(15)).selfMask())
    flood = flood.updateMask(flood.connectedPixelCount(8, True).gte(8)).rename("flood")
    crop_flood = flood.And(CROPLAND).unmask(0)
    meta = {"event_id": eid, "post_image_time": post_day.format("YYYY-MM-dd HH:mm"),
            "hours_after_event_end": post_day.difference(end, "hour"), "orbit": orbit, "pass": pas,
            "orbit_matched": matched, "pre_images": ee.Algorithms.If(matched, pre_orbit.size(), pre_pass.size()),
            "t_diff_db": t_diff, "t_post_db": t_post, "n_water_samples": n_water}
    area = ee.Image.cat([crop_flood.multiply(ee.Image.pixelArea()).divide(1e4).rename("crop_flood_ha"),
                         CROPLAND.unmask(0).multiply(ee.Image.pixelArea()).divide(1e4).rename("cropland_ha")])
    table = area.reduceRegions(collection=aoi_fc, reducer=ee.Reducer.sum(), scale=10, tileScale=8)         .map(lambda f: f.setGeometry(f.geometry().centroid(10)).set(meta))
    return table, flood


def cmd_flood():
    ensure_folder()
    ev = pd.read_csv(DERIVED / (sys.argv[3] if len(sys.argv) > 3 else "flood_events_gee3.csv"), dtype={"district_code": str})
    p = parcels()
    for r in ev.itertuples():
        aoi_fc = mandals().filter(ee.Filter.eq("dist", r.district_code))
        table, flood = flood_event(aoi_fc, str(r.start)[:10], str(r.end)[:10], r.id)
        to_asset(table, f"out_flood_mandal_{r.id}")
        if r.district_code == "11":
            to_asset(flood.unmask(0).rename("flood_frac").reduceRegions(collection=p.select(["pid"]), reducer=ee.Reducer.mean(),
                     scale=10, tileScale=8).map(lambda f: f.setGeometry(f.geometry().centroid(10)).set("event_id", r.id)),
                     f"out_flood_parcel_{r.id}")


# ---------------------------------------------------------------- MODIS long record (independent check)
def cmd_modis():
    """MOD13Q1 NDVI over WorldCover cropland per mandal, 2001-2026: Kharif peak (Aug-Nov max),
    Kharif mid (Sep-Oct mean) and Rabi peak (Dec-Mar max). QA: SummaryQA <= 1 (good/marginal)."""
    ensure_folder()
    col = ee.ImageCollection("MODIS/061/MOD13Q1").map(
        lambda i: i.select("NDVI").multiply(0.0001).updateMask(i.select("SummaryQA").lte(1)).copyProperties(i, ["system:time_start"]))
    bands = []
    for y in range(2001, 2027):
        bands += [col.filterDate(f"{y}-08-01", f"{y}-12-01").max().rename(f"kpeak_{y}"),
                  col.filterDate(f"{y}-09-01", f"{y}-11-01").mean().rename(f"kmid_{y}")]
        if y < 2026:
            bands.append(col.filterDate(f"{y}-12-01", f"{y + 1}-04-01").max().rename(f"rpeak_{y}"))
    img = ee.Image.cat(bands).updateMask(CROPLAND)
    to_asset(img.reduceRegions(collection=mandals(), reducer=ee.Reducer.median(), scale=250, tileScale=4)
             .map(lambda f: f.setGeometry(f.geometry().centroid(10))), "out_modis_ndvi_2001_2026")


# ---------------------------------------------------------------- status / download
def cmd_status():
    tasks = ee.data.getTaskList()
    df = pd.DataFrame([{k: t.get(k) for k in ("description", "state", "error_message")} for t in tasks])
    print(df.groupby("state").size().to_string())
    bad = df[df.state == "FAILED"].drop_duplicates("description")
    if len(bad):
        print(bad.to_string(index=False))


def cmd_download():
    names = [a["name"].split("/")[-1] for a in ee.data.listAssets({"parent": ROOT})["assets"]]
    for n in sorted(x for x in names if x.startswith("out_")):
        f = OUT / f"{n}.parquet"
        if f.exists():
            continue
        df = ee.data.computeFeatures({"expression": ee.FeatureCollection(asset(n)), "fileFormat": "PANDAS_DATAFRAME"})
        df.drop(columns=[c for c in df.columns if c == "geo"], errors="ignore").to_parquet(f, index=False)
        print("downloaded", n, len(df))


if __name__ == "__main__":
    {"upload": cmd_upload, "chirps": cmd_chirps, "ts": cmd_ts, "flood": cmd_flood, "modis": cmd_modis,
     "status": cmd_status, "download": cmd_download}[sys.argv[2]]()
