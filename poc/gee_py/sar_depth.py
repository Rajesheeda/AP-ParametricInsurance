"""SAR depth study (rules declared in poc/SAR_DEPTH_STUDY.md before computing).

Usage: py -3.13 sar_depth.py <ee-project> <study>
  revisit   D. P(radar image within 72 h) per pilot mandal and constellation period (metadata only)
  sample    A+B. per event: optical reference (Sentinel-2 MNDWI new water) and every variant at the same
            stratified points -> gee_out/out_depth_<event>.parquet (+ strata areas)
  fv        C. flooded-vegetation (double bounce) share on Budameru 2024 vs the two dry control dates
  score     A+B. Olofsson / Stehman estimator over the sampled points -> data/derived/sar_depth_accuracy.json
The frozen flood method (ee_run.flood_event) is called unchanged for v1; nothing here alters the contract.
"""
import json
import sys

import geopandas as gpd
import numpy as np
import pandas as pd

PROJECT, CMD, ONLY = sys.argv[1], sys.argv[2], sys.argv[3:]   # optional: event ids for sample
sys.argv = ["ee_run", PROJECT, "none"]
import ee  # noqa: E402
import ee_run as R  # noqa: E402

DERIVED, OUT = R.DERIVED, R.OUT
ENL = 4.4            # ESA Sentinel-1 product definition, IW GRDH equivalent number of looks
N_PER_STRATUM = 300
MIN_REF_FLOOD = 30


def fc_of(gdf, key):
    return ee.FeatureCollection([ee.Feature(ee.Geometry(json.loads(gpd.GeoSeries([g]).to_json())["features"][0]["geometry"],
                                                        geodesic=False), {"unit": str(k)}) for k, g in zip(gdf[key], gdf.geometry)])


def district_fc(code):
    m = gpd.read_file(DERIVED / "poc_mandals.geojson")
    m = m[m.ok & (m.district_code == code)].drop_duplicates("adm3_id").copy()
    m["geometry"] = m.geometry.simplify(0.002)
    return fc_of(m, "adm3_id")


def events():
    """Every event already mapped with the frozen method: GEE-3 list, the positive control, Cyclone Arnab."""
    ev = pd.read_csv(DERIVED / "flood_events_gee3.csv", dtype={"district_code": str})
    rows = [dict(eid=r.id, code=r.district_code, start=str(r.start)[:10], end=str(r.end)[:10]) for r in ev.itertuples()]
    rows.append(dict(eid="PC_BUDAMERU_2024", code="PC", start="2024-08-31", end="2024-09-02"))
    rows.append(dict(eid="ARNAB_2026_14", code="14", start="2026-10-27", end="2026-10-29"))
    return rows


def pc_fc():
    """Positive-control AOI, same rule as pc_run.aoi_gdf: mandals within 30 km of Vijayawada."""
    g = gpd.read_file(R.POC / "data" / "open" / "gb_ind_adm3.geojson").cx[79.9:81.4, 15.8:17.2].copy()
    ctr = gpd.GeoSeries(gpd.points_from_xy([80.648], [16.506]), crs=4326).to_crs(32644).iloc[0]
    g = g[g.to_crs(32644).centroid.distance(ctr) / 1000 <= 30].copy()
    g["geometry"] = g.geometry.simplify(0.0003)
    return fc_of(g, "shapeID")


def aoi_of(e):
    return pc_fc() if e["code"] == "PC" else district_fc(e["code"])


# ---------------------------------------------------------------- filters and variants
def lee(img):
    """Lee (1980) adaptive filter in linear power, 7x7 window."""
    lin = ee.Image(10).pow(img.divide(10))
    st = lin.reduceNeighborhood(ee.Reducer.mean().combine(ee.Reducer.variance(), sharedInputs=True), ee.Kernel.square(3))
    mean, var = st.select(0), st.select(1)
    ci2 = var.divide(mean.pow(2))
    w = ee.Image(1).subtract(ee.Image(1.0 / ENL).divide(ci2)).max(0)
    out = mean.add(w.multiply(lin.subtract(mean)))
    return out.log10().multiply(10)


def pair(aoi, start, end):
    """Same image selection as ee_run.flood_event (orbit-matched pre/post), both polarisations, unfiltered."""
    pre_orbits = R.s1(start.advance(-60, "day"), start, aoi).aggregate_array("relativeOrbitNumber_start").distinct()
    post_all = (R.s1(end, end.advance(12, "day"), aoi)
                .filter(ee.Filter.inList("relativeOrbitNumber_start", pre_orbits)).sort("system:time_start"))
    first = ee.Image(post_all.first())
    orbit, pas = first.get("relativeOrbitNumber_start"), first.get("orbitProperties_pass")
    post_t = ee.Date(first.get("system:time_start"))
    post = post_all.filter(ee.Filter.eq("relativeOrbitNumber_start", orbit)).filterDate(post_t, post_t.advance(1, "day")).mosaic()
    pre_pass = R.s1(start.advance(-60, "day"), start, aoi).filter(ee.Filter.eq("orbitProperties_pass", pas))
    pre_orbit = pre_pass.filter(ee.Filter.eq("relativeOrbitNumber_start", orbit))
    pre = ee.ImageCollection(ee.Algorithms.If(pre_orbit.size().gt(0), pre_orbit, pre_pass)).median()
    return post, pre, post_t


def otsu_t(post_vh, aoi):
    cls = R.JRC.unmask(0).gte(10).toInt().rename("cls")
    strat = (post_vh.rename("post").addBands(cls).updateMask(cls.Or(R.CROPLAND))
             .stratifiedSample(numPoints=2000, classBand="cls", region=aoi, scale=30, seed=1, geometries=False))
    return ee.Number(R.otsu(strat.reduceColumns(ee.Reducer.histogram(255, 0.1), ["post"]).get("histogram")))


def rule(post, pre, t, dthr):
    f = post.subtract(pre).lt(dthr).And(post.lt(t)).updateMask(R.JRC.unmask(0).lt(10)).updateMask(R.HND.lte(15)).selfMask()
    return f.updateMask(f.connectedPixelCount(8, True).gte(8)).unmask(0)


def variants(aoi_fc, start_s, end_s, eid):
    aoi = aoi_fc.geometry()
    start, end = ee.Date(start_s), ee.Date(end_s)
    post, pre, post_t = pair(aoi, start, end)
    fm = lambda i: i.focalMedian(50, "circle", "meters")  # noqa: E731
    pvh, qvh = fm(post.select("VH")), fm(pre.select("VH"))
    lpvh, lqvh = lee(post.select("VH")), lee(pre.select("VH"))
    t, tl = otsu_t(pvh, aoi), otsu_t(lpvh, aoi)
    _, v1 = R.flood_event(aoi_fc, start_s, end_s, eid)
    v1 = v1.unmask(0).rename("v1")
    open_water = rule(pvh, qvh, t, -3)
    vv_rise = fm(post.select("VV")).subtract(fm(pre.select("VV"))).gte(3)
    single = post.select("VH").focalMedian(50, "circle", "meters").lt(t).updateMask(R.JRC.unmask(0).lt(10)).updateMask(R.HND.lte(15)).unmask(0)
    img = ee.Image.cat([
        v1, open_water.rename("v1_check"), rule(lpvh, lqvh, tl, -3).rename("lee"),
        rule(pvh, qvh, t, -2).rename("d2"), rule(pvh, qvh, t, -4).rename("d4"),
        rule(pvh, qvh, t.subtract(1), -3).rename("tm1"), rule(pvh, qvh, t.add(1), -3).rename("tp1"),
        single.rename("single"), vv_rise.And(R.CROPLAND).And(open_water.Not()).rename("fv")]).toByte()
    # radar footprint of the post pass (amendment 1): outside it the map says nothing
    return img.updateMask(post.select("VH").mask()), post_t, t


# ---------------------------------------------------------------- optical reference
def s2_clear(start, end, region):
    sr = ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED").filterBounds(region).filterDate(start, end)
    prob = ee.ImageCollection("COPERNICUS/S2_CLOUD_PROBABILITY").filterBounds(region).filterDate(start, end)
    joined = ee.Join.saveFirst("cp").apply(sr, prob, ee.Filter.equals(leftField="system:index", rightField="system:index"))

    def f(img):
        img = ee.Image(img)
        scl = img.select("SCL")
        clear = ee.Image(img.get("cp")).select("probability").lt(40).And(scl.neq(3)).And(scl.neq(8)).And(scl.neq(9)).And(scl.neq(10))
        return img.normalizedDifference(["B3", "B11"]).rename("mndwi").updateMask(clear).copyProperties(img, ["system:time_start"])
    return ee.ImageCollection(joined).map(f)


def reference(aoi, start, post_t):
    near = s2_clear(post_t.advance(-1, "day"), post_t.advance(1, "day"), aoi)
    # closest acquisition on top
    near = near.map(lambda i: i.set("dt", ee.Number(i.get("system:time_start")).subtract(post_t.millis()).abs())).sort("dt", False)
    post_w = near.mosaic().select("mndwi").gt(0)
    pre_w = s2_clear(start.advance(-60, "day"), start, aoi).median().select("mndwi").gt(0)
    ref = post_w.And(pre_w.Not()).rename("ref")
    domain = post_w.mask().And(pre_w.mask()).And(R.CROPLAND).And(R.JRC.unmask(0).lt(10)).And(R.HND.lte(15))
    return ref, domain, near.size(), near.aggregate_array("dt")


# ---------------------------------------------------------------- commands
def _save_meta(rows):
    meta_f = DERIVED / "sar_depth_events.json"
    keep = {r["event"]: r for r in (json.loads(meta_f.read_text()) if meta_f.exists() else [])}
    keep.update({r["event"]: r for r in rows})
    meta_f.write_text(json.dumps(list(keep.values()), indent=1))


def cmd_sample():
    rows = []
    for e in [e for e in events() if not ONLY or e["eid"] in ONLY]:
        try:
            _sample_one(e, rows)
        except ee.EEException as err:
            info = dict(event=e["eid"], status=f"compute error: {str(err)[:80]}")
            rows.append(info); print(info, flush=True)
    _save_meta(rows)


def _sample_one(e, rows):
    if True:  # one event; errors are caught by cmd_sample
        f = OUT / f"out_depth_{e['eid']}.parquet"
        if f.exists():
            print("have", e["eid"]); return
        aoi_fc = aoi_of(e)
        aoi = aoi_fc.geometry()
        img, post_t, t = variants(aoi_fc, e["start"], e["end"], e["eid"])
        ref, domain, n_s2, dts = reference(aoi, ee.Date(e["start"]), post_t)
        n_s2 = n_s2.getInfo()
        info = dict(event=e["eid"], post_image=post_t.format("YYYY-MM-dd HH:mm").getInfo(), s2_images_within_1d=n_s2)
        if n_s2 == 0:
            info["status"] = "no Sentinel-2 image within 1 day"
            rows.append(info); print(info, flush=True); return
        info["s2_dt_hours"] = [round(x / 3.6e6, 1) for x in dts.getInfo()]
        domain = domain.And(img.select("v1").mask())
        stack = img.addBands(ref.toByte()).updateMask(domain)
        areas = (ee.Image.pixelArea().divide(1e4).addBands(img.select("v1")).updateMask(domain)
                 .reduceRegion(ee.Reducer.sum().group(1, "v1"), aoi, 20, maxPixels=1e11, tileScale=16).getInfo())
        info["strata_ha"] = {str(g["v1"]): g["sum"] for g in areas["groups"]}
        if not info["strata_ha"]:
            info["status"] = "no clear cropland in the scored domain"
            rows.append(info); print(info, flush=True); return
        pts = stack.stratifiedSample(numPoints=N_PER_STRATUM, classBand="v1", region=aoi, scale=20, seed=1,
                                     tileScale=16, geometries=False)
        df = ee.data.computeFeatures({"expression": pts, "fileFormat": "PANDAS_DATAFRAME"})
        df = df.drop(columns=["geo"], errors="ignore")
        df["event"] = e["eid"]
        df.to_parquet(f, index=False)
        info.update(status="sampled", n_points=len(df), n_ref_flood=int(df.ref.sum()),
                    v1_check_agreement=float((df.v1 == df.v1_check).mean()))
        rows.append(info); print(info, flush=True)
        _save_meta([info])


def cmd_fv():
    fc = pc_fc()
    aoi = fc.geometry()
    res = {}
    for eid, s, e in [("PC_BUDAMERU_2024", "2024-08-31", "2024-09-02"), ("PC_CTRL_20240215", "2024-02-15", "2024-02-15"),
                      ("PC_CTRL_20240301", "2024-03-01", "2024-03-01")]:
        img, post_t, _ = variants(fc, s, e, eid)
        st = img.select(["fv", "v1"]).updateMask(R.CROPLAND).reduceRegion(ee.Reducer.mean(), aoi, 20, maxPixels=1e11, tileScale=16).getInfo()
        res[eid] = dict(post_image=post_t.format("YYYY-MM-dd HH:mm").getInfo(), fv_share_pct=100 * st["fv"], open_water_share_pct=100 * st["v1"])
        print(eid, res[eid], flush=True)
    ctrl = max(res["PC_CTRL_20240215"]["fv_share_pct"], res["PC_CTRL_20240301"]["fv_share_pct"])
    res["ratio_event_to_max_control"] = res["PC_BUDAMERU_2024"]["fv_share_pct"] / ctrl if ctrl else None
    res["signal"] = bool(res["ratio_event_to_max_control"] and res["ratio_event_to_max_control"] >= 2)
    (DERIVED / "sar_depth_fv.json").write_text(json.dumps(res, indent=1))
    print(res)


def cmd_revisit():
    m = gpd.read_file(DERIVED / "poc_mandals.geojson")
    pil = pd.read_csv(DERIVED / "pilot_mandals.csv")
    m = m[m.adm3_id.isin(pil.adm3_id)].drop_duplicates("adm3_id")
    rows = []
    for r in m.itertuples():
        g = ee.Geometry(json.loads(gpd.GeoSeries([r.geometry.simplify(0.002)]).to_json())["features"][0]["geometry"], geodesic=False)
        c = R.s1(ee.Date("2020-11-01"), ee.Date("2026-11-14"), g)
        t = c.aggregate_array("system:time_start").getInfo()
        o = c.aggregate_array("relativeOrbitNumber_start").getInfo()
        p = c.aggregate_array("system:index").getInfo()
        rows += [dict(adm3_id=r.adm3_id, mandal=r.adm3_name, time=pd.to_datetime(a, unit="ms"), orbit=b, sat=s[:3]) for a, b, s in zip(t, o, p)]
        print(r.adm3_name, len(t), flush=True)
    acq = pd.DataFrame(rows).sort_values("time")
    acq.to_parquet(OUT / "out_depth_s1_acquisitions.parquet", index=False)
    periods = {"2021 (S1A + S1B)": ("2021-01-01", "2021-12-23"), "2022-2024 (S1A only)": ("2022-01-01", "2024-12-31"),
               "2025-2026 (current)": ("2025-01-01", "2026-11-10")}
    out = []
    for (mid, name), a in acq.groupby(["adm3_id", "mandal"]):
        # one acquisition per orbit per day (adjacent frames of the same pass)
        a = a.assign(day=a.time.dt.floor("D")).drop_duplicates(["orbit", "day"])
        for label, (p0, p1) in periods.items():
            hours = pd.date_range(p0, p1, freq="h")
            nxt = np.full(len(hours), np.inf)
            for orb, ao in a.groupby("orbit"):
                ts = ao.time.values
                # usable only if the same orbit has an image in the 60 days before the event hour
                i = np.searchsorted(ts, hours.values)
                prev_ok = (i > 0) & ((hours.values - ts[np.maximum(i - 1, 0)]) <= np.timedelta64(60, "D"))
                has_next = i < len(ts)
                wait = np.where(has_next & prev_ok, (ts[np.minimum(i, len(ts) - 1)] - hours.values) / np.timedelta64(1, "h"), np.inf)
                nxt = np.minimum(nxt, wait)
            sats = sorted(a[(a.time >= p0) & (a.time <= p1)].sat.unique())
            out.append(dict(adm3_id=mid, mandal=name, period=label, satellites=",".join(sats),
                            p_within_72h=float((nxt <= 72).mean()), median_wait_h=float(np.median(nxt)),
                            p95_wait_h=float(np.percentile(nxt, 95))))
    res = pd.DataFrame(out)
    res.to_csv(DERIVED / "sar_depth_revisit.csv", index=False)
    print(res.pivot(index="mandal", columns="period", values="p_within_72h").round(2).to_string())


# ---------------------------------------------------------------- estimator
def stratified(df, W, map_col, strata="v1"):
    """Stehman (2014): strata = v1 map classes (pooled: event x class) with area weights W[h]; map_col may differ."""
    df = df.rename(columns={strata: "_h"}) if strata != "v1" else df.assign(_h=df.v1)

    def est(y, x=None):
        num = sum(W[h] * y[df._h == h].mean() for h in W)
        if x is None:
            var = sum(W[h] ** 2 * y[df._h == h].var(ddof=1) / (df._h == h).sum() for h in W)
            return num, np.sqrt(var)
        den = sum(W[h] * x[df._h == h].mean() for h in W)
        Rr = num / den if den else np.nan
        var = sum(W[h] ** 2 * (y[df._h == h] - Rr * x[df._h == h]).var(ddof=1) / (df._h == h).sum() for h in W) / den ** 2 if den else np.nan
        return Rr, np.sqrt(var)
    m, r = df[map_col].astype(float), df.ref.astype(float)
    oa = est((m == r).astype(float))
    ua = est(m * r, m)
    pa = est(m * r, r)
    f1 = 2 * ua[0] * pa[0] / (ua[0] + pa[0]) if (ua[0] + pa[0]) else 0.0
    ci = lambda v: [max(0.0, v[0] - 1.96 * v[1]), min(1.0, v[0] + 1.96 * v[1])]  # noqa: E731
    return dict(oa=oa[0], oa_ci=ci(oa), ua=ua[0], ua_ci=ci(ua), pa=pa[0], pa_ci=ci(pa), f1=f1)


def cmd_score():
    meta = {r["event"]: r for r in json.loads((DERIVED / "sar_depth_events.json").read_text())}
    VARS = ["v1", "lee", "d2", "d4", "tm1", "tp1", "single"]
    per, pooled = [], []
    total_ha = 0
    for eid, info in meta.items():
        f = OUT / f"out_depth_{eid}.parquet"
        if not f.exists():
            per.append(dict(event=eid, status=info.get("status"))); continue
        df = pd.read_parquet(f)
        ha = {int(k): v for k, v in info["strata_ha"].items()}
        if df.ref.sum() < MIN_REF_FLOOD:
            per.append(dict(event=eid, status=f"not scored: {int(df.ref.sum())} reference-flood points (< {MIN_REF_FLOOD})",
                            n_points=len(df))); continue
        W = {h: ha.get(h, 0) / sum(ha.values()) for h in (0, 1) if (df.v1 == h).sum() > 1}
        per.append(dict(event=eid, status="scored", n_points=len(df), n_ref_flood=int(df.ref.sum()), domain_ha=sum(ha.values()),
                        **{v: stratified(df, W, v) for v in VARS}))
        pooled.append(df.assign(stratum=eid + "_" + df.v1.astype(str), w_ha=df.v1.map(ha)))
        total_ha += sum(ha.values())
    res = dict(per_event=per)
    if pooled:
        P = pd.concat(pooled)
        Wp = P.groupby("stratum").w_ha.first() / total_ha
        # pooled: each event x map class is a stratum
        res["pooled"] = {v: stratified(P, Wp.to_dict(), v, strata="stratum") for v in VARS}
        res["pooled_events"] = len(pooled)
        res["ppt_criterion_oa_ge_80"] = res["pooled"]["v1"]["oa"] >= 0.80
    (DERIVED / "sar_depth_accuracy.json").write_text(json.dumps(res, indent=1, default=float))
    print(json.dumps(res.get("pooled", {}), indent=1, default=float))
    for p in per:
        print(p["event"], p["status"], {k: round(p[k]["f1"], 2) for k in VARS} if p["status"] == "scored" else "")


def cmd_coverage():
    """Share of each mandal's cropland that the frozen method's post image actually covers.
    flood_event scores a district with the first matched pass; a mandal outside that footprint reads 0 ha flooded."""
    from concurrent.futures import ThreadPoolExecutor
    jobs = [e for e in events() if e["code"] != "PC"]
    for d in ["10", "11", "14", "22"]:
        jobs += [dict(eid=f"CTRL_{d}_{x.replace('-', '')}", code=d, start=x, end=x) for x in ("2024-02-15", "2024-03-01")]
    w = pd.read_csv(DERIVED / "sar_cce_windows.csv", parse_dates=["start", "end"])
    jobs += [dict(eid=r.id, code="11", start=str(r.start.date()), end=str(r.end.date())) for r in w.itertuples()]

    def run(e):
        f = OUT / f"out_depth_cov_{e['eid']}.parquet"
        if f.exists():
            return
        fc = district_fc(e["code"])
        post, _, post_t = pair(fc.geometry(), ee.Date(e["start"]), ee.Date(e["end"]))
        img = ee.Image.cat([post.select("VH").mask().And(R.CROPLAND).unmask(0).rename("imaged"),
                            R.CROPLAND.unmask(0).rename("crop")]).multiply(ee.Image.pixelArea()).divide(1e4)
        t = img.reduceRegions(collection=fc, reducer=ee.Reducer.sum(), scale=30, tileScale=8).map(lambda x: x.setGeometry(None))
        df = ee.data.computeFeatures({"expression": t, "fileFormat": "PANDAS_DATAFRAME"}).drop(columns=["geo"], errors="ignore")
        df["event_id"] = e["eid"]
        df["post_image_time"] = post_t.format("YYYY-MM-dd HH:mm").getInfo()
        df.to_parquet(f, index=False)
        print(e["eid"], f"{100 * df.imaged.sum() / df.crop.sum():.0f}% of cropland imaged,",
              int((df.imaged / df.crop < 0.5).sum()), "of", len(df), "mandals mostly not imaged", flush=True)

    with ThreadPoolExecutor(3) as ex:
        for fut in [ex.submit(run, e) for e in jobs]:
            try:
                fut.result()
            except Exception as err:
                print("error:", str(err)[:200], flush=True)


{"sample": cmd_sample, "fv": cmd_fv, "revisit": cmd_revisit, "score": cmd_score, "coverage": cmd_coverage}[CMD]()
