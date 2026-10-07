"""Interim validation: rainfall-trigger season stress vs MODIS Vegetation Condition Index (independent sensor).

VCI (Kogan 1995) per mandal-year from Kharif mid-season NDVI (Sep-Oct mean, MOD13Q1, cropland only),
scaled by the mandal's own 2001-2025 min/max. VCI < 35 = vegetation stress (Kogan; GoI Drought Manual 2016).
Compared with trigger season stress S (crop-averaged), separately for deficit/dry-driven seasons,
because NDVI responds to drought but not reliably to excess-rain damage.
Labelled INTERIM: this checks the trigger against a second sensor, not against PMFBY/CCE losses.
"""
import numpy as np
import pandas as pd
from scipy.stats import spearmanr

from common import DERIVED, POC

m = pd.read_parquet(POC / "data" / "gee_out" / "out_modis_ndvi_2001_2026.parquet")
cols = [c for c in m.columns if c.startswith("kmid_")]
v = m.melt(id_vars=["mid", "dist"], value_vars=cols, var_name="k", value_name="ndvi")
v["year"] = v.k.str[-4:].astype(int)
v = v[v.year <= 2025].dropna(subset=["ndvi"])
g = v.groupby("mid").ndvi
v["vci"] = 100 * (v.ndvi - g.transform("min")) / (g.transform("max") - g.transform("min"))

t = pd.read_parquet(DERIVED / "trigger_annual_payouts.parquet")
t = t[t.season == "Kharif"]
s = t.groupby(["adm3_id", "year"]).agg(S=("S", "mean"), pay=("pay_pct", "mean"),
                                       driver=("driver_peril", lambda x: x.mode().iloc[0])).reset_index()
j = s.merge(v.rename(columns={"mid": "adm3_id"}), on=["adm3_id", "year"])
j = j[j.year >= 2001]
j.to_csv(DERIVED / "validation_trigger_vs_vci.csv", index=False)

def report(df, label):
    rho, p = spearmanr(df.S, df.vci)
    fired, stressed = df.pay > 0, df.vci < 35
    hits = (fired & stressed).sum()
    pod = hits / stressed.sum() if stressed.sum() else np.nan          # share of VCI-stress seasons the trigger caught
    far = (fired & ~stressed).sum() / fired.sum() if fired.sum() else np.nan  # share of trigger seasons without VCI stress
    agree = (fired == stressed).mean()
    print(f"{label:38s} n={len(df):5d}  spearman(S,VCI)={rho:+.2f} (p={p:.1e})  POD={pod:.2f}  FAR={far:.2f}  agreement={agree:.2f}")

print("Kharif seasons 2001-2025, mandal level")
report(j, "all drivers")
report(j[j.driver.isin(["deficit", "dry"])], "deficit / dry-spell driven")
report(j[j.driver == "excess"], "excess-rain driven")
for d, sub in j.groupby("dist"):
    report(sub[sub.driver.isin(["deficit", "dry"])], f"  district {d}, deficit/dry")
yr = j.groupby("year").agg(S=("S", "mean"), vci=("vci", "mean"), fired=("pay", lambda x: (x > 0).mean())).round(2)
print("\ndistrict-pooled by year (S high = stress; VCI low = stress):\n", yr.loc[2014:].to_string())

# District x year (fiscal-planning scale in the PPT): mean S vs mean VCI over the district's mandals.
dy = j.groupby(["dist", "year"]).agg(S=("S", "mean"), vci=("vci", "mean")).reset_index()
rho, p = spearmanr(dy.S, dy.vci)
print(f"\ndistrict x year: n={len(dy)}  spearman(S,VCI)={rho:+.2f} (p={p:.1e})")
for d, sub in dy.groupby("dist"):
    r, pp = spearmanr(sub.S, sub.vci)
    print(f"  district {d}: n={len(sub)} spearman={r:+.2f} (p={pp:.2f})")
