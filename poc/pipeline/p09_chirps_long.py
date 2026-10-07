"""CHIRPS mandal-year wide tables (GEE output) -> long daily series in the ERA5 schema."""
import glob

import pandas as pd

from common import DERIVED, POC

frames = []
for f in sorted(glob.glob(str(POC / "data" / "gee_out" / "out_chirps_*.parquet"))):
    w = pd.read_parquet(f)
    days = [c for c in w.columns if c[1:].isdigit()]
    long = w.melt(id_vars=["mid", "dist"], value_vars=days, var_name="d", value_name="rain_mm")
    long["date"] = pd.to_datetime(long.d.str[1:], format="%Y%m%d")
    frames.append(long.rename(columns={"mid": "adm3_id", "dist": "district_code"}).drop(columns="d"))
r = pd.concat(frames, ignore_index=True).dropna(subset=["rain_mm"])
r.to_parquet(DERIVED / "rain_chirps_daily.parquet", index=False)
print(len(r), "rows;", r.date.min().date(), "to", r.date.max().date())
print("mean annual mm per mandal 1995-2024 by district:",
      r[r.date.dt.year.between(1995, 2024)].groupby(["district_code", "adm3_id", r.date.dt.year]).rain_mm.sum()
      .groupby("district_code").mean().round(0).to_dict())
