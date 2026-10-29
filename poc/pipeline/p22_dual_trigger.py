"""Lane 1 catastrophe cover (Cover B): consensus rainfall index x Sentinel-1 flood index, validated on CCE.

Declared 2026-10-30, before computing against CCE:
  Index      : maximum 3-day rainfall in the crop season (Jun 1 - Jan 31), per mandal, from each of three
               independent products: CHIRPS, ERA5, GPM IMERG.
  Payout     : per product, linear from its own 1-in-5 level (0%) to its own 1-in-25 level (100%) of the
               seasonal 3-day maximum, 2001-2024 (the common record of all three; same return periods as the
               season cover, p10). Consensus payout = MEDIAN of the products' payouts, i.e. the level that at
               least two of three products support. Each product is judged against its own climatology,
               so its bias cancels; one product's miss or false spike cannot move the median.
  Satellite  : Sentinel-1 flood index = flooded cropland share above the mandal's dry-season false-alarm floor
               in any rain window of that season (gee_py/sar_cce.py, frozen method).
  Dual trigger: consensus payout > 0 AND Sentinel-1 confirms.
  Season cover (Cover A, p10) dual trigger: season payout > 0 AND MODIS VCI < 35 (Kogan 1995) in the same mandal-year.
  Tested     : fired vs CCE loss (yield < 70/80/90 % of leave-one-out normal), YSR Kadapa 2019-2025, by crop.
RESULT and the decision that followed (2026-10-30, AFTER seeing the result above, so it is stated as such):
  The consensus x Sentinel-1 design failed (17 payouts, 2 to real losses): CHIRPS and IMERG flag October 2024, a
  season with ~2% loss. Of the declared candidates only ERA5 beat the base rate. Index qualification gate, applied
  from now on to every candidate and re-run every season: an index may enter the contract only if the lower bound of
  the Wilson 95% interval of its precision (share of payouts that went to a real loss) exceeds the base loss rate.
  The contract's catastrophe cover therefore uses ERA5 x Sentinel-1. Its hits are mostly cyclone Nivar 2020, so it
  must be confirmed on Kharif 2026 CCE before it is relied on.
Outputs: dual_trigger_validation.json, cat_cover_levels.parquet (term-sheet levels per mandal and product).
"""
import glob
import json

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

from common import DERIVED, POC

BASE = (2001, 2024)
RP_T, RP_X = 5, 25
SRC = {"chirps": "rain_chirps_daily.parquet", "era5": "rain_era5_daily.parquet", "imerg": "rain_imerg_daily.parquet"}


def season_max(f):
    r = pd.read_parquet(DERIVED / f).sort_values(["adm3_id", "date"])
    r["r3"] = r.groupby("adm3_id").rain_mm.transform(lambda s: s.rolling(3, min_periods=3).sum())
    r = r[(r.date.dt.month >= 6) | (r.date.dt.month == 1)]
    r["sy"] = np.where(r.date.dt.month == 1, r.date.dt.year - 1, r.date.dt.year)
    # a season counts only when the product has published it to Jan 31 (or to its last day for the live season)
    return r.groupby(["adm3_id", "district_code", "sy"]).r3.max().rename("x").reset_index()


parts = []
for k, f in SRC.items():
    m = season_max(f)
    lv = m[m.sy.between(*BASE)].groupby("adm3_id").x.agg(L5=lambda s: s.quantile(1 - 1 / RP_T),
                                                          L25=lambda s: s.quantile(1 - 1 / RP_X)).reset_index()
    m = m.merge(lv, on="adm3_id")
    m["pay"] = 100 * np.clip((m.x - m.L5) / (m.L25 - m.L5), 0, 1)
    parts.append(m.assign(src=k))
cat = pd.concat(parts)
cat.to_parquet(DERIVED / "cat_cover_levels.parquet", index=False)
wide = cat.pivot_table(index=["adm3_id", "district_code", "sy"], columns="src", values="pay").reset_index()
wide["consensus"] = wide[list(SRC)].median(axis=1, skipna=True)
wide["n_src"] = wide[list(SRC)].notna().sum(axis=1)

# Sentinel-1 flood index per mandal-season (YSR windows), net of the dry-season false-alarm floor
fl = pd.concat([pd.read_parquet(f) for f in glob.glob(str(POC / "data" / "gee_out" / "out_flood_mandal_*.parquet"))])
ctrl = fl[fl.event_id.str.startswith("CTRL_")]
noise = (ctrl.crop_flood_ha / ctrl.cropland_ha).groupby(ctrl.mid).max()
sar = pd.concat([pd.read_parquet(f) for f in glob.glob(str(POC / "data" / "gee_out" / "out_sarcce_*.parquet"))])
sar["share"] = sar.crop_flood_ha / sar.cropland_ha
sar["floor"] = sar.mid.map(noise)
sar["excess"] = sar.share - sar.floor
d = pd.to_datetime(sar.event_id.str[-8:], format="%Y%m%d")
sar["sy"] = np.where(d.dt.month == 1, d.dt.year - 1, d.dt.year)
sar["within_72h"] = sar.hours_after_event_end <= 72
s_idx = sar.groupby(["mid", "sy"]).agg(sar_excess=("excess", "max"), sar_hours=("hours_after_event_end", "min"),
                                       sar_windows=("event_id", "nunique")).reset_index()
s_idx["sar_confirms"] = s_idx.sar_excess > 0

# CCE join (losses from p15)
v = pd.read_csv(DERIVED / "validation_trigger_vs_cce.csv")
j = v.merge(wide, left_on=["adm3_id", "year"], right_on=["adm3_id", "sy"], how="left")
j = j.merge(s_idx, left_on=["adm3_id", "year"], right_on=["mid", "sy"], how="left", suffixes=("", "_s"))
j["sar_confirms"] = j.sar_confirms.fillna(False).astype(bool)
for k in list(SRC) + ["consensus"]:
    j[f"fire_{k}"] = j[k].fillna(0) > 0
j["fire_dual"] = j.fire_consensus & j.sar_confirms
j["fire_dual_era5"] = j.fire_era5 & j.sar_confirms
j["fire_sar"] = j.sar_confirms
j["fire_season"] = j.pay_pct > 0
vci = pd.read_csv(DERIVED / "validation_trigger_vs_vci.csv")[["adm3_id", "year", "vci"]].drop_duplicates(["adm3_id", "year"])
j = j.merge(vci, on=["adm3_id", "year"], how="left")
j["fire_vci"] = j.vci < 35
j["fire_season_dual"] = j.fire_season & j.fire_vci
j["fire_lane1"] = j.fire_season_dual | j.fire_dual_era5   # Lane 1 product: both covers, each a dual trigger

ROWS = [("fire_season", "Season cover, rainfall only (WBCIS structure)"),
        ("fire_vci", "MODIS VCI < 35 alone"), ("fire_season_dual", "Season cover dual: rainfall AND VCI"),
        ("fire_chirps", "Cat cover, CHIRPS alone"), ("fire_era5", "Cat cover, ERA5 alone"),
        ("fire_imerg", "Cat cover, IMERG alone"), ("fire_consensus", "Cat cover, 3-source consensus"),
        ("fire_sar", "Sentinel-1 flood alone"), ("fire_dual", "Dual trigger: consensus AND Sentinel-1"),
        ("fire_dual_era5", "Dual trigger: ERA5 AND Sentinel-1"),
        ("fire_lane1", "Lane 1 product: both covers, dual-triggered")]


def wilson(h, n, z=1.96):
    if n == 0:
        return None, None
    p = h / n
    d = 1 + z * z / n
    c, w = (p + z * z / (2 * n)) / d, z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return float(c - w), float(c + w)


def stats(df, col):
    out = []
    for lvl in (70, 80, 90):
        loss = df.kg_ha < df.normal * lvl / 100
        f = df[col]
        tp = int((f & loss).sum())
        lo, hi = wilson(tp, int(f.sum()))
        out.append(dict(indemnity=lvl, fired=int(f.sum()), losses=int(loss.sum()), hits=tp, prec_lo=lo, prec_hi=hi,
                        qualifies=bool(lo is not None and lo > loss.mean()),
                        hits_by_year={int(y): int(g.sum()) for y, g in (f & loss).groupby(df.year) if g.sum()},
                        pod=tp / max(1, loss.sum()), precision=tp / max(1, f.sum()) if f.sum() else None,
                        agreement=float((f == loss).mean()), base_rate=float(loss.mean())))
    return out


res = {"n": int(len(j)), "declared": "2026-10-30", "rows": []}
for col, lab in ROWS:
    for crop in ["All", "Paddy", "Cotton"]:
        df = j if crop == "All" else j[j.crop == crop]
        for s in stats(df, col):
            res["rows"].append(dict(test=lab, crop=crop, **s))
rho, p = spearmanr(j.consensus.fillna(0), j.loss_pct)
res["spearman_consensus_vs_loss"] = dict(rho=float(rho), p=float(p))
res["sar_coverage"] = dict(mandal_seasons_with_sar=int(j.sar_windows.notna().sum()),
                           within_72h=int((j.sar_hours <= 72).sum()))
res["contract"] = {"season": "fire_season_dual", "catastrophe": "fire_dual_era5"}
res["by_year"] = j.groupby("year").agg(loss=("loss_pct", "mean"), consensus=("fire_consensus", "mean"),
                                       sar=("fire_sar", "mean"), dual=("fire_dual", "mean"), dual_era5=("fire_dual_era5", "mean"),
                                       season=("fire_season", "mean"),
                                       season_dual=("fire_season_dual", "mean"),
                                       lane1=("fire_lane1", "mean")).round(3).reset_index().to_dict("records")
j.to_csv(DERIVED / "validation_dual_trigger.csv", index=False)
(DERIVED / "dual_trigger_validation.json").write_text(json.dumps(res, indent=1), encoding="utf-8")

t = pd.DataFrame(res["rows"])
print(t[(t.indemnity == 80) & (t.crop == "All")].drop(columns=["indemnity", "crop"]).round(2).to_string(index=False))
print("\nSpearman(consensus payout, CCE loss):", round(rho, 2), "p", round(p, 3))
print("by year:\n", pd.DataFrame(res["by_year"]).to_string(index=False))
print("SAR coverage:", res["sar_coverage"])
