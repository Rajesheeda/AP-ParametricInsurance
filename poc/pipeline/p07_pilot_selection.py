"""Pilot mandal selection (PPT: 5-7 mandals prone to flood, drought or cyclone).

Rule, per district:
  1. Eligible = at least one qualifying event of the district's primary peril in 2020-2025:
       extreme / unseasonal rain with peak day >= IMD 'heavy' (64.5 mm), cyclone >= 34 kt within 150 km,
       or drought with JJAS departure <= -20% (IMD 'deficient').
  2. YSR additionally needs parcel coverage >= 0.5 (to demonstrate parcel-level assessment).
  3. Rank eligible mandals by focus-crop acres (e-Panta Kharif/Rabi 2025); take N per district.
"""
import pandas as pd

from common import DERIVED

PLAN = {  # district: (season, perils, N)
    "14": ("Kharif", {"extreme_rain", "cyclone"}, 2),            # paddy flood / cyclone
    "22": ("Kharif", {"extreme_rain", "unseasonal_rain", "cyclone"}, 2),  # chilli, cotton
    "11": ("Kharif", {"drought", "extreme_rain", "cyclone"}, 2),  # drought + paddy
    "10": ("Rabi", {"unseasonal_rain", "cyclone"}, 1),            # Rabi paddy, Nov-Feb storms
}
ev = pd.read_csv(DERIVED / "event_catalogue_era5.csv", dtype={"district_code": str})
ev = ev[pd.to_datetime(ev.start).dt.year.between(2020, 2025)]
ev["qual"] = ((ev.type.isin(["extreme_rain", "unseasonal_rain"]) & (ev.peak_day_mm >= 64.5))
              | (ev.type == "cyclone") | ((ev.type == "drought") & (ev.value <= -20)))
ex = pd.read_csv(DERIVED / "mandal_exposure_2025.csv", dtype={"district_code": str})
picks = []
for d, (season, perils, n) in PLAN.items():
    q = ev[(ev.district_code == d) & ev.qual & ev.type.isin(perils)]
    cnt = q.groupby("adm3_id").type.agg(lambda s: s.value_counts().to_dict()).rename("events")
    nq = q.groupby("adm3_id").size().rename("n_events")
    e = ex[(ex.district_code == d) & ex.ok].merge(nq, left_on="adm3_id", right_index=True).merge(cnt, left_on="adm3_id", right_index=True)
    if d == "11":
        e = e[e.parcel_cov >= 0.5]
    e = e.sort_values("focus_ac", ascending=False)
    print(f"\n== {d} eligible {len(e)}; top 5:")
    print(e[["adm3_name", "focus_ac", "n_events", "events"] + (["parcel_cov"] if d == "11" else [])].head(5).to_string(index=False))
    picks.append(e.head(n).assign(season=season))
p = pd.concat(picks)
p[["district_code", "season", "adm3_name", "adm3_id", "mandal_te", "focus_ac", "n_events", "events", "parcel_cov"]].to_csv(
    DERIVED / "pilot_mandals.csv", index=False, encoding="utf-8-sig")
print("\nPILOT:", p[["district_code", "adm3_name"]].values.tolist())
