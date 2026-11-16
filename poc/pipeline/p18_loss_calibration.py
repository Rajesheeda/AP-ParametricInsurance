"""Estimated yield loss per trigger type, calibrated on real CCE losses (YSR Kadapa, Kharif 2019-2025).

For each trigger outcome, the distribution of CCE yield loss (% below the mandal's leave-one-out normal):
  acute   : ERA5 acute event (extreme rain >= IMD heavy at peak, or cyclone) in the crop season
  drought : season trigger fired (deficit / dry spell driven)
  none    : nothing fired
Median and inter-quartile range are attached to the pilot assessment as "estimated yield loss", labelled
with the calibration sample size. share_loss_33 (Wilson 95% CI) is the share at or above the SDRF input-subsidy
line (crop loss >= 33%, MHA norms 2022-26); p26 uses it to size the relief estimate. Mandal-years of one event are
correlated (ICC, p24), so the CI is narrower than the true uncertainty. Output: loss_calibration.json
"""
import json

import numpy as np
import pandas as pd

from common import DERIVED


def wilson(h, n, z=1.96):
    if n == 0:
        return None, None
    p = h / n
    d = 1 + z * z / n
    c, w = (p + z * z / (2 * n)) / d, z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return float(c - w), float(c + w)


j = pd.read_csv(DERIVED / "validation_trigger_vs_cce.csv")
groups = {
    "acute": j.acute_era5.notna(),
    "drought": (j.pay_pct > 0) & j.driver_peril.isin(["deficit", "dry"]) & j.acute_era5.isna(),
    "none": ~(j.pay_pct > 0) & j.acute_era5.isna(),
}
cal = {}
for k, m in groups.items():
    d = j[m].loss_pct
    cal[k] = dict(n=int(len(d)), years=sorted(int(y) for y in j[m].year.unique()),
                  median=float(d.median()), q25=float(d.quantile(0.25)), q75=float(d.quantile(0.75)),
                  share_loss_over_20=float((d > 20).mean()),
                  share_loss_33=float((d >= 33).mean()), share_loss_33_ci=wilson(int((d >= 33).sum()), len(d)))
    print(f"{k:8s} n={cal[k]['n']:3d} years {cal[k]['years']}  median loss {cal[k]['median']:.0f}%  "
          f"IQR {cal[k]['q25']:.0f}-{cal[k]['q75']:.0f}%  share with >20% loss {cal[k]['share_loss_over_20']:.0%}  "
          f">=33% {cal[k]['share_loss_33']:.0%} (CI {cal[k]['share_loss_33_ci'][0]:.0%}-{cal[k]['share_loss_33_ci'][1]:.0%})")
(DERIVED / "loss_calibration.json").write_text(json.dumps(cal, indent=1), encoding="utf-8")
