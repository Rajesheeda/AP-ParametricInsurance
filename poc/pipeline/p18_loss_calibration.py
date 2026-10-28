"""Estimated yield loss per trigger type, calibrated on real CCE losses (YSR Kadapa, Kharif 2019-2025).

For each trigger outcome, the distribution of CCE yield loss (% below the mandal's leave-one-out normal):
  acute   : ERA5 acute event (extreme rain >= IMD heavy at peak, or cyclone) in the crop season
  drought : season trigger fired (deficit / dry spell driven)
  none    : nothing fired
Median and inter-quartile range are attached to the pilot assessment as "estimated yield loss", labelled
with the calibration sample size. Output: loss_calibration.json
"""
import json

import numpy as np
import pandas as pd

from common import DERIVED

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
                  share_loss_over_20=float((d > 20).mean()))
    print(f"{k:8s} n={cal[k]['n']:3d} years {cal[k]['years']}  median loss {cal[k]['median']:.0f}%  "
          f"IQR {cal[k]['q25']:.0f}-{cal[k]['q75']:.0f}%  share with >20% loss {cal[k]['share_loss_over_20']:.0%}")
(DERIVED / "loss_calibration.json").write_text(json.dumps(cal, indent=1), encoding="utf-8")
