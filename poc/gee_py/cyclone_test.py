"""Out-of-pilot test on Cyclones Arnab and Murasu (rules: poc/CYCLONE_TEST_2026.md, written before computing).

Usage: py -3.13 cyclone_test.py <ee-project> [radar|rain|score]   (default: all three)
  radar  per-mandal radar flood (flood_passes.by_mandal, corrected pass selection) for each scored old district,
         event window and the two dry control dates -> gee_out/out_cyc_<event>_<district>.parquet
  rain   ERA5 daily at every mandal centroid, event window +/- 2 days (Open-Meteo) -> derived/cyclone_test_rain.parquet
  score  district table and the declared scores -> derived/cyclone_test.json
"""
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor

import geopandas as gpd
import numpy as np
import pandas as pd
import requests
from scipy.stats import spearmanr

PROJECT = sys.argv[1]
STEPS = sys.argv[2:] or ["radar", "rain", "score"]
sys.argv = ["ee_run", PROJECT, "none"]
import ee  # noqa: E402
import ee_run as R  # noqa: E402
import flood_passes as FP  # noqa: E402

OUT, DERIVED = R.OUT, R.DERIVED
EVENTS = {
    "ARNAB": dict(name="Cyclone Arnab", landfall="2026-10-28 02:00", start="2026-10-27", end="2026-10-29",
                  districts=["East Godavari", "West Godavari", "Krishna", "Guntur", "Visakhapatnam", "Vizianagaram", "Srikakulam"]),
    "MURASU": dict(name="Cyclone Murasu", landfall="2026-11-03 01:00", start="2026-11-02", end="2026-11-04",
                   districts=["Prakasam", "Guntur", "Krishna", "Potti Sriramulu Nellore"]),
}
CTRL = ["2024-02-15", "2024-03-01"]
# state figures (CYCLONE_TEST_2026.md), summed into old districts; None = not itemised
REPORTED = {"ARNAB": {"East Godavari": 52253 + 49959 + 46845, "West Godavari": 76752, "Krishna": 44836},
            "MURASU": {"Prakasam": 3151, "Guntur": 5619, "Potti Sriramulu Nellore": 0}}


def mandals():
    gaul = ee.FeatureCollection("FAO/GAUL/2025/level2").filter(ee.Filter.eq("GAUL1_NAME", "Andhra Pradesh"))
    d = gpd.GeoDataFrame.from_features(gaul.map(lambda f: f.simplify(500)).getInfo()["features"], crs=4326)[["GAUL2_NAME", "geometry"]]
    g = gpd.read_file(R.POC / "data" / "open" / "gb_ind_adm3.geojson").cx[76.5:85.0, 12.5:19.5]
    c = g.assign(geometry=g.to_crs(32644).centroid.to_crs(4326))
    j = gpd.sjoin(c, d, predicate="within")[["shapeID", "GAUL2_NAME"]]
    g = g.merge(j, on="shapeID")
    g["geometry"] = g.geometry.simplify(0.0003)
    return g.rename(columns={"GAUL2_NAME": "district", "shapeID": "mid", "shapeName": "mandal"})


def fc_of(g):
    return ee.FeatureCollection([ee.Feature(ee.Geometry(json.loads(gpd.GeoSeries([x]).to_json())["features"][0]["geometry"], geodesic=False),
                                            {"mid": m}) for m, x in zip(g.mid, g.geometry)])


def cmd_radar(M):
    jobs = []
    for ev, e in EVENTS.items():
        for d in e["districts"]:
            jobs.append((f"out_cyc_{ev}_{d.replace(' ', '_')}", d, e["start"], e["end"]))
    for d in sorted({d for e in EVENTS.values() for d in e["districts"]}):
        for c in CTRL:
            jobs.append((f"out_cyc_CTRL{c.replace('-', '')}_{d.replace(' ', '_')}", d, c, c))

    def run(job):
        name, d, s, e = job
        f = OUT / f"{name}.parquet"
        if f.exists():
            return
        res = FP.by_mandal(fc_of(M[M.district == d]), s, e, "mid")
        if res is None:
            print(name, "no matched pass in 12 days", flush=True)
            return
        res.assign(district=d).to_parquet(f, index=False)
        print(name, f"imaged {int(res.imaged.sum())}/{len(res)}, first pass {res.post_image_time.min()}", flush=True)

    with ThreadPoolExecutor(4) as ex:
        for fut in [ex.submit(run, j) for j in jobs]:
            try:
                fut.result()
            except Exception as err:
                print("error:", str(err)[:300], flush=True)


def cmd_rain(M):
    c = M.assign(geometry=M.to_crs(32644).centroid.to_crs(4326))
    c["lat"], c["lon"] = c.geometry.y.round(4), c.geometry.x.round(4)
    out = []
    for i in range(0, len(c), 50):
        b = c.iloc[i:i + 50]
        p = dict(latitude=",".join(map(str, b.lat)), longitude=",".join(map(str, b.lon)), start_date="2026-10-25",
                 end_date="2026-11-06", daily="precipitation_sum", models="era5", timezone="Asia/Kolkata")
        for _ in range(8):
            r = requests.get("https://archive-api.open-meteo.com/v1/archive", params=p, timeout=300)
            if r.status_code == 200:
                break
            time.sleep(65)
        r.raise_for_status()
        js = r.json() if isinstance(r.json(), list) else [r.json()]
        for m, j in zip(b.mid, js):
            out.append(pd.DataFrame({"mid": m, "date": pd.to_datetime(j["daily"]["time"]), "rain_mm": j["daily"]["precipitation_sum"]}))
        time.sleep(4)
    pd.concat(out).to_parquet(DERIVED / "cyclone_test_rain.parquet", index=False)
    print("rain:", len(out), "mandals")


def cmd_score(M):
    rain = pd.read_parquet(DERIVED / "cyclone_test_rain.parquet")
    res = {}
    for ev, e in EVENTS.items():
        w0, w1 = pd.Timestamp(e["start"]) - pd.Timedelta(days=2), pd.Timestamp(e["end"]) + pd.Timedelta(days=2)
        rw = rain[rain.date.between(w0, w1)].sort_values(["mid", "date"])
        rw["r3"] = rw.groupby("mid").rain_mm.transform(lambda s: s.rolling(3, min_periods=3).sum())
        rr = rw.groupby("mid").agg(max1=("rain_mm", "max"), max3=("r3", "max"))
        rows = []
        for d in e["districts"]:
            k = d.replace(" ", "_")
            f = OUT / f"out_cyc_{ev}_{k}.parquet"
            if not f.exists():
                continue
            x = pd.read_parquet(f)
            ctl = pd.concat([pd.read_parquet(OUT / f"out_cyc_CTRL{c.replace('-', '')}_{k}.parquet") for c in CTRL])
            floor = (ctl.crop_flood_ha / ctl.cropland_ha).groupby(ctl.mid).max()
            x["floor"] = x.mid.map(floor)
            x["share"] = x.crop_flood_ha / x.cropland_ha
            x["net_ha"] = (x.share - x.floor).clip(lower=0) * x.cropland_ha
            x = x.join(rr, on="mid")
            hrs = (pd.to_datetime(x.post_image_time) + pd.Timedelta(hours=5, minutes=30) - pd.Timestamp(e["landfall"])).dt.total_seconds() / 3600
            rows.append(dict(district=d, mandals=len(x), imaged=int(x.imaged.sum()), floor_known=int(x.floor.notna().sum()),
                             cropland_imaged_ha=float(x.cropland_ha.sum()), flooded_ha=float(x.crop_flood_ha.sum()),
                             net_flooded_ha=float(x.net_ha.sum()), mandals_above_floor=int((x.share > x.floor).sum()),
                             first_image_h=float(hrs.min()), within_72h=bool(hrs.min() <= 72),
                             mandals_very_heavy=int((x.max1 >= 115.6).sum()), mandals_extremely_heavy=int((x.max1 >= 204.5).sum()),
                             max3_median_mm=float(x.max3.median()), max3_max_mm=float(x.max3.max()),
                             reported_ha=REPORTED[ev].get(d)))
        t = pd.DataFrame(rows).sort_values("net_flooded_ha", ascending=False)
        t["ratio_net_to_reported"] = t.net_flooded_ha / t.reported_ha.replace(0, np.nan)
        sc = {}
        if ev == "ARNAB":
            top3 = set(t.district.head(3))
            sc["top3_match"] = top3 == {"East Godavari", "West Godavari", "Krishna"}
            k = t.dropna(subset=["reported_ha"])
            sc["spearman_named"] = float(spearmanr(k.net_flooded_ha, k.reported_ha)[0]) if len(k) >= 3 else None
        else:
            n = t.set_index("district").net_flooded_ha
            nel = n.get("Potti Sriramulu Nellore", np.nan)
            sc["prakasam_gt_nellore"] = bool(n.get("Prakasam", np.nan) > nel)
            sc["guntur_gt_nellore"] = bool(n.get("Guntur", np.nan) > nel)
        sc["share_districts_within_72h"] = float(t.within_72h.mean())
        res[ev] = dict(event=e, districts=json.loads(t.to_json(orient="records")), scores=sc)
        print(f"\n{e['name']}\n", t.drop(columns=["floor_known"]).round(1).to_string(index=False), "\n", sc)
    (DERIVED / "cyclone_test.json").write_text(json.dumps(res, indent=1, default=float))


M = mandals()
print("mandals by district:", M.groupby("district").size().to_dict())
for s in STEPS:
    {"radar": cmd_radar, "rain": cmd_rain, "score": cmd_score}[s](M)
