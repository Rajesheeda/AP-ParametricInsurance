"""Per-mandal exposure of the PPT focus crops (e-Panta, latest complete season) for pilot selection.
YSR also gets parcel coverage: share of booked acres joined to a cadastral polygon."""
import geopandas as gpd
import pandas as pd

from common import DERIVED, ac

FOCUS = {  # PPT slide 7: paddy (flood), cotton + groundnut (drought), chilli (unseasonal rain)
    ("22", "Kharif"): ["Red Chillies", "Cotton", "Paddy"],
    ("11", "Kharif"): ["Paddy", "Cotton", "Groundnut", "Red gram"],
    ("14", "Kharif"): ["Paddy", "Cotton"],
    ("10", "Rabi"): ["Paddy", "Groundnut"],
}
m = gpd.read_file(DERIVED / "poc_mandals.geojson")[["district_code", "mandal_te", "adm3_name", "adm3_id", "ok"]]
rows = []
for (code, season), crops in FOCUS.items():
    d = pd.read_parquet(ac.extract_path("parametric", f"epanta_crop_parcel_{code}.parquet"),
                        columns=["mandal", "season", "year", "crop_name", "area"])
    d = d[(d.season == season) & (d.year == 2025) & d.crop_name.notna()]
    tot = d.groupby("mandal").area.sum().rename("booked_ac")
    foc = d[d.crop_name.isin(crops)].pivot_table(index="mandal", columns="crop_name", values="area", aggfunc="sum").fillna(0)
    t = pd.concat([tot, foc], axis=1).fillna(0)
    t["focus_ac"] = t[crops].sum(axis=1) if set(crops) <= set(t.columns) else t[[c for c in crops if c in t]].sum(axis=1)
    t["district_code"], t["season"] = code, season
    rows.append(t.reset_index(names="mandal_te"))
ex = pd.concat(rows, ignore_index=True).merge(m, on=["district_code", "mandal_te"], how="left")

j = pd.read_parquet(DERIVED / "ysr_epanta_parcel_join.parquet", columns=["mandal_en", "village", "season", "year", "join_level", "area"])
j = j[(j.season == "Kharif") & (j.year == 2025)]
cov = j.assign(hit=j.join_level.isin(["exact", "base"]) * j.area).groupby("mandal_en")[["hit", "area"]].sum()
cov["parcel_cov"] = (cov.hit / cov.area).round(2)
ysr_te = pd.read_parquet(ac.extract_path("parametric", "epanta_crop_parcel_11.parquet"), columns=["mandal", "mandal_en"]).drop_duplicates("mandal")
ex = ex.merge(ysr_te.merge(cov.parcel_cov, left_on="mandal_en", right_index=True)[["mandal", "parcel_cov"]]
              .rename(columns={"mandal": "mandal_te"}), on="mandal_te", how="left")
ex.to_csv(DERIVED / "mandal_exposure_2025.csv", index=False, encoding="utf-8-sig")
for code, g in ex.groupby("district_code"):
    cols = ["adm3_name", "booked_ac", "focus_ac"] + [c for c in g.columns if c in sum(FOCUS.values(), [])] + (["parcel_cov"] if code == "11" else [])
    print(f"\n== {code} top 8 by focus-crop acres"); print(g.sort_values("focus_ac", ascending=False)[cols].head(8).round(0 if code != "11" else 2).to_string(index=False))
