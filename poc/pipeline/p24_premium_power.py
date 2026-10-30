"""Premium of the Lane 1 product, and how much evidence the available CCE data can carry.

PREMIUM (pure burn cost = mean annual payout as % of sum insured; the insurer adds loading)
  Cover A, season, 2001-2024 (the MODIS record): rainfall-only payout (p10) vs dual trigger (payout only if VCI < 35),
          per district x crop, all mandals of the Kharif districts.
  Cover B, catastrophe, YSR Kadapa: ERA5 rainfall-side payout 2001-2024 (p22 levels) x P(Sentinel-1 confirms | ERA5
          fires), the confirmation rate measured on the 2019-2025 events (Sentinel-1 has no record before 2015).
          Reported with the Wilson 95% interval of that rate. Assumes payout size is independent of confirmation.

EVIDENCE POWER (why the >=75% target can neither be met nor tested with this data)
  - CCE losses are clustered by year (one cyclone hits every mandal), so the 166 mandal-crop-years are not 166
    independent observations: design effect = 1 + (m - 1) x ICC (Kish 1965), ICC of the loss indicator by year.
  - Year-cluster bootstrap (resample whole seasons, 5000 draws) of precision and detection for each system.
  - Correlation over seasons: Fisher z interval for r = 0.75 with the 7 seasons available, and the number of
    seasons needed before a true r = 0.75 has a lower 95% bound above 0.5.
  - Detection: independent loss events needed to estimate a detection rate of 75% to +/-10 points.
Outputs: premium_lane1.json, evidence_power.json
"""
import json

import numpy as np
import pandas as pd
from scipy.stats import norm

from common import DERIVED

DIST = {"11": "YSR Kadapa", "22": "Palnadu", "14": "Parvathipuram Manyam"}


def wilson(h, n, z=1.96):
    p = h / n
    d = 1 + z * z / n
    c, w = (p + z * z / (2 * n)) / d, z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return float(c - w), float(c + w)


# ------------------------------------------------------------------ premium
t = pd.read_parquet(DERIVED / "trigger_annual_payouts.parquet")
v = pd.read_csv(DERIVED / "validation_trigger_vs_vci.csv")[["adm3_id", "year", "vci"]].drop_duplicates(["adm3_id", "year"])
a = t[t.year.between(2001, 2024) & t.district_code.isin(DIST)].merge(v, on=["adm3_id", "year"], how="inner")
a["dual"] = a.pay_pct.where(a.vci < 35, 0.0)
coverA = (a.groupby(["district_code", "crop"]).agg(
    rain_only=("pay_pct", "mean"), dual=("dual", "mean"),
    freq_rain=("pay_pct", lambda s: (s > 0).mean()), freq_dual=("dual", lambda s: (s > 0).mean()),
    mandal_years=("pay_pct", "size")).reset_index())
coverA["district"] = coverA.district_code.map(DIST)
allA = dict(rain_only=float(a.pay_pct.mean()), dual=float(a.dual.mean()),
            freq_rain=float((a.pay_pct > 0).mean()), freq_dual=float((a.dual > 0).mean()))

c = pd.read_parquet(DERIVED / "cat_cover_levels.parquet")
c = c[(c.src == "era5") & (c.district_code == "11") & c.sy.between(2001, 2024)]
j = pd.read_csv(DERIVED / "validation_dual_trigger.csv")
fired = int(j.fire_era5.sum())
conf = int((j.fire_era5 & j.sar_confirms).sum())
lo, hi = wilson(conf, fired)
b_rain = float(c.pay.mean())
coverB = dict(district="YSR Kadapa", rain_side=b_rain, freq_rain=float((c.pay > 0).mean()), confirm_rate=conf / fired,
              confirm_ci=[lo, hi], confirm_n=f"{conf} of {fired}", dual=b_rain * conf / fired, dual_range=[b_rain * lo, b_rain * hi])
ysrA = a[a.district_code == "11"]
prem = dict(coverA=coverA.to_dict("records"), coverA_all=allA, coverB=coverB,
            ysr_total=dict(rain_only=float(ysrA.pay_pct.mean()) + b_rain, dual=float(ysrA.dual.mean()) + coverB["dual"],
                           dual_range=[float(ysrA.dual.mean()) + coverB["dual_range"][0], float(ysrA.dual.mean()) + coverB["dual_range"][1]]),
            years="2001-2024")
(DERIVED / "premium_lane1.json").write_text(json.dumps(prem, indent=1), encoding="utf-8")
print("Cover A burn cost, % SI (2001-2024):\n", coverA.round(2).to_string(index=False))
print("all districts:", {k: round(x, 3) for k, x in allA.items()})
print("Cover B YSR:", {k: (round(x, 2) if isinstance(x, float) else x) for k, x in coverB.items()})
print("YSR Lane 1 total:", prem["ysr_total"])

# ------------------------------------------------------------------ evidence power
j["loss"] = j.kg_ha < j.normal * 0.8
n = len(j)
m = j.groupby("year").size().mean()
# ICC of the binary loss indicator by year (one-way ANOVA estimator)
g = j.groupby("year").loss
k = g.size()
msb = (k * (g.mean() - j.loss.mean()) ** 2).sum() / (len(k) - 1)
msw = ((j.loss - g.transform("mean")) ** 2).sum() / (n - len(k))
m0 = (n - (k ** 2).sum() / n) / (len(k) - 1)
icc = float(max(0.0, (msb - msw) / (msb + (m0 - 1) * msw)))
deff = 1 + (m - 1) * icc
n_eff = n / deff
loss_eff = j.loss.sum() / deff

rng = np.random.default_rng(0)
years = j.year.unique()
by = {y: d for y, d in j.groupby("year")}
SYS = {"Season cover, rainfall only": "fire_season", "Season + ERA5 acute layer": "system_fired_era5",
       "Lane 1 product (dual)": "fire_lane1"}
boot = {}
for lab, col in SYS.items():
    pod, prec = [], []
    for _ in range(5000):
        d = pd.concat([by[y] for y in rng.choice(years, len(years))])
        f, l = d[col].astype(bool), d.loss
        if l.sum():
            pod.append((f & l).sum() / l.sum())
        if f.sum():
            prec.append((f & l).sum() / f.sum())
    f, l = j[col].astype(bool), j.loss
    boot[lab] = dict(pod=float((f & l).sum() / l.sum()), pod_ci=[float(np.percentile(pod, 2.5)), float(np.percentile(pod, 97.5))],
                     precision=float((f & l).sum() / max(1, f.sum())),
                     precision_ci=[float(np.percentile(prec, 2.5)), float(np.percentile(prec, 97.5))] if prec else None,
                     seasons_with_payout=int(j[f].year.nunique()))

S = len(years)
z75, se = np.arctanh(0.75), 1 / np.sqrt(S - 3)
r_ci = [float(np.tanh(z75 - 1.96 * se)), float(np.tanh(z75 + 1.96 * se))]
need_r = int(np.ceil((1.96 / (z75 - np.arctanh(0.5))) ** 2 + 3))
need_events = int(np.ceil(1.96 ** 2 * 0.75 * 0.25 / 0.10 ** 2))
per_season = loss_eff / S
yl = j.groupby("year").agg(loss_pct=("loss_pct", "mean"), share_loss=("loss", "mean")).round(3).reset_index()
pw = dict(n=n, seasons=S, mean_cluster=float(m), icc_year=icc, design_effect=float(deff), n_effective=float(n_eff),
          loss_events=int(j.loss.sum()), loss_events_effective=float(loss_eff),
          bootstrap=boot, r75_ci_with_seasons=r_ci, seasons_needed_r=need_r,
          events_needed_pod=need_events, seasons_needed_pod=int(np.ceil(need_events / per_season)),
          by_year=yl.to_dict("records"))
(DERIVED / "evidence_power.json").write_text(json.dumps(pw, indent=1), encoding="utf-8")
print(f"\nICC(year)={icc:.2f}  design effect={deff:.1f}  effective n={n_eff:.0f} of {n}  effective loss events={loss_eff:.1f}")
for lab, b in boot.items():
    print(f"{lab:30s} POD {b['pod']:.2f} CI {b['pod_ci'][0]:.2f}-{b['pod_ci'][1]:.2f} | precision {b['precision']:.2f} CI {b['precision_ci']}")
print(f"true r=0.75 over {S} seasons -> 95% CI {r_ci[0]:.2f} to {r_ci[1]:.2f}; seasons needed for lower bound > 0.5: {need_r}")
print(f"detection 75% +/-10 pts needs {need_events} independent loss events = about {pw['seasons_needed_pod']} seasons at this district's rate")
