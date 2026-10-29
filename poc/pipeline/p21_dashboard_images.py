"""Real images for the dashboard (no stock imagery): Sentinel-2 views, Sentinel-1 flood before/after, field photos.

Usage: py -3.13 p21_dashboard_images.py <earth-engine-project>
Writes poc/data/dashboard/img/*.jpg and img/manifest.json (gitignored: derived from Department data).
"""
import io
import json
import sys
from pathlib import Path

import ee
import geopandas as gpd
import pandas as pd
import requests
from PIL import Image

from common import DERIVED, POC

ee.Initialize(project=sys.argv[1])
sys.argv = ["ee_run", sys.argv[1], "none"]
sys.path.insert(0, str(POC / "gee_py"))
import ee_run as R  # noqa: E402

IMG = POC / "data" / "dashboard" / "img"
IMG.mkdir(parents=True, exist_ok=True)
man = {"mandals": [], "floods": [], "photos": []}


def save(url, name, size=None, q=82):
    if (IMG / name).exists():
        return name
    r = requests.get(url, timeout=300)
    r.raise_for_status()
    im = Image.open(io.BytesIO(r.content)).convert("RGB")
    if size:
        im.thumbnail(size)
    im.save(IMG / name, "JPEG", quality=q, optimize=True)
    return name


def geom(g):
    return ee.Geometry(json.loads(gpd.GeoSeries([g]).to_json())["features"][0]["geometry"], geodesic=False)


def s2_rgb(region, start, end):
    col = (ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED").filterBounds(region).filterDate(start, end)
           .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 30)))
    return col.median().select(["B4", "B3", "B2"]).visualize(min=200, max=2600, gamma=1.15)


# 1. pilot mandals: cloud-free Sentinel-2 true colour (Jan-Mar 2026, dry season), boundary drawn in
m = gpd.read_file(DERIVED / "poc_mandals.geojson")
pil = pd.read_csv(DERIVED / "pilot_mandals.csv", dtype={"district_code": str})
m = m[m.adm3_id.isin(pil.adm3_id)].drop_duplicates("adm3_id")
for r in m.itertuples():
    g = geom(r.geometry.simplify(0.001))
    box = g.bounds().buffer(1500)
    img = ee.ImageCollection([s2_rgb(box, "2026-01-01", "2026-03-31"),
                              ee.Image().byte().paint(ee.FeatureCollection([ee.Feature(g)]), 1, 3).visualize(palette=["38f9d7"])]).mosaic()
    name = save(img.getThumbURL({"region": box, "dimensions": 720, "format": "jpg"}), f"mandal_{r.adm3_id}.jpg", (720, 720))
    man["mandals"].append(dict(adm3_id=r.adm3_id, name=r.adm3_name, file=name))
    print("mandal", r.adm3_name, flush=True)

# hero: Krishna delta around Vijayawada (S2 true colour)
hero = ee.Geometry.Rectangle([80.35, 16.30, 81.05, 16.70])
man["hero"] = save(s2_rgb(hero, "2025-12-01", "2026-03-31").getThumbURL({"region": hero, "dimensions": 1800, "format": "jpg"}),
                   "hero_krishna_delta.jpg", q=78)
print("hero", flush=True)


# 2. flood before / after with the frozen method's flood mask overlaid
def flood_pair(key, title, start, end, region, note):
    pre_orbits = R.s1(ee.Date(start).advance(-60, "day"), start, region).aggregate_array("relativeOrbitNumber_start").distinct()
    post_all = (R.s1(end, ee.Date(end).advance(12, "day"), region).select("VH")
                .filter(ee.Filter.inList("relativeOrbitNumber_start", pre_orbits)).sort("system:time_start"))
    first = ee.Image(post_all.first())
    orbit, pas = first.get("relativeOrbitNumber_start"), first.get("orbitProperties_pass")
    day = ee.Date(first.get("system:time_start"))
    post = post_all.filter(ee.Filter.eq("relativeOrbitNumber_start", orbit)).filterDate(day, day.advance(1, "day")).mosaic().focalMedian(50, "circle", "meters")
    pre = (R.s1(ee.Date(start).advance(-60, "day"), start, region).select("VH").filter(ee.Filter.eq("orbitProperties_pass", pas))
           .filter(ee.Filter.eq("relativeOrbitNumber_start", orbit)).median().focalMedian(50, "circle", "meters"))
    fc = ee.FeatureCollection([ee.Feature(region, {"mid": key})])
    _, flood = R.flood_event(fc, start, end, key)
    vis = dict(min=-26, max=-8)
    before = pre.visualize(**vis)
    after = post.visualize(**vis)
    overlay = after.blend(flood.selfMask().visualize(palette=["00e5ff"]))
    out = dict(key=key, title=title, note=note, post_date=day.format("YYYY-MM-dd").getInfo())
    out["before"] = save(before.getThumbURL({"region": region, "dimensions": 1000, "format": "jpg"}), f"flood_{key}_before.jpg")
    out["after"] = save(overlay.getThumbURL({"region": region, "dimensions": 1000, "format": "jpg"}), f"flood_{key}_after.jpg")
    man["floods"].append(out)
    print("flood", key, out["post_date"], flush=True)


flood_pair("budameru2024", "Budameru / Krishna floods, Sep 2024 (positive control)", "2024-08-31", "2024-09-02",
           ee.Geometry.Rectangle([80.45, 16.40, 80.80, 16.65]),
           "Sentinel-1 VH before (left) and after with detected flood in cyan (right). Pass: 5.6% flooded cropland vs 1.4% dry-season floor.")
b = m[m.adm3_name.isin(["Balijipeta", "Parvathipuram"])].geometry.union_all().bounds
flood_pair("manyam2026", "Parvathipuram Manyam, cyclonic storm, 20-25 Sep 2026 (this season)", "2026-09-20", "2026-09-25",
           ee.Geometry.Rectangle([b[0] - 0.02, b[1] - 0.02, b[2] + 0.02, b[3] + 0.02]),
           "Same frozen method on this season's storm in the pilot mandals Parvathipuram and Balijipeta.")

# 3. real field photos (Department labelled images) with the trained model's top prediction
pred = pd.read_csv(POC / "data" / "pest_model" / "test_predictions.csv")
for cls, g in pred.groupby("cls"):
    ok = g[g.model_ok]
    row = (ok if len(ok) else g).iloc[0]
    src = POC / "data" / "pest_benchmark" / row.file
    im = Image.open(src).convert("RGB")
    im.thumbnail((640, 640))
    name = f"photo_{cls}.jpg"
    im.save(IMG / name, "JPEG", quality=80, optimize=True)
    man["photos"].append(dict(file=name, truth=cls.replace("_", " "), pred=row.pred.replace("_", " "), ok=bool(row.model_ok)))
(IMG / "manifest.json").write_text(json.dumps(man, indent=1), encoding="utf-8")
print("images:", len(list(IMG.glob("*.jpg"))))
