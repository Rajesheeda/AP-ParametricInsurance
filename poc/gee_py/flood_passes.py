"""Corrected radar step (SAR_DEPTH_STUDY.md amendment 1): every mandal is scored by its own earliest orbit-matched pass.

ee_run.flood_event scores a whole district with the district's first matched pass, so a mandal outside that pass's
footprint read 0 ha flooded. Here each matched post-event pass in the same 12-day window is mapped with the identical
detection (VH, 50 m focal median, Otsu water threshold on the JRC/cropland sample, >= 3 dB drop, JRC / HAND / 8-pixel
masks); a mandal takes the earliest pass covering at least half of its cropland, and its flood share is over imaged
cropland only. A mandal with no such pass is NOT IMAGED (no number), never "no flood".

Usage: py -3.13 flood_passes.py <ee-project> [out_name ...]
  Old outputs are moved to data/gee_out/v1_district_pass/ (kept for the as-run comparison); new files keep the
  same names and columns, plus cropland_total_ha, coverage, imaged (cropland_ha becomes imaged cropland).
"""
import json
import shutil
import sys
from concurrent.futures import ThreadPoolExecutor

import geopandas as gpd
import pandas as pd

if __name__ == "__main__":
    PROJECT, ONLY = sys.argv[1], sys.argv[2:]   # optional: output names to (re)compute
    sys.argv = ["ee_run", PROJECT, "none"]
import ee  # noqa: E402
import ee_run as R  # noqa: E402   (importers set sys.argv for ee_run first)

OUT, DERIVED = R.OUT, R.DERIVED
V1 = OUT / "v1_district_pass"
V1.mkdir(exist_ok=True)
MIN_COVER = 0.5


def one_pass(aoi, start, orbit, day, pas):
    """Frozen detection for one post-event pass (same code path as ee_run.flood_event)."""
    post = (R.s1(day, day.advance(1, "day"), aoi).select("VH").filter(ee.Filter.eq("relativeOrbitNumber_start", orbit))
            .mosaic())
    foot = post.mask()
    post = post.focalMedian(50, "circle", "meters")
    pre = (R.s1(start.advance(-60, "day"), start, aoi).select("VH").filter(ee.Filter.eq("orbitProperties_pass", pas))
           .filter(ee.Filter.eq("relativeOrbitNumber_start", orbit)))
    n_pre = pre.size()
    pre = pre.median().focalMedian(50, "circle", "meters")
    cls = R.JRC.unmask(0).gte(10).toInt().rename("cls")
    strat = (post.rename("post").addBands(cls).updateMask(cls.Or(R.CROPLAND))
             .stratifiedSample(numPoints=2000, classBand="cls", region=aoi, scale=30, seed=1, geometries=False))
    t_post = R.otsu(strat.reduceColumns(ee.Reducer.histogram(255, 0.1), ["post"]).get("histogram"))
    flood = (post.subtract(pre).lt(-3).And(post.lt(ee.Number(t_post)))
             .updateMask(R.JRC.unmask(0).lt(10)).updateMask(R.HND.lte(15)).selfMask())
    flood = flood.updateMask(flood.connectedPixelCount(8, True).gte(8))
    img = ee.Image.cat([flood.And(R.CROPLAND).unmask(0).rename("crop_flood_ha"),
                        foot.And(R.CROPLAND).unmask(0).rename("imaged_ha"),
                        R.CROPLAND.unmask(0).rename("cropland_total_ha")]).multiply(ee.Image.pixelArea()).divide(1e4)
    return img, t_post, n_pre


def by_mandal(aoi_fc, start_s, end_s, key):
    aoi = aoi_fc.geometry()
    start, end = ee.Date(start_s), ee.Date(end_s)
    pre_orbits = R.s1(start.advance(-60, "day"), start, aoi).aggregate_array("relativeOrbitNumber_start").distinct()
    post_all = (R.s1(end, end.advance(12, "day"), aoi).select("VH")
                .filter(ee.Filter.inList("relativeOrbitNumber_start", pre_orbits)).sort("system:time_start"))
    info = ee.Dictionary({"t": post_all.aggregate_array("system:time_start"), "o": post_all.aggregate_array("relativeOrbitNumber_start"),
                          "p": post_all.aggregate_array("orbitProperties_pass")}).getInfo()
    passes = (pd.DataFrame(info).assign(day=lambda d: pd.to_datetime(d.t, unit="ms").dt.floor("D"))
              .sort_values("t").drop_duplicates(["o", "day"]))
    rows = []
    for p in passes.itertuples():
        img, t_post, n_pre = one_pass(aoi, start, p.o, ee.Date(p.day.strftime("%Y-%m-%d")), p.p)
        tab = img.reduceRegions(collection=aoi_fc, reducer=ee.Reducer.sum(), scale=10, tileScale=8).map(lambda f: f.setGeometry(None))
        try:
            d = ee.data.computeFeatures({"expression": tab, "fileFormat": "PANDAS_DATAFRAME"}).drop(columns=["geo"], errors="ignore")
        except ee.EEException as err:
            # a pass clipping a sliver of the area leaves no water / cropland sample for the Otsu threshold:
            # the pass cannot be thresholded, so it is skipped and the mandal takes its next pass
            if "bucketMeans" not in str(err):
                raise
            print(f"  skipped pass orbit {p.o} {p.day.date()}: no threshold sample", flush=True)
            continue
        first_t = pd.to_datetime(p.t, unit="ms")
        d = d.assign(post_image_time=first_t.strftime("%Y-%m-%d %H:%M"), orbit=p.o, **{"pass": p.p},
                     hours_after_event_end=(first_t - pd.Timestamp(end_s)).total_seconds() / 3600,
                     t_post_db=ee.Number(t_post).getInfo(), pre_images=n_pre.getInfo(), orbit_matched=True, t_diff_db=-3)
        rows.append(d)
    if not rows:
        return None
    a = pd.concat(rows)
    a["coverage"] = a.imaged_ha / a.cropland_total_ha
    ok = a[a.coverage >= MIN_COVER].sort_values("post_image_time").drop_duplicates(key)
    allm = a.drop_duplicates(key)[[key]]
    res = allm.merge(ok, on=key, how="left")
    res["imaged"] = res.crop_flood_ha.notna()
    res["cropland_ha"] = res.imaged_ha
    res["n_passes_considered"] = len(passes)
    return res


def jobs():
    ev = pd.read_csv(DERIVED / "flood_events_gee3.csv", dtype={"district_code": str})
    j = [dict(out=f"out_flood_mandal_{r.id}", code=r.district_code, start=str(r.start)[:10], end=str(r.end)[:10]) for r in ev.itertuples()]
    for d in ["10", "11", "14", "22"]:
        j += [dict(out=f"out_flood_mandal_CTRL_{d}_{x.replace('-', '')}", code=d, start=x, end=x) for x in ("2024-02-15", "2024-03-01")]
    w = pd.read_csv(DERIVED / "sar_cce_windows.csv", parse_dates=["start", "end"])
    j += [dict(out=f"out_sarcce_{r.id}", code="11", start=str(r.start.date()), end=str(r.end.date())) for r in w.itertuples()]
    j.append(dict(out="out_live_ARNAB_2026_14", code="14", start="2026-10-27", end="2026-10-29"))
    j += [dict(out=f"out_{eid}", code="PC", start=s, end=e) for eid, s, e in
          [("PC_BUDAMERU_2024", "2024-08-31", "2024-09-02"), ("PC_CTRL_20240215", "2024-02-15", "2024-02-15"),
           ("PC_CTRL_20240301", "2024-03-01", "2024-03-01")]]
    return j


def fc_for(code, key):
    if code == "PC":
        g = gpd.read_file(R.POC / "data" / "open" / "gb_ind_adm3.geojson").cx[79.9:81.4, 15.8:17.2].copy()
        ctr = gpd.GeoSeries(gpd.points_from_xy([80.648], [16.506]), crs=4326).to_crs(32644).iloc[0]
        g = g[g.to_crs(32644).centroid.distance(ctr) / 1000 <= 30].copy()
        g["geometry"], ids = g.geometry.simplify(0.0003), g.shapeID
    else:
        g = gpd.read_file(DERIVED / "poc_mandals.geojson")
        g = g[g.ok & (g.district_code == code)].drop_duplicates("adm3_id").copy()
        g["geometry"], ids = g.geometry.simplify(0.0003), g.adm3_id
    return ee.FeatureCollection([ee.Feature(ee.Geometry(json.loads(gpd.GeoSeries([x]).to_json())["features"][0]["geometry"], geodesic=False),
                                            {key: str(i)}) for i, x in zip(ids, g.geometry)])


def run(j):
    old_f, new_f = V1 / f"{j['out']}.parquet", OUT / f"{j['out']}.parquet"
    if old_f.exists() and new_f.exists() and "imaged" in pd.read_parquet(new_f).columns:
        return
    if not old_f.exists():
        shutil.copy2(new_f, old_f)
    old = pd.read_parquet(old_f)
    key = "uid" if "uid" in old.columns else "mid"
    res = by_mandal(fc_for(j["code"], key), j["start"], j["end"], key)
    ident = [c for c in old.columns if c in ("mid", "uid", "dist", "mandal", "unit", "dist_km")]
    new = old[ident].merge(res, on=key, how="left") if res is not None else old[ident].assign(imaged=False)
    new["event_id"] = old.event_id.iloc[0] if "event_id" in old else j["out"]
    new.to_parquet(new_f, index=False)
    # consistency: where the old first pass was also the chosen pass, flooded ha must match
    same = new.merge(old[[key, "crop_flood_ha", "post_image_time"]], on=key, suffixes=("", "_v1"))
    same = same[same.post_image_time == same.post_image_time_v1]
    dev = (same.crop_flood_ha - same.crop_flood_ha_v1).abs().max() if len(same) else float("nan")
    print(f"{j['out']}: imaged {int(new.imaged.sum())}/{len(new)} mandals (v1 scored all {len(old)} from one pass); "
          f"same-pass max |dha| = {dev:.2f}", flush=True)


if __name__ == "__main__":
    todo = [j for j in jobs() if not ONLY or j["out"] in ONLY]
    with ThreadPoolExecutor(4) as ex:
        for f in [ex.submit(run, j) for j in todo]:
            try:
                f.result()
            except Exception as err:
                print("error:", str(err)[:300], flush=True)
