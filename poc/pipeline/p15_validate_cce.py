"""Validation of the rainfall triggers against real CCE yields (Department), YSR Kadapa, Kharif 2019-2025.

Declared before computing (2026-10-27):
  Actual yield   : CCE plot yield, mean of Exp1/Exp2 per village, converted to kg/ha from the plot size,
                   averaged per mandal x crop x year.
  Normal yield   : mean of the same mandal x crop over the OTHER CCE years (leave-one-out), so a year is
                   never part of its own baseline.
  Loss %         : max(0, (normal - actual) / normal) x 100.
  Loss event     : actual < normal x indemnity level, reported for the three PMFBY indemnity levels 70/80/90 %.
  Trigger        : season stress S and payout % from p10 (CHIRPS, WBCIS structure), same mandal x crop x year.
  Metrics        : Spearman(S, loss %); agreement = share of mandal-crop-years where "trigger fired" equals
                   "loss event"; hit rate (POD) and false-alarm ratio (FAR). Minimum 3 CCE years per mandal-crop.
"""
import glob

import numpy as np
import pandas as pd
from rapidfuzz import fuzz, process
from scipy.stats import spearmanr

from common import DERIVED, norm_name

SRC = r"C:\AP-Agri-Common\data"
FILES = ["Crop Yield Estimation & Market Intelligence (additional).csv", "Automated Crop Sowing Assessment.csv",
         "AI-Based Crop Yield Intelligence.csv", "Smart Drought Forecasting System.csv"]
CROP = {"PADDY (I)": "Paddy", "PADDY (UI)": "Paddy", "PADDY": "Paddy", "COTTON": "Cotton", "GROUNDNUT": "Groundnut",
        "GROUNDNUT (UI)": "Groundnut", "GROUNDNUT (I)": "Groundnut"}

a = pd.concat([pd.read_csv(f"{SRC}\\{f}", dtype=str) for f in FILES], ignore_index=True).drop_duplicates()
a = a[a.District.str.contains("Kadapa", case=False, na=False) & (a.Season == "Kharif")].copy()
a["crop"] = a.Crop.str.strip().str.upper().map(CROP)
a = a[a.crop.notna()].copy()
dims = a["Plot Size"].str.extract(r"(\d+(?:\.\d+)?)\s*\*\s*(\d+(?:\.\d+)?)").astype(float)
a["plot_m2"] = dims[0] * dims[1]
for c in ["Plot Yield Exp1", "Plot Yield Exp2"]:
    a[c] = pd.to_numeric(a[c], errors="coerce")
a["kg_ha"] = a[["Plot Yield Exp1", "Plot Yield Exp2"]].mean(axis=1) / a.plot_m2 * 10000
a["year"] = a.Year.astype(int)
a = a[a.kg_ha > 0]
print("YSR Kharif CCE villages:", len(a), "| plot sizes:", a["Plot Size"].value_counts().head(3).to_dict())

# mandal names -> geoBoundaries ids used by the triggers
cent = pd.read_csv(DERIVED / "poc_mandal_centroids.csv", dtype={"district_code": str})
ysr = cent[cent.district_code == "11"]
keys = ysr.adm3_name.map(norm_name).tolist()
mm = {m: process.extractOne(norm_name(m), keys, scorer=fuzz.ratio) for m in a.Mandal.unique()}
a["adm3_id"] = a.Mandal.map(lambda m: ysr.adm3_id.iloc[mm[m][2]] if mm[m][1] >= 80 else None)
print("mandals matched:", a.dropna(subset=["adm3_id"]).Mandal.nunique(), "of", a.Mandal.nunique(),
      "| unmatched:", sorted({m for m, v in mm.items() if v[1] < 80}))

y = a.dropna(subset=["adm3_id"]).groupby(["adm3_id", "Mandal", "crop", "year"]).agg(kg_ha=("kg_ha", "mean"), villages=("kg_ha", "size")).reset_index()
y = y[y.groupby(["adm3_id", "crop"]).year.transform("nunique") >= 3]
g = y.groupby(["adm3_id", "crop"]).kg_ha
y["normal"] = (g.transform("sum") - y.kg_ha) / (g.transform("count") - 1)
y["loss_pct"] = (100 * (y.normal - y.kg_ha) / y.normal).clip(lower=0)

t = pd.read_parquet(DERIVED / "trigger_annual_payouts.parquet")
t = t[(t.district_code == "11") & (t.season == "Kharif")][["adm3_id", "crop", "year", "S", "pay_pct", "driver_peril"]]
j = y.merge(t, on=["adm3_id", "crop", "year"])
j.to_csv(DERIVED / "validation_trigger_vs_cce.csv", index=False)
print(f"\nmandal-crop-years with CCE and trigger: {len(j)} ({j.adm3_id.nunique()} mandals; {j.groupby('crop').size().to_dict()})")


def report(df, label):
    rho, p = spearmanr(df.S, df.loss_pct)
    out = [f"{label:28s} n={len(df):4d}  Spearman(S, loss)={rho:+.2f} (p={p:.3f})"]
    fired = df.pay_pct > 0
    for lvl in (70, 80, 90):
        loss = df.kg_ha < df.normal * lvl / 100
        agree = (fired == loss).mean()
        pod = (fired & loss).sum() / max(1, loss.sum())
        far = (fired & ~loss).sum() / max(1, fired.sum())
        out.append(f"   indemnity {lvl}%: loss events {int(loss.sum()):3d}  agreement {agree:.0%}  POD {pod:.2f}  FAR {far:.2f}")
    print("\n".join(out))


report(j, "all crops")
for c, d in j.groupby("crop"):
    report(d, c)
report(j[j.Mandal.str.upper().str.startswith(("CHAPAD", "KHAJIP"))], "pilot: Chapad + Khajipet")
print("\nyear pattern (mean over mandal-crops):")
print(j.groupby("year").agg(S=("S", "mean"), loss=("loss_pct", "mean"), fired=("pay_pct", lambda s: (s > 0).mean()), n=("S", "size")).round(2).to_string())

# Full system as designed before the CCE data arrived: season trigger OR a qualifying acute event during the
# crop season (Jun 1 - Jan 31): extreme / unseasonal rain with peak day >= IMD heavy (64.5 mm), or an
# IBTrACS cyclone >= 34 kt within 150 km. Same qualifying rule as p07 / p13; nothing re-tuned on CCE.
ev = pd.read_csv(DERIVED / "event_catalogue_chirps.csv", dtype={"district_code": str})
ev["start"] = pd.to_datetime(ev.start)
ev["season_year"] = np.where(ev.start.dt.month == 1, ev.start.dt.year - 1, ev.start.dt.year)
q = ev[((ev.type.isin(["extreme_rain", "unseasonal_rain"]) & (ev.peak_day_mm >= 64.5)) | (ev.type == "cyclone"))
       & ((ev.start.dt.month >= 6) | (ev.start.dt.month == 1))]
acute = q.groupby(["adm3_id", "season_year"]).type.agg(lambda s: "+".join(sorted(set(s)))).rename("acute_event")
j = j.merge(acute, left_on=["adm3_id", "year"], right_index=True, how="left")
j["season_fired"] = j.pay_pct > 0
j["system_fired"] = j.season_fired | j.acute_event.notna()
j.to_csv(DERIVED / "validation_trigger_vs_cce.csv", index=False)


def report_bin(df, col, label):
    out = [f"{label:40s} n={len(df):4d}"]
    for lvl in (70, 80, 90):
        loss = df.kg_ha < df.normal * lvl / 100
        f = df[col]
        out.append(f"   indemnity {lvl}%: agreement {(f == loss).mean():.0%}  POD {(f & loss).sum() / max(1, loss.sum()):.2f}"
                   f"  FAR {(f & ~loss).sum() / max(1, f.sum()):.2f}  (fired {int(f.sum())}, losses {int(loss.sum())})")
    print("\n".join(out))


print("\n=== Full system (season trigger OR acute event) vs CCE loss")
report_bin(j, "season_fired", "season trigger only")
report_bin(j, "system_fired", "season OR acute (full system)")
for c, d in j.groupby("crop"):
    report_bin(d, "system_fired", f"full system, {c}")
print("\nby year:", j.groupby("year").agg(loss=("loss_pct", "mean"), season=("season_fired", "mean"), system=("system_fired", "mean")).round(2).to_dict("index"))

# Sensitivity to the rainfall source of the acute layer. Both catalogues were built before the CCE data
# arrived (ERA5: p05 screening run, 2026-10-01; CHIRPS: p05 rerun, 2026-10-07). Same qualifying rule.
print("\n=== Acute layer from ERA5 instead of CHIRPS (same rule)")
e5 = pd.read_csv(DERIVED / "event_catalogue_era5.csv", dtype={"district_code": str})
e5["start"] = pd.to_datetime(e5.start)
e5["season_year"] = np.where(e5.start.dt.month == 1, e5.start.dt.year - 1, e5.start.dt.year)
q5 = e5[((e5.type.isin(["extreme_rain", "unseasonal_rain"]) & (e5.peak_day_mm >= 64.5)) | (e5.type == "cyclone"))
        & ((e5.start.dt.month >= 6) | (e5.start.dt.month == 1))]
a5 = q5.groupby(["adm3_id", "season_year"]).size().rename("acute_era5")
j = j.merge(a5, left_on=["adm3_id", "year"], right_index=True, how="left")
j["system_fired_era5"] = j.season_fired | j.acute_era5.notna()
report_bin(j, "system_fired_era5", "season OR acute (ERA5)")
for c, d in j.groupby("crop"):
    report_bin(d, "system_fired_era5", f"season OR acute (ERA5), {c}")
print("by year:", j.groupby("year").agg(loss=("loss_pct", "mean"), era5_system=("system_fired_era5", "mean")).round(2).to_dict("index"))
j.to_csv(DERIVED / "validation_trigger_vs_cce.csv", index=False)

# GPM IMERG V07 as a third, independent rainfall source and a multi-source consensus. Declared 2026-10-30
# before computing: same qualifying rule as above on the IMERG catalogue (p05, own 2000-2024 climatology, so each
# product is judged against its own record and its bias cancels). "Any of 3" fires when any product flags an
# acute event in that mandal-season; "2 of 3" when at least two do (cyclones come from IBTrACS in all three).
im_f = DERIVED / "event_catalogue_imerg.csv"
if im_f.exists():
    print("\n=== Acute layer from GPM IMERG and multi-source consensus (same rule)")
    ei = pd.read_csv(im_f, dtype={"district_code": str})
    ei["start"] = pd.to_datetime(ei.start)
    ei["season_year"] = np.where(ei.start.dt.month == 1, ei.start.dt.year - 1, ei.start.dt.year)
    qi = ei[((ei.type.isin(["extreme_rain", "unseasonal_rain"]) & (ei.peak_day_mm >= 64.5)) | (ei.type == "cyclone"))
            & ((ei.start.dt.month >= 6) | (ei.start.dt.month == 1))]
    j = j.merge(qi.groupby(["adm3_id", "season_year"]).size().rename("acute_imerg"), left_on=["adm3_id", "year"],
                right_index=True, how="left")
    votes = j[["acute_event", "acute_era5", "acute_imerg"]].notna().sum(axis=1)
    j["system_fired_imerg"] = j.season_fired | j.acute_imerg.notna()
    j["system_fired_any3"] = j.season_fired | (votes >= 1)
    j["system_fired_2of3"] = j.season_fired | (votes >= 2)
    for col, lab in [("system_fired_imerg", "season OR acute (IMERG)"), ("system_fired_any3", "season OR acute (any of 3)"),
                     ("system_fired_2of3", "season OR acute (2 of 3)")]:
        report_bin(j, col, lab)
    print("by year:", j.groupby("year").agg(loss=("loss_pct", "mean"), imerg=("system_fired_imerg", "mean"),
                                            any3=("system_fired_any3", "mean")).round(2).to_dict("index"))
    j.to_csv(DERIVED / "validation_trigger_vs_cce.csv", index=False)

# Summary for the dashboard / report
import json  # noqa: E402

summary = {"n": int(len(j)), "mandals": int(j.adm3_id.nunique()), "crops": j.groupby("crop").size().to_dict(),
           "years": [int(y) for y in sorted(j.year.unique())], "systems": [], "by_year": []}
for col, label in [("season_fired", "Season trigger only (CHIRPS)"),
                   ("system_fired", "Season + acute event (CHIRPS)"),
                   ("system_fired_era5", "Season + acute event (ERA5)"),
                   ("system_fired_imerg", "Season + acute event (GPM IMERG)"),
                   ("system_fired_any3", "Season + acute event (any of 3 sources)"),
                   ("system_fired_2of3", "Season + acute event (2 of 3 sources)")]:
    if col not in j:
        continue
    for lvl in (70, 80, 90):
        loss = j.kg_ha < j.normal * lvl / 100
        f = j[col]
        summary["systems"].append(dict(system=label, indemnity=lvl, agreement=float((f == loss).mean()),
                                       pod=float((f & loss).sum() / max(1, loss.sum())),
                                       far=float((f & ~loss).sum() / max(1, f.sum())),
                                       fired=int(f.sum()), losses=int(loss.sum())))
for yr, d in j.groupby("year"):
    summary["by_year"].append(dict(year=int(yr), loss_pct=float(d.loss_pct.mean()), n=int(len(d)),
                                   season=float(d.season_fired.mean()), chirps=float(d.system_fired.mean()),
                                   era5=float(d.system_fired_era5.mean()),
                                   imerg=float(d.system_fired_imerg.mean()) if "system_fired_imerg" in d else None,
                                   any3=float(d.system_fired_any3.mean()) if "system_fired_any3" in d else None))
rho, p = spearmanr(j.S, j.loss_pct)
summary["spearman_season"] = dict(rho=float(rho), p=float(p))
(DERIVED / "validation_cce_summary.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
print("summary written")
