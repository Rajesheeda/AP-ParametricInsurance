"""Event catalogue 2020-2026 per POC mandal, using published definitions only.

Extreme rain  : 3-day total > mandal's own 99th percentile of 3-day totals, 1995-2024 (ETCCDI-style);
                peak day labelled with IMD classes (heavy >=64.5, very heavy >=115.6, extremely heavy >=204.4 mm).
Unseasonal    : same test, events falling Nov-Feb (chilli harvest / Rabi).
Drought       : Jun-Sep total vs 1995-2024 mean -> IMD categories (deficient <= -20%, large deficient <= -60%);
                SPI (gamma fit, McKee 1993); longest dry spell (days < 2.5 mm, IMD rainy-day threshold) Jul-Sep.
Cyclone       : IBTrACS NI track points within 150 km of mandal centroid with wind >= 34 kt (IMD cyclonic storm).
Input rainfall: ERA5-Land point series now (screening); swap to CHIRPS areal means (GEE-1) when available.
"""
import sys

import numpy as np
import pandas as pd
from scipy import stats

from common import DERIVED, OPEN

RAIN = sys.argv[1] if len(sys.argv) > 1 else "rain_era5_daily.parquet"
BASE = (1995, 2024)
YEARS = range(2020, 2027)

r = pd.read_parquet(DERIVED / RAIN)
cent = pd.read_csv(DERIVED / "poc_mandal_centroids.csv")
names = cent.set_index("adm3_id")[["district_code", "adm3_name"]]
r = r.sort_values(["adm3_id", "date"])
r["r3"] = r.groupby("adm3_id").rain_mm.transform(lambda s: s.rolling(3, min_periods=3).sum())
r["yr"] = r.date.dt.year

def imd_class(x):
    return ("extremely heavy" if x >= 204.4 else "very heavy" if x >= 115.6
            else "heavy" if x >= 64.5 else "below heavy")

events = []
# --- extreme / unseasonal rain
for mid, g in r.groupby("adm3_id"):
    base = g[g.yr.between(*BASE)]
    p99 = base.r3.quantile(0.99)
    hits = g[(g.yr.isin(YEARS)) & (g.r3 > p99)]
    if hits.empty:
        continue
    grp = (hits.date.diff().dt.days > 3).cumsum()
    for _, h in hits.groupby(grp):
        end = h.date.max(); start = end - pd.Timedelta(days=2) if len(h) == 1 else h.date.min() - pd.Timedelta(days=2)
        win = g[(g.date >= start) & (g.date <= end)]
        peak = win.rain_mm.max()
        kind = "unseasonal_rain" if end.month in (11, 12, 1, 2) else "extreme_rain"
        events.append(dict(adm3_id=mid, type=kind, start=start.date(), end=end.date(),
                           value=round(h.r3.max(), 1), threshold=round(p99, 1),
                           unit="mm/3day", severity=imd_class(peak), peak_day_mm=round(peak, 1)))

# --- drought (Kharif Jun-Sep)
r["m"] = r.date.dt.month
jjas = r[r.m.between(6, 9)].groupby(["adm3_id", "yr"]).rain_mm.sum().rename("jjas").reset_index()
for mid, g in jjas.groupby("adm3_id"):
    base = g[g.yr.between(*BASE)].jjas
    mean = base.mean()
    a, loc, scale = stats.gamma.fit(base, floc=0)
    for _, row in g[g.yr.isin(YEARS)].iterrows():
        if row.yr == 2026:
            continue  # season incomplete in the series cut
        dep = (row.jjas - mean) / mean * 100
        spi = stats.norm.ppf(stats.gamma.cdf(row.jjas, a, loc=loc, scale=scale))
        d = r[(r.adm3_id == mid) & (r.yr == row.yr) & r.m.between(7, 9)].rain_mm.lt(2.5)
        spell = int(d.groupby((~d).cumsum()).sum().max())
        cat = ("large deficient" if dep <= -60 else "deficient" if dep <= -20 else
               "normal" if dep < 20 else "excess" if dep < 60 else "large excess")
        if cat in ("deficient", "large deficient") or spi <= -1.0:
            events.append(dict(adm3_id=mid, type="drought", start=f"{row.yr}-06-01", end=f"{row.yr}-09-30",
                               value=round(dep, 1), threshold=-20.0, unit="% departure JJAS",
                               severity=f"{cat}; SPI {spi:.2f}; dry spell {spell}d", peak_day_mm=np.nan))

# --- cyclones
ib = pd.read_csv(OPEN / "ibtracs_NI.csv", skiprows=[1], low_memory=False,
                 usecols=["SID", "NAME", "ISO_TIME", "LAT", "LON", "WMO_WIND", "USA_WIND"])
ib["t"] = pd.to_datetime(ib.ISO_TIME)
ib = ib[ib.t.dt.year.isin(YEARS)].copy()
ib["wind"] = pd.to_numeric(ib.WMO_WIND, errors="coerce").fillna(pd.to_numeric(ib.USA_WIND, errors="coerce"))
ib["LAT"] = pd.to_numeric(ib.LAT); ib["LON"] = pd.to_numeric(ib.LON)
for _, c in cent.iterrows():
    la, lo = np.radians(c.lat), np.radians(c.lon)
    d = 6371 * np.arccos(np.clip(np.sin(la) * np.sin(np.radians(ib.LAT)) +
                                 np.cos(la) * np.cos(np.radians(ib.LAT)) * np.cos(np.radians(ib.LON) - lo), -1, 1))
    near = ib[(d <= 150) & (ib.wind >= 34)].assign(dist=d[(d <= 150) & (ib.wind >= 34)])
    for sid, s in near.groupby("SID"):
        events.append(dict(adm3_id=c.adm3_id, type="cyclone", start=s.t.min().date(), end=s.t.max().date(),
                           value=float(s.wind.max()), threshold=34.0, unit="kt max wind within 150 km",
                           severity=f"{s.NAME.iloc[0]}; closest {s.dist.min():.0f} km", peak_day_mm=np.nan))

ev = pd.DataFrame(events).join(names, on="adm3_id")
ev = ev[["district_code", "adm3_name", "adm3_id", "type", "start", "end", "value", "threshold", "unit", "severity", "peak_day_mm"]]
ev = ev.sort_values(["district_code", "adm3_name", "start"])
tag = RAIN.split("_")[1]
ev.to_csv(DERIVED / f"event_catalogue_{tag}.csv", index=False, encoding="utf-8-sig")
print("events by district x type:\n", pd.crosstab(ev.district_code, ev.type).to_string())
print("\nevents by year x type:\n", pd.crosstab(pd.to_datetime(ev.start).dt.year, ev.type).to_string())
print("\ncyclones:", ev[ev.type == "cyclone"].drop_duplicates("severity")[["district_code", "start", "severity", "value"]].to_string())
