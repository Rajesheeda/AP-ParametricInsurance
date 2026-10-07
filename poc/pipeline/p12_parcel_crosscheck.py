"""Parcel-level cross-sensor check, cyclone Michaung (Dec 2023), YSR Kadapa.

Do parcels that Sentinel-1 mapped as flooded lose more greenness (Sentinel-2 NDVI) than parcels of the
SAME crop and SAME sowing fortnight that were not flooded? (cohort-normalized change, no thresholds)
  pre  = max NDVI over 19 Oct - 27 Nov 2023 windows;  post = max NDVI over 8 - 27 Dec 2023 windows
  anomaly = (post - pre) minus the cohort median (crop x sowing fortnight, purity >= 0.8)
"""
import glob

import geopandas as gpd
import numpy as np
import pandas as pd
from scipy.stats import spearmanr

from common import DERIVED, POC

ts = pd.concat([pd.read_parquet(f) for f in glob.glob(str(POC / "data" / "gee_out" / "out_ts_parcels_2023_*.parquet"))])
pre_c = [c for c in ["ndvi_1019", "ndvi_1029", "ndvi_1108", "ndvi_1118"] if c in ts]
post_c = [c for c in ["ndvi_1208", "ndvi_1218"] if c in ts]
ts["pre"], ts["post"] = ts[pre_c].max(axis=1), ts[post_c].max(axis=1)
fl = pd.read_parquet(POC / "data" / "gee_out" / "out_flood_parcel_11_20231205_MICHAUNG.parquet").rename(columns={"mean": "flood_frac"})
attrs = gpd.read_file(DERIVED / "gee_upload" / "ysr_parcels.shp", ignore_geometry=True)[["pid", "mandal", "crop23", "pur23", "sow23"]]
# cadastral objectid is not unique (8.5k duplicates in the APAIMS file): drop ambiguous ids everywhere
attrs["pid"] = attrs.pid.astype(int)
attrs["pur23"] = pd.to_numeric(attrs.pur23, errors="coerce")
amb = set(attrs.pid[attrs.pid.duplicated(keep=False)])
attrs, ts, fl = (x[~x.pid.isin(amb)] for x in (attrs, ts, fl))
print(f"ambiguous parcel ids excluded: {len(amb):,}")
d = ts[["pid", "pre", "post"]].merge(fl[["pid", "flood_frac"]], on="pid").merge(attrs, on="pid")
d = d[(d.pur23 >= 0.8) & d.crop23.notna() & d.pre.notna() & d.post.notna()].copy()
d["sow"] = pd.to_datetime(d.sow23, errors="coerce")
d = d[d.sow.notna()]
d["cohort"] = d.crop23 + "|" + d.sow.dt.strftime("%m") + np.where(d.sow.dt.day <= 15, "a", "b")
d["dndvi"] = d.post - d.pre
d["anom"] = d.dndvi - d.groupby("cohort").dndvi.transform("median")
d = d[d.groupby("cohort").pid.transform("size") >= 30]   # cohorts big enough for a stable median
d["flood_bin"] = pd.cut(d.flood_frac, [-0.001, 0, 0.1, 0.5, 1.0], labels=["none", "0-10%", "10-50%", ">50%"])
print(f"parcels analysed: {len(d):,} in {d.cohort.nunique()} crop x sowing-fortnight cohorts; flooded (>0): {(d.flood_frac > 0).sum():,}")
print("\ncohort-normalized NDVI change by SAR flooded fraction (negative = greenness lost vs same-cohort peers):")
print(d.groupby("flood_bin", observed=True).anom.agg(["size", "median", "mean"]).round(3).to_string())
rho, p = spearmanr(d.flood_frac, d.anom)
print(f"\nspearman(flood fraction, NDVI anomaly) = {rho:+.3f} (p={p:.1e})")
for crop, g in d.groupby("crop23"):
    if (g.flood_frac > 0).sum() >= 30:
        r, pp = spearmanr(g.flood_frac, g.anom)
        print(f"  {crop:14s} n={len(g):6d} flooded={int((g.flood_frac > 0).sum()):5d} spearman={r:+.3f} (p={pp:.1e}) "
              f"median anom flooded={g[g.flood_frac > 0].anom.median():+.3f} vs none={g[g.flood_frac == 0].anom.median():+.3f}")
d.to_parquet(DERIVED / "crosscheck_michaung_2023.parquet", index=False)

# Standing-crop gate: parcel counts only if the event falls inside its own season
# (e-Panta sowing date + FAO-56 total crop duration, Table 11).
DUR = {"Paddy": 150, "Cotton": 195, "Groundnut": 130, "Red Chillies": 120}
EVENT = pd.Timestamp("2023-12-04")
d["season_end"] = d.sow + pd.to_timedelta(d.crop23.map(DUR), unit="D")
d["standing"] = (d.sow <= EVENT) & (d.season_end >= EVENT)
f = d[d.flood_frac > 0]
print(f"\nSAR-flagged parcels: {len(f):,}; with a standing crop on {EVENT.date()}: {int(f.standing.sum()):,} "
      f"({f.standing.mean():.0%}); gated out as harvested / not sown: {int((~f.standing).sum()):,}")
for name, g in [("standing", d[d.standing]), ("not standing", d[~d.standing])]:
    fl, nf = g[g.flood_frac > 0], g[g.flood_frac == 0]
    if len(fl) >= 20:
        r, pp = spearmanr(g.flood_frac, g.anom)
        print(f"  {name:13s}: flooded n={len(fl):4d} median anom {fl.anom.median():+.3f} vs unflooded {nf.anom.median():+.3f}; spearman={r:+.3f} (p={pp:.1e})")
d.to_parquet(DERIVED / "crosscheck_michaung_2023.parquet", index=False)
