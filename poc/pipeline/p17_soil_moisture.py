"""Soil moisture confirmation of drought triggers, validated against CCE (YSR Kadapa).

Declared before computing (2026-10-28):
  Window     : the crop's FAO-56 mid (reproductive) stage for that mandal and year (from p10).
  SM index   : mean monthly soil moisture over the months overlapping that window; percentile within the
               mandal's own record for the same crop window (ERA5-Land root zone: 2000-2024 baseline;
               SMAP surface: 2016-2024 baseline).
  Confirmed  : drought trigger fired (p10 payout > 0, driver deficit or dry spell) AND SM percentile <= 20 %
               (the same 1-in-5 return period as the trigger).
  Test       : precision (share with real CCE loss < 80% of normal) and POD vs the unconfirmed drought trigger.
Outputs: soil_moisture_index.parquet (all POC mandals, crops, years) for the assessment; console report.
"""
import numpy as np
import pandas as pd

from common import DERIVED

sm = pd.read_parquet(DERIVED / "soil_moisture_monthly.parquet")
ph = pd.read_parquet(DERIVED / "trigger_phase_stress.parquet")
mid = ph[ph.phase == "mid"][["adm3_id", "district_code", "season", "crop", "year", "start", "end"]].copy()
mid["start"], mid["end"] = pd.to_datetime(mid.start), pd.to_datetime(mid.end)

rows = []
for src, g in sm.groupby("source"):
    s = g.set_index(["adm3_id", "month"]).sm
    for r in mid.itertuples():
        months = pd.date_range(r.start.to_period("M").to_timestamp(), r.end.to_period("M").to_timestamp(), freq="MS")
        v = [s.get((r.adm3_id, mo)) for mo in months]
        v = [x for x in v if x is not None and not np.isnan(x)]
        if v:
            rows.append(dict(adm3_id=r.adm3_id, district_code=r.district_code, season=r.season, crop=r.crop,
                             year=r.year, source=src, sm=float(np.mean(v))))
x = pd.DataFrame(rows)
base_years = {"era5land_root": (2000, 2024), "smap_surface": (2016, 2024)}


def pct(g):
    lo, hi = base_years[g.name[0]]
    b = np.sort(g[g.year.between(lo, hi)].sm.values)
    g["sm_pct"] = 100 * np.searchsorted(b, g.sm.values, side="right") / (len(b) + 1) if len(b) else np.nan
    return g


x = x.groupby(["source", "adm3_id", "crop", "season"], group_keys=False).apply(pct)
wide = x.pivot_table(index=["adm3_id", "district_code", "season", "crop", "year"], columns="source", values="sm_pct").reset_index()
wide.columns.name = None
wide.to_parquet(DERIVED / "soil_moisture_index.parquet", index=False)
print("soil moisture index rows:", len(wide), "| years ERA5-Land", int(wide.year.min()), "-", int(wide.year.max()))

# validation against CCE (YSR)
j = pd.read_csv(DERIVED / "validation_trigger_vs_cce.csv").merge(wide, on=["adm3_id", "crop", "year"], how="left")
j["loss80"] = j.kg_ha < 0.8 * j.normal
drought = (j.pay_pct > 0) & j.driver_peril.isin(["deficit", "dry"])
print(f"\nCCE mandal-crop-years {len(j)}; base loss rate {j.loss80.mean():.0%}; drought trigger fired {int(drought.sum())}")


def show(mask, label):
    d = j[mask]
    pod = (mask & j.loss80).sum() / max(1, j.loss80.sum())
    print(f"  {label:48s} fired {len(d):3d}  precision {d.loss80.mean() if len(d) else float('nan'):.0%}  POD {pod:.0%}")


show(drought, "drought trigger alone")
for src in ("era5land_root", "smap_surface"):
    show(drought & (j[src] <= 20), f"drought trigger AND {src} <= 20th pct")
    show(j[src] <= 20, f"{src} <= 20th pct alone")
j.to_csv(DERIVED / "validation_soil_moisture_cce.csv", index=False)

import json  # noqa: E402

summ = {"n": int(len(j)), "base_rate": float(j.loss80.mean()), "rows": []}
for label, mask in [("Drought trigger alone", drought),
                    ("Drought trigger + dry root zone (ERA5-Land)", drought & (j.era5land_root <= 20)),
                    ("Drought trigger + dry surface (SMAP satellite)", drought & (j.smap_surface <= 20)),
                    ("Dry root zone alone (ERA5-Land)", j.era5land_root <= 20),
                    ("Dry surface alone (SMAP satellite)", j.smap_surface <= 20)]:
    d = j[mask]
    summ["rows"].append(dict(rule=label, fired=int(len(d)), precision=float(d.loss80.mean()) if len(d) else None))
(DERIVED / "validation_soil_summary.json").write_text(json.dumps(summ, indent=1), encoding="utf-8")
