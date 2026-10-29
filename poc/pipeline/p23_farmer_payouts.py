"""Lane 1 per-farmer payouts, Kharif 2023-2025: YSR pilot mandals (Chapad, Khajipet; e-Panta joined to cadastral)
and Palnadu pilot mandals (Gurazala, Sattenapalle; e-Panta survey numbers, no cadastral).

Every e-Panta booking (survey number x crop) gets its own cover, built from ITS OWN sowing date:
  Cover A (season, WBCIS structure, p10): FAO-56 phases start at the booking's sowing week, not at a mandal-wide
          calendar. Bookings are grouped into cohorts of the same mandal x crop x sowing week; each cohort's trigger
          (1-in-5) and exit (1-in-25) levels come from 1995-2024 CHIRPS over that cohort's own phase windows, so
          every farmer has the same 1-in-5 payout frequency whether they sowed early or late.
  Cover B (catastrophe, p22): for each acute rain window, ERA5 payout (from its own 1-in-5 to 1-in-25 level; the
          index that passed the qualification gate on CCE) AND Sentinel-1 flood above the mandal's false-alarm floor,
          paid only if the booking's crop was standing (sowing <= window start <= sowing + FAO-56 duration).
  Cover A is a dual trigger too: its rainfall payout is paid only if MODIS VCI < 35 in that mandal-season.
  Total payout % = min(100, A paid + B) of the sum insured. Sum insured per acre is the notified scale of finance
  (input, not computed here).
Sowing outside 0-150 days from May 1 is outside the Kharif window: reported, not covered.
Compared with the mandal-calendar (median sowing date) payout that a WBCIS term sheet would use.
Output: farmer_payouts.parquet, farmer_payouts_summary.json (gitignored data/derived).
"""
import glob
import re
import json

import numpy as np
import pandas as pd

import p10_triggers as T
from common import DERIVED, POC, ac

DUR = {"Paddy": 150, "Cotton": 195, "Groundnut": 130, "Red Chillies": 120}
PILOT = {"CHAPAD": "Chapad", "KHAJIPET": "Khajipet"}
CROPS = {"11": ["Paddy", "Cotton", "Groundnut"], "22": ["Cotton", "Red Chillies", "Paddy"]}
YEARS = [2023, 2024, 2025]

pil = pd.read_csv(DERIVED / "pilot_mandals.csv", dtype={"district_code": str})
mid = pil.set_index("adm3_name").adm3_id.to_dict()
b = pd.read_parquet(DERIVED / "ysr_epanta_parcel_join.parquet")
b = b[b.mandal_en.isin(PILOT) & b.year.isin(YEARS) & b.crop_name.isin(CROPS["11"])].copy()
b["mandal"] = b.mandal_en.map(PILOT)
b["district_code"] = "11"
pal = pil[pil.district_code == "22"].set_index("mandal_te").adm3_name.to_dict()
e22 = pd.read_parquet(ac.extract_path("parametric", "epanta_crop_parcel_22.parquet"),
                      columns=["mandal", "village", "village_en", "season", "year", "survey", "crop_name", "variety", "sowing_date", "area"])
e22 = e22[e22.mandal.isin(pal) & (e22.season == "Kharif") & e22.year.isin(YEARS) & e22.crop_name.isin(CROPS["22"])].copy()
# Telugu-only village names: romanised (Harvard-Kyoto, as p02 does for mandal names) for display; Telugu kept alongside
from indic_transliteration import sanscript  # noqa: E402


def roman(te):
    import unicodedata
    x = re.sub(r"M\b", "m", sanscript.transliterate(str(te), sanscript.TELUGU, sanscript.HK))   # final anusvara reads "m"
    for a, b in [("M", "n"), ("~", "n"), ("H", ""), ("c", "ch"), ("z", "s"), ("S", "s"), ("A", "a"), ("I", "i"), ("U", "u"),
                 ("R", "r"), ("T", "t"), ("D", "d"), ("N", "n"), ("E", "e"), ("O", "o")]:
        x = x.replace(a, b)
    x = unicodedata.normalize("NFKD", x).encode("ascii", "ignore").decode()
    return " ".join(w.capitalize() for w in x.split())


e22["village_en"] = e22.village_en.fillna(e22.village.map(lambda v: f"{roman(v)} ({v})"))
e22["mandal"] = e22.mandal.map(pal)
e22["district_code"], e22["join_level"], e22["sv"], e22["objectid"] = "22", "no cadastral", None, None
b = pd.concat([b, e22[[c for c in b.columns if c in e22.columns]]], ignore_index=True)
b["adm3_id"] = b.mandal.map(mid)
b["sow"] = pd.to_datetime(b.sowing_date, errors="coerce")
b = b.dropna(subset=["sow"])
b["off"] = (b.sow - pd.to_datetime(b.year.astype(str) + "-05-01")).dt.days
b["covered"] = b.off.between(0, 150)
b["week"] = (b.off.clip(0, 150) // 7) * 7 + 3
print("bookings:", len(b), "| outside sowing window:", int((~b.covered).sum()))

# ---- Cover A: cohort-specific season cover
rain = pd.read_parquet(DERIVED / "rain_chirps_daily.parquet")
coh = b[b.covered].groupby(["district_code", "adm3_id", "crop_name", "week"]).size().reset_index(name="n")
ix = []
for r in coh.itertuples():
    sow = pd.DataFrame([dict(district_code=r.district_code, adm3_id=r.adm3_id, season="Kharif", crop_name=r.crop_name, off=r.week)])
    x = T.indices(rain, sow)
    x["adm3_id"] = f"{r.adm3_id}|{r.week}"
    ix.append(x)
_, seas = T.payouts(pd.concat(ix))
seas[["adm3_id", "week"]] = seas.adm3_id.str.split("|", expand=True)
seas["week"] = seas.week.astype(int)
seas = seas.rename(columns={"crop": "crop_name", "pay_pct": "coverA_pct", "S": "coverA_S", "driver_peril": "coverA_driver"})
b = b.merge(seas[["adm3_id", "crop_name", "week", "year", "coverA_pct", "coverA_S", "coverA_driver"]],
            on=["adm3_id", "crop_name", "week", "year"], how="left")
mc = pd.read_parquet(DERIVED / "trigger_annual_payouts.parquet")[["adm3_id", "crop", "year", "pay_pct"]]
b = b.merge(mc.rename(columns={"crop": "crop_name", "pay_pct": "calendar_pct"}), on=["adm3_id", "crop_name", "year"], how="left")

# ---- Cover B: event consensus x Sentinel-1, standing crop only
lv = pd.read_parquet(DERIVED / "cat_cover_levels.parquet")[["adm3_id", "src", "L5", "L25"]].drop_duplicates(["adm3_id", "src"])
win = pd.read_csv(DERIVED / "sar_cce_windows.csv", parse_dates=["start", "end"])
win = win[win.start.dt.year.isin(YEARS) | ((win.start.dt.month == 1) & win.start.dt.year.isin([y + 1 for y in YEARS]))]
fl = pd.concat([pd.read_parquet(f) for f in glob.glob(str(POC / "data" / "gee_out" / "out_flood_mandal_*.parquet"))])
ctrl = fl[fl.event_id.str.startswith("CTRL_")]
noise = (ctrl.crop_flood_ha / ctrl.cropland_ha).groupby(ctrl.mid).max()
sar = pd.concat([pd.read_parquet(f) for f in glob.glob(str(POC / "data" / "gee_out" / "out_sarcce_*.parquet"))])
sar["excess"] = sar.crop_flood_ha / sar.cropland_ha - sar.mid.map(noise)
series = {k: pd.read_parquet(DERIVED / f"rain_{k}_daily.parquet") for k in ["chirps", "era5", "imerg"]}
ev = []
for w in win.itertuples():
    for m, a in mid.items():
        if m not in PILOT.values():
            continue
        pays = {}
        for k, s in series.items():
            x = s[(s.adm3_id == a) & s.date.between(w.start - pd.Timedelta(days=2), w.end + pd.Timedelta(days=2))].sort_values("date")
            if len(x) < 3:
                continue
            l = lv[(lv.adm3_id == a) & (lv.src == k)].iloc[0]
            v = x.rain_mm.rolling(3).sum().max()
            pays[k] = dict(mm=round(float(v), 1), pay=float(100 * np.clip((v - l.L5) / (l.L25 - l.L5), 0, 1)))
        cons = float(np.median([p["pay"] for p in pays.values()])) if pays else 0.0
        s = sar[(sar.event_id == w.id) & (sar.mid == a)]
        sx = float(s.excess.iloc[0]) if len(s) else np.nan
        ev.append(dict(event=w.id, start=w.start, end=w.end, adm3_id=a, mandal=m, consensus_pct=cons,
                       sar_excess_pct=None if np.isnan(sx) else 100 * sx, sar_hours=float(s.hours_after_event_end.iloc[0]) if len(s) else None,
                       sar_confirms=bool(len(s) and sx > 0),
                       coverB_pct=pays["era5"]["pay"] if ("era5" in pays and len(s) and sx > 0) else 0.0,
                       **{f"{k}_mm": p["mm"] for k, p in pays.items()}, **{f"{k}_pay": p["pay"] for k, p in pays.items()}))
ev = pd.DataFrame(ev)
ev.to_csv(DERIVED / "cat_cover_events.csv", index=False)
print(ev[["event", "mandal", "chirps_mm", "era5_mm", "imerg_mm", "consensus_pct", "sar_excess_pct", "sar_hours", "coverB_pct"]].round(1).to_string(index=False))

b["coverB_pct"], b["coverB_event"] = 0.0, None
for e in ev[ev.coverB_pct > 0].itertuples():
    sy = e.start.year - 1 if e.start.month == 1 else e.start.year
    standing = (b.adm3_id == e.adm3_id) & (b.year == sy) & b.covered & (b.sow <= e.start) & \
               (b.sow + pd.to_timedelta(b.crop_name.map(DUR), unit="D") >= e.start)
    upd = standing & (b.coverB_pct < e.coverB_pct)
    b.loc[upd, "coverB_pct"], b.loc[upd, "coverB_event"] = e.coverB_pct, e.event
# Palnadu: Cover B from the pilot assessment's Lane 1 decisions (same contract, p13), standing crop only
asm = pd.read_csv(DERIVED / "assessment_pilot.csv", dtype={"district_code": str})
asm = asm[(asm.kind == "acute") & (asm.district_code == "22") & (asm.lane1_payout_pct > 0)]
for e in asm.itertuples():
    st = pd.Timestamp(e.start)
    sy = st.year - 1 if st.month == 1 else st.year
    standing = (b.mandal == e.mandal) & (b.crop_name == e.crop) & (b.year == sy) & b.covered & (b.sow <= st) &                (b.sow + pd.to_timedelta(b.crop_name.map(DUR), unit="D") >= st)
    upd = standing & (b.coverB_pct < e.lane1_payout_pct)
    b.loc[upd, "coverB_pct"], b.loc[upd, "coverB_event"] = e.lane1_payout_pct, e.event_id
b.loc[~b.covered, ["coverA_pct", "coverB_pct"]] = 0.0
vci = pd.read_csv(DERIVED / "validation_trigger_vs_vci.csv")[["adm3_id", "year", "vci"]].drop_duplicates(["adm3_id", "year"])
b = b.merge(vci, on=["adm3_id", "year"], how="left")
b["coverA_paid"] = b.coverA_pct.fillna(0).where(b.vci < 35, 0.0)
b["total_pct"] = (b.coverA_paid + b.coverB_pct).clip(upper=100)
b["calendar_pct"] = b.calendar_pct.where(b.covered, 0.0)
cols = ["mandal", "village_en", "survey", "sv", "join_level", "objectid", "year", "crop_name", "variety", "sowing_date", "area",
        "covered", "week", "coverA_pct", "coverA_driver", "calendar_pct", "vci", "coverA_paid", "coverB_pct", "coverB_event", "total_pct"]
b[cols].to_parquet(DERIVED / "farmer_payouts.parquet", index=False)

# summary: what farmer-specific timing changes vs a mandal-wide calendar
s = {"bookings": int(len(b)), "acres": float(b.area.sum()), "outside_window": int((~b.covered).sum()), "by": []}
for (m, y, c), g in b.groupby(["mandal", "year", "crop_name"]):
    own, cal = g.coverA_pct.fillna(0) > 0, g.calendar_pct.fillna(0) > 0
    s["by"].append(dict(mandal=m, year=int(y), crop=c, bookings=int(len(g)), acres=float(g.area.sum()),
                        paid_own=int(own.sum()), paid_calendar=int(cal.sum()),
                        own_only=int((own & ~cal).sum()), calendar_only=int((cal & ~own).sum()),
                        coverB=int((g.coverB_pct > 0).sum()), vci=None if g.vci.isna().all() else float(g.vci.iloc[0]),
                        paid_product=int((g.total_pct > 0).sum()),
                        mean_total_pct=float(g.total_pct.mean()), acre_weighted_pct=float((g.total_pct * g.area).sum() / g.area.sum()),
                        sowing_spread_days=float(g.off.quantile(0.9) - g.off.quantile(0.1))))
(DERIVED / "farmer_payouts_summary.json").write_text(json.dumps(s, indent=1), encoding="utf-8")
print(pd.DataFrame(s["by"]).round(1).to_string(index=False))
