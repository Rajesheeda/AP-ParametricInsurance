"""Compensation workflow for both lanes: what is owed, to whom, on what evidence, and where each case stands.

Lane 1 (parametric insurance): one settlement batch per mandal x season from p23 per-booking payouts. Each line is a
  booking (survey number x crop; e-Panta carries no farmer names and none are added here) with its index evidence.
  Amount = payout % x sum insured per acre x acres. Sum insured is the notified scale of finance (DLTC / SLCCCI), an
  input the Department supplies in poc/config/sum_insured.csv; until then the batch is in % of sum insured and
  "sum-insured acres" (acres x payout %), never in invented rupees. Each batch file carries its SHA-256 so the file
  the Crop Insurance Section approves is the file the insurer receives.
Lane 2 (SDRF relief, live event p25): one case per mandal opened for enumeration. Relief budget range =
  standing acres (e-Panta 2026) x share of acute-trigger CCE mandal-years with loss >= 33% (p18, Wilson CI)
  x MHA input subsidy rate (rainfed Rs 8,500/ha to assured-irrigated Rs 17,000/ha; irrigation is unknown in
  Manyam and Palnadu, so both ends are shown). Payment needs the AEO's >= 33% enumeration; the estimate only sizes it.
  Not applied (no farmer ID in e-Panta extracts): the 2 ha per-farmer ceiling and the Rs 1,000 / 2,000 minimum.
  MHA note: input subsidy is reduced by any PMFBY claim for the same calamity, so relief = SDRF - Lane 1 payout.
Source of norms: MHA F.No.33-03/2020-NDM-I, 10 Oct 2022, Items and norms of assistance from SDRF/NDRF 2022-23 to
  2025-26, item 5(i)(B)(a) and 5(ii).
Case states are kept by the backend (routers/poc_compensation.py) in an append-only, hash-chained log.
Output: compensation.json, settlement/<mandal>_<year>.csv (gitignored data/derived).
"""
import hashlib
import json
import re

import pandas as pd

from common import DERIVED, POC

HA_PER_ACRE = 0.404686
NORMS = dict(source="MHA F.No.33-03/2020-NDM-I, 10 Oct 2022 (SDRF/NDRF norms 2022-23 to 2025-26), item 5",
             rainfed_per_ha=8500, irrigated_per_ha=17000, perennial_per_ha=22500, threshold_pct=33, ceiling_ha=2,
             min_rainfed=1000, min_irrigated=2000,
             pmfby_note="Input subsidy is adjusted to the extent of the PMFBY claim received for the same calamity.")
LANE1_STATES = ["CALCULATED", "APPROVED", "SENT TO INSURER", "PAID"]
LANE2_STATES = ["OPENED", "EVIDENCE RECEIVED", "AEO VERIFIED >=33%", "SANCTIONED", "PAID", "CLOSED: BELOW 33%"]
OUT = DERIVED / "settlement"
OUT.mkdir(exist_ok=True)

# ---- sum insured (Department input; blank until notified values are supplied)
si_path = POC / "config" / "sum_insured.csv"
si = pd.read_csv(si_path) if si_path.exists() else pd.DataFrame(columns=["district", "crop", "year", "si_per_ha", "reference"])
si = si.dropna(subset=["si_per_ha"])

# ---- Lane 1 settlement batches
f = pd.read_parquet(DERIVED / "farmer_payouts.parquet")
f = f[f.total_pct > 0].copy()
f["survey"] = f.survey.astype(str)
f["sowing_date"] = f.sowing_date.astype(str).str[:10]
f["si_acres"] = f.area * f.total_pct / 100
batches = []
for (m, y), d in f.groupby(["mandal", "year"]):
    d = d.sort_values(["village_en", "survey", "crop_name"])
    d.insert(0, "line_ref", [hashlib.sha1(f"{m}|{y}|{v}|{s}|{c}|{i}".encode()).hexdigest()[:12]
                             for i, (v, s, c) in enumerate(zip(d.village_en, d.survey, d.crop_name))])
    cols = ["line_ref", "mandal", "village_en", "survey", "crop_name", "sowing_date", "area", "coverA_paid", "coverA_driver",
            "vci", "coverB_pct", "coverB_event", "total_pct", "si_acres"]
    s = si[(si.year == y)] if len(si) else si
    rate = d.crop_name.map(s.set_index("crop").si_per_ha) if len(s) else None
    out = d[cols].copy()
    out["amount_rs"] = (rate * HA_PER_ACRE * d.area * d.total_pct / 100).round(0) if rate is not None else None
    path = OUT / f"{m}_{y}.csv"
    out = out.round({"area": 3, "coverA_paid": 2, "vci": 1, "coverB_pct": 2, "total_pct": 2, "si_acres": 3})
    out.to_csv(path, index=False)
    batches.append(dict(batch_id=f"L1-{m[:4].upper()}-{y}", mandal=m, year=int(y), lines=int(len(out)),
                        acres=round(float(out.area.sum()), 1), si_acres=round(float(out.si_acres.sum()), 1),
                        mean_pct=round(float((out.total_pct * out.area).sum() / out.area.sum()), 1),
                        amount_rs=None if out.amount_rs.isna().all() else float(out.amount_rs.sum()),
                        drivers=out.coverA_driver.dropna().value_counts().to_dict(),
                        file=path.name, sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    print(f"Lane 1 batch {m} {y}: {len(out):,} lines, {out.area.sum():,.0f} acres, {out.si_acres.sum():,.0f} sum-insured acres")

# ---- Lane 2 relief cases (live event)
cals = json.loads((DERIVED / "loss_calibration.json").read_text(encoding="utf-8"))
cal = cals["acute"]
live = json.loads((DERIVED / "live_event_arnab.json").read_text(encoding="utf-8"))
lv = pd.read_csv(DERIVED / "live_event_mandals.csv", dtype={"district_code": str})
lv = lv[lv.lane2_action.str.startswith("ENUMERATION", na=False) | lv.lane2_action.str.startswith("PRIORITY", na=False)]
sh, (lo, hi) = cal["share_loss_33"], cal["share_loss_33_ci"]
cases = []
for r in lv.itertuples():
    ha = r.standing_acres * HA_PER_ACRE
    paid1 = float(r.lane1_payout_pct) if str(r.lane1_decision).startswith("INDEX PAYOUT") else 0.0
    cases.append(dict(case_id=f"{live['event']['id']}-{re.sub('[^A-Z]', '', r.adm3_name.upper())[:20]}", event_id=live["event"]["id"], district=r.district,
                      mandal=r.adm3_name, adm3_id=r.adm3_id, standing_acres=round(float(r.standing_acres), 0),
                      lane2_action=r.lane2_action, rain_mm=None if pd.isna(r.index_mm) else round(float(r.index_mm), 0),
                      eligible_ha=[round(ha * lo), round(ha * sh), round(ha * hi)],
                      budget_rs=[round(ha * lo * NORMS["rainfed_per_ha"]), round(ha * sh * NORMS["rainfed_per_ha"]),
                                 round(ha * sh * NORMS["irrigated_per_ha"]), round(ha * hi * NORMS["irrigated_per_ha"])],
                      lane1_payout_pct=paid1))
tot = dict(cases=len(cases), standing_acres=round(sum(c["standing_acres"] for c in cases)),
           budget_rs=[sum(c["budget_rs"][i] for c in cases) for i in range(4)])
print(f"Lane 2 {live['event']['name']}: {len(cases)} cases, {tot['standing_acres']:,} standing acres, budget "
      f"Rs {tot['budget_rs'][1] / 1e7:.1f} cr (rainfed) to {tot['budget_rs'][2] / 1e7:.1f} cr (irrigated) at the {sh:.0%} share; "
      f"CI range Rs {tot['budget_rs'][0] / 1e7:.1f}-{tot['budget_rs'][3] / 1e7:.1f} cr")

res = dict(norms=NORMS, lane1_states=LANE1_STATES, lane2_states=LANE2_STATES,
           sum_insured=dict(supplied=bool(len(si)), file="poc/config/sum_insured.csv",
                            note="Scale of finance notified by DLTC / SLCCCI per district x crop x season; Department input."),
           calibration=dict(share_33=sh, ci=[lo, hi], share_33_none=cals["none"]["share_loss_33"], n=cal["n"], years=cal["years"], source="YSR Kadapa CCE, acute-trigger mandal-years"),
           lane1_batches=batches, lane2=dict(event=live["event"], cases=cases, totals=tot))
(DERIVED / "compensation.json").write_text(json.dumps(res, indent=1, default=float), encoding="utf-8")
