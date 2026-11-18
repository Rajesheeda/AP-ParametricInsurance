"""WBCIS / RWBCIS-structure weather index term sheet and claim calculator for the pilot mandals.

This is a pure weather product: the claim is generated from the weather index alone, irrespective of
yield loss. No CCE, no satellite and no photo enters the claim. (CCE is used only outside the claim, to
report basis risk.)

Structure (per mandal x crop):
  Phases : FAO-56 crop stages (Allen et al. 1998, Table 11), calendar dates anchored on the median
           e-Panta sowing date of that crop in that mandal (2023-25) - as in p10.
  Covers : per phase, the six perils the Crop Insurance Section named:
             deficit rainfall   cumulative phase rain, mm                     (low is bad)       CHIRPS
             excess rainfall    maximum 3-day rain in the phase, mm           (high is bad)      CHIRPS
             dry spell          longest run of days < 2.5 mm (IMD rainy day)  (high is bad)      CHIRPS
             high wind          maximum daily wind gust in the phase, km/h    (high is bad)      ERA5
             disease-congenial  longest run of days with RH mean >= RH_DIS and
                                T mean in [T_DIS_LO, T_DIS_HI]                 (high is bad)      ERA5
             heat               days with T max >= T_HEAT                      (high is bad)      ERA5
  Trigger / exit (the "start and exit points"): each mandal's own 1995-2024 history of that cover in that
           phase - trigger = 1-in-5-year level, exit = 1-in-25-year level (empirical quantiles 0.80/0.96 or
           0.20/0.04). Payout rises linearly from trigger to exit, giving a fixed Rs per mm / per day / per km/h.
  Sum insured: AP SLTC Scale of Finance 2024-25 (poc/config/sum_insured.csv). Allocation of the sum insured:
           equal across the six perils, and within a peril across phases by crop water demand
           (FAO-56 days x Kc). This allocation is the Department's / insurer's choice and is a parameter.
  Claim  : sum over covers and phases, capped at the sum insured. Rs per acre.

Day thresholds for the disease and heat covers are parameters for the Department / ANGRAU agromet cell to
set; the defaults are stated below and are NOT measured. Trigger and exit levels are measured.
Data   : rain CHIRPS (areal mandal mean, gauge-blended); for days after CHIRPS ends, ERA5 (provisional).
         Wind / RH / temperature ERA5 at the mandal centroid (p27). Live product: Reference Weather Station
         (DES RTGS AWS or IMD), back-up station when the RWS fails, gridded data as last fallback.
"""
import json
import sys
import time

import numpy as np
import pandas as pd
import requests
from scipy.stats import kendalltau, theilslopes

from common import DERIVED, POC
from p10_triggers import FAO, PHASES, phase_kc, sowing_doy

sys.stdout.reconfigure(encoding="utf-8")
BASE = (1995, 2024)
Q_TRIG, Q_EXIT = 1 - 1 / 5, 1 - 1 / 25
ACRE_PER_HA = 2.4710538
TREND_YEAR = 2026
# Day thresholds (parameters, not measured; Department / ANGRAU to confirm).
RH_DIS, T_DIS_LO, T_DIS_HI = 85.0, 20.0, 30.0
T_HEAT = 35.0     # rice spikelet fertility falls at anthesis above ~35 C (Jagadish et al. 2007, J. Exp. Bot. 58:1627)
COVERS = [  # name, unit, worse_high, source
    ("deficit rainfall", "mm", False, "CHIRPS"),
    ("excess rainfall", "mm in 3 days", True, "CHIRPS"),
    ("dry spell", "days", True, "CHIRPS"),
    ("high wind", "km/h gust", True, "ERA5"),
    ("disease-congenial", "days in a row", True, "ERA5"),
    ("heat", "days", True, "ERA5"),
]
PER_PERIL = 1 / len(COVERS)
# Which crop stages each peril is insured in (the "exposure" of each stage). Design parameter, stated:
#   rainfall deficit / dry spell : establishment to flowering (initial, development, mid) - FAO-56 late stage has low water demand
#   excess rainfall              : every stage (seedling submergence to lodging / harvest damage)
#   high wind                    : once the canopy and panicles / bolls stand (mid, late) - lodging and shedding
#   disease-congenial            : tillering / vegetative to flowering (development, mid)
#   heat                         : flowering (mid) - anthesis heat sterility (Jagadish et al. 2007)
EXPOSURE = {"deficit rainfall": ["initial", "development", "mid"], "dry spell": ["initial", "development", "mid"],
            "excess rainfall": PHASES, "high wind": ["mid", "late"], "disease-congenial": ["development", "mid"],
            "heat": ["mid"]}


def recent_era5_rain(pilot, start="2026-05-01", end=None):
    """ERA5 daily rain for the pilot mandals after CHIRPS ends (provisional), cached."""
    f = DERIVED / "rain_era5_recent_pilot.parquet"
    end = end or (pd.Timestamp.today() - pd.Timedelta(days=6)).strftime("%Y-%m-%d")
    if f.exists():
        r = pd.read_parquet(f)
        if r.date.max() >= pd.Timestamp(end) - pd.Timedelta(days=1):
            return r
    rows = []
    for p in pilot.itertuples():
        for _ in range(6):
            q = requests.get("https://archive-api.open-meteo.com/v1/archive", timeout=120, params=dict(
                latitude=p.lat, longitude=p.lon, start_date=start, end_date=end, daily="precipitation_sum",
                models="era5", timezone="Asia/Kolkata"))
            if q.status_code == 200:
                break
            time.sleep(65)
        q.raise_for_status()
        d = q.json()["daily"]
        rows.append(pd.DataFrame({"adm3_id": p.adm3_id, "date": pd.to_datetime(d["time"]), "rain_mm": d["precipitation_sum"]}))
        time.sleep(3)
    r = pd.concat(rows).dropna()
    r.to_parquet(f, index=False)
    return r


def daily_table(pilot):
    rain = pd.read_parquet(DERIVED / "rain_chirps_daily.parquet")
    rain = rain[rain.adm3_id.isin(pilot.adm3_id)][["adm3_id", "date", "rain_mm"]].assign(rain_src="CHIRPS")
    last = rain.date.max()
    er = recent_era5_rain(pilot)
    er = er[er.date > last].assign(rain_src="ERA5 (provisional)")
    rain = pd.concat([rain, er])
    w = pd.read_parquet(DERIVED / "weather_era5_daily.parquet")
    w["tmean"] = (w.tmax + w.tmin) / 2
    d = rain.merge(w.drop(columns="district_code"), on=["adm3_id", "date"], how="outer").sort_values(["adm3_id", "date"])
    return d, last


def longest_run(mask):
    m = mask.astype(int).values
    best = cur = 0
    for v in m:
        cur = cur + 1 if v else 0
        best = max(best, cur)
    return best


def index_values(d, sow, today):
    out = []
    for r in sow.itertuples():
        lens, _ = FAO[r.crop_name]
        s = d[d.adm3_id == r.adm3_id].set_index("date")
        for yr in range(BASE[0], 2027):
            t0 = pd.Timestamp(yr, 5 if r.season == "Kharif" else 10, 1) + pd.Timedelta(days=r.off)
            for ph, n in zip(PHASES, lens):
                t1 = t0 + pd.Timedelta(days=n - 1)
                x = s.loc[t0:t1]
                status = "complete" if t1 <= today else ("in progress" if t0 <= today else "not started")
                if status == "not started" or x.rain_mm.notna().sum() < 0.9 * min(n, (min(t1, today) - t0).days + 1):
                    t0 = t1 + pd.Timedelta(days=1)
                    continue
                dis = (x.rh_mean >= RH_DIS) & x.tmean.between(T_DIS_LO, T_DIS_HI)
                vals = {"deficit rainfall": x.rain_mm.sum(),
                        "excess rainfall": x.rain_mm.rolling(3).sum().max(),
                        "dry spell": longest_run(x.rain_mm.fillna(0) < 2.5),
                        "high wind": x.gust_kmh.max(),
                        "disease-congenial": longest_run(dis),
                        "heat": int((x.tmax >= T_HEAT).sum())}
                if status == "in progress":   # a running total cannot be judged as a deficit before the phase ends
                    vals["deficit rainfall"] = np.nan
                for c, v in vals.items():
                    out.append(dict(adm3_id=r.adm3_id, district_code=r.district_code, season=r.season, crop=r.crop_name,
                                    year=yr, phase=ph, start=t0.date(), end=t1.date(), status=status, cover=c, value=v,
                                    rain_src=",".join(sorted(x.rain_src.dropna().unique()))))
                t0 = t1 + pd.Timedelta(days=1)
    return pd.DataFrame(out)


def term_sheet(ix, si_acre):
    meta = {c: (u, hi, src) for c, u, hi, src in COVERS}
    w = {}   # (crop, cover, phase) -> share of that peril's sum insured, by crop water demand over its exposed stages
    for crop, (lens, kc) in FAO.items():
        dem = dict(zip(PHASES, np.array(lens) * np.array(phase_kc(kc))))
        for cov, phs in EXPOSURE.items():
            tot = sum(dem[p] for p in phs)
            w.update({(crop, cov, p): (dem[p] / tot if p in phs else 0.0) for p in PHASES})
    rows = []
    for (aid, crop, ph, c), g in ix.groupby(["adm3_id", "crop", "phase", "cover"]):
        bb = g[g.year.between(*BASE) & (g.status == "complete")].dropna(subset=["value"])
        b = bb.value
        u, hi, src = meta[c]
        # Non-stationary climate (e.g. warming): Mann-Kendall test; if significant, Theil-Sen detrend the history
        # to the 2026 level before taking the trigger/exit quantiles (Sen 1968; standard in index burn analysis).
        slope, trend = 0.0, False
        if len(b) >= 25 and b.nunique() > 3:
            tau, pv = kendalltau(bb.year, b)
            if pv < 0.05:
                slope, trend = float(theilslopes(b, bb.year)[0]), True
                b = b + slope * (TREND_YEAR - bb.year)
        trig = b.quantile(Q_TRIG if hi else 1 - Q_TRIG)
        ext = b.quantile(Q_EXIT if hi else 1 - Q_EXIT)
        offered = len(b) >= 25 and abs(ext - trig) > 1e-9 and w[(crop, c, ph)] > 0
        mx = si_acre[crop] * PER_PERIL * w[(crop, c, ph)] if offered else 0.0
        last = g[g.year == g.year.max()].iloc[0]
        cal = g[g.year == 2026]
        rows.append(dict(adm3_id=aid, crop=crop, phase=ph, cover=c, unit=u, worse_high=hi, source=src,
                         start_mmdd=pd.Timestamp(cal.start.iloc[0]).strftime("%d %b") if len(cal) else None,
                         end_mmdd=pd.Timestamp(cal.end.iloc[0]).strftime("%d %b") if len(cal) else None,
                         n_years=len(b), trigger=round(float(trig), 1), exit=round(float(ext), 1), offered=offered,
                         max_rs_acre=round(mx), rate_rs_per_unit=round(mx / abs(ext - trig), 1) if offered else None,
                         phase_weight=round(w[(crop, c, ph)], 3), trend=trend, slope_per_yr=round(slope, 3)))
    return pd.DataFrame(rows)


def claims(ix, ts):
    c = ix.merge(ts[["adm3_id", "crop", "phase", "cover", "trigger", "exit", "worse_high", "offered", "max_rs_acre", "slope_per_yr"]],
                 on=["adm3_id", "crop", "phase", "cover"])
    # past years are scored at today's climate level (as-if 2026); 2026 itself is the raw observation
    c["value_adj"] = c.value + c.slope_per_yr * (TREND_YEAR - c.year)
    num = np.where(c.worse_high, c.value_adj - c.trigger, c.trigger - c.value_adj)
    frac = np.clip(num / (c.exit - c.trigger).abs().replace(0, np.nan), 0, 1)
    c["frac"] = np.where(c.offered, np.nan_to_num(frac), 0.0)
    c["claim_rs_acre"] = c.frac * c.max_rs_acre
    return c


if __name__ == "__main__":
    pilot = pd.read_csv(DERIVED / "pilot_mandals.csv", dtype={"district_code": str})
    cent = pd.read_csv(DERIVED / "poc_mandal_centroids.csv", dtype={"district_code": str})
    pilot = pilot.merge(cent[["adm3_id", "lat", "lon"]], on="adm3_id")
    names = pilot.set_index("adm3_id").adm3_name
    si = pd.read_csv(POC / "config" / "sum_insured.csv")
    si = si[si.year == 2026]
    si_acre = (si.set_index("crop").si_per_ha / ACRE_PER_HA).round().to_dict()
    sow = sowing_doy()
    sow = sow[sow.adm3_id.isin(pilot.adm3_id)]
    d, chirps_last = daily_table(pilot)
    today = d.dropna(subset=["rain_mm", "gust_kmh"]).date.max()
    ix = index_values(d, sow, today)
    ts = term_sheet(ix, si_acre)
    c = claims(ix, ts)
    ts.insert(1, "mandal", ts.adm3_id.map(names))
    c.insert(1, "mandal", c.adm3_id.map(names))
    ts.to_csv(DERIVED / "wbcis_termsheet.csv", index=False)
    c.to_parquet(DERIVED / "wbcis_claims.parquet", index=False)

    yr = c.groupby(["adm3_id", "mandal", "district_code", "season", "crop", "year"]).agg(
        claim=("claim_rs_acre", "sum"), complete=("status", lambda s: (s == "complete").all())).reset_index()
    yr["claim"] = np.minimum(yr.claim, yr.crop.map(si_acre))
    yr["pct"] = 100 * yr.claim / yr.crop.map(si_acre)
    drv = c[c.claim_rs_acre > 0].groupby(["adm3_id", "crop", "year", "cover"]).claim_rs_acre.sum().reset_index()
    top = drv.sort_values("claim_rs_acre").groupby(["adm3_id", "crop", "year"]).tail(1)
    yr = yr.merge(top.rename(columns={"cover": "main_cover"})[["adm3_id", "crop", "year", "main_cover"]], how="left")
    base = yr[yr.year.between(*BASE)]
    burn = base.groupby(["mandal", "crop"]).agg(burn_pct=("pct", "mean"), burn_rs=("claim", "mean"),
                                                freq=("claim", lambda s: (s > 0).mean())).reset_index()
    by_cover = (c[c.year.between(*BASE)].groupby(["crop", "cover"]).claim_rs_acre.sum()
                / c[c.year.between(*BASE)].groupby("crop").claim_rs_acre.sum()).round(3).reset_index(name="share")
    live = c[c.year == 2026]
    live_y = yr[yr.year == 2026]
    print("covers with a significant trend (share of mandal-crop-phase):\n", ts.groupby("cover").trend.mean().round(2).to_string())
    print(f"CHIRPS ends {chirps_last.date()}, ERA5 to {today.date()}")
    print("\nburn cost 1995-2024 (% of sum insured, Rs/acre, share of years with any claim):\n",
          burn.round({"burn_pct": 1, "burn_rs": 0, "freq": 2}).to_string(index=False))
    print("\nshare of claims by cover:\n", by_cover.pivot(index="crop", columns="cover", values="share").to_string())
    print("\nKharif 2026 to date (Rs/acre):\n", live_y[["mandal", "crop", "claim", "pct", "main_cover", "complete"]].round(1).to_string(index=False))
    for yy in (2020, 2023, 2024, 2025):
        print(f"\n{yy}:", yr[yr.year == yy][["mandal", "crop", "claim", "pct", "main_cover"]].round(1).to_string(index=False))

    # Basis risk only (never part of the claim): YSR pilot mandals vs Department CCE, loss = yield < 80% of normal.
    cce = pd.read_csv(DERIVED / "validation_trigger_vs_cce.csv")[["adm3_id", "crop", "year", "loss_pct"]]
    br = yr.merge(cce, on=["adm3_id", "crop", "year"])
    br["loss"] = br.loss_pct >= 20
    from scipy.stats import spearmanr
    basis = dict(n=int(len(br)), n_loss=int(br.loss.sum()),
                 mean_claim_pct_loss=round(float(br[br.loss].pct.mean()), 1) if br.loss.any() else None,
                 mean_claim_pct_noloss=round(float(br[~br.loss].pct.mean()), 1),
                 spearman=round(float(spearmanr(br.pct, br.loss_pct).statistic), 2) if len(br) > 4 else None,
                 rows=json.loads(br[["mandal", "crop", "year", "pct", "loss_pct", "main_cover"]].round(1).to_json(orient="records")))
    print("\nbasis risk vs CCE (YSR pilot, not used in claims):", {k: v for k, v in basis.items() if k != "rows"})
    print(br[["mandal", "crop", "year", "pct", "loss_pct", "main_cover"]].round(1).to_string(index=False))
    dist = base.pct.describe(percentiles=[.5, .8, .95]).round(1).to_dict()
    dist.update(share_ge10=round(float((base.pct >= 10).mean()), 2), share_ge25=round(float((base.pct >= 25).mean()), 2))
    print("\nyearly claim % distribution 1995-2024:", dist)

    # Settlement per mandal-season: e-Panta bookings x claim Rs/acre of that crop (WBCIS claim is per unit area)
    from common import ac
    st_rows = []
    for code in pilot.district_code.unique():
        e = pd.read_parquet(ac.extract_path("parametric", f"epanta_crop_parcel_{code}.parquet"),
                            columns=["mandal", "season", "year", "crop_name", "area"])
        for p_ in pilot[pilot.district_code == code].itertuples():
            q = e[(e.mandal == p_.mandal_te) & (e.season == p_.season) & e.year.between(2023, 2026)]
            q = q.merge(yr[yr.adm3_id == p_.adm3_id][["crop", "year", "claim"]], left_on=["crop_name", "year"], right_on=["crop", "year"])
            for y_, g in q.groupby("year"):
                st_rows.append(dict(mandal=p_.adm3_name, season=p_.season, year=int(y_), lines=int(len(g)),
                                    acres=round(float(g.area.sum()), 1), paid_lines=int((g.claim > 0).sum()),
                                    amount_rs=round(float((g.area * g.claim).sum())),
                                    final=bool(y_ < 2026)))
    settle = pd.DataFrame(st_rows)
    print("\nsettlement (e-Panta bookings x claim):\n", settle.to_string(index=False))

    def rec(df):
        return json.loads(df.to_json(orient="records", date_format="iso"))
    out = dict(
        params=dict(base=list(BASE), trigger_rp=5, exit_rp=25, rh_dis=RH_DIS, t_dis=[T_DIS_LO, T_DIS_HI], t_heat=T_HEAT,
                    allocation="equal across 6 perils; within a peril by FAO-56 crop water demand over the stages it is insured in",
                    exposure=EXPOSURE,
                    si_acre=si_acre, si_source="AP SLTC Scale of Finance 2024-25 (NABARD PLP 2025-26 Palnadu, Annexure V)",
                    rain_source=f"CHIRPS to {chirps_last.date()}, then ERA5 (provisional) to {today.date()}",
                    weather_source="ERA5 reanalysis (ECMWF) via Open-Meteo, mandal centroid", data_to=str(today.date())),
        covers=[dict(cover=a, unit=u, worse_high=h, source=s) for a, u, h, s in COVERS],
        termsheet=rec(ts.drop(columns="adm3_id")),
        burn=rec(burn.round(3)),
        basis=basis, dist=dist, settlement=rec(settle),
        by_cover=rec(by_cover),
        years=rec(yr.drop(columns="adm3_id").round(2)),
        # compact claim detail for the dashboard calculator: [mandal, crop, year, phase, cover, value, value_adj, frac, rs/acre, status, start, end, rain_src]
        detail=[[r.mandal, r.crop, int(r.year), r.phase, r.cover, None if pd.isna(r.value) else round(float(r.value), 1),
                 None if pd.isna(r.value_adj) else round(float(r.value_adj), 1), round(float(r.frac), 3),
                 round(float(r.claim_rs_acre)), r.status, str(r.start), str(r.end), r.rain_src]
                for r in c[c.year >= 2005].itertuples()],
        live_phases=rec(live[live.claim_rs_acre > 0].drop(columns=["adm3_id"])[
            ["mandal", "crop", "phase", "cover", "start", "end", "status", "value", "trigger", "exit", "claim_rs_acre", "rain_src"]].round(1)),
    )
    (DERIVED / "wbcis.json").write_text(json.dumps(out, default=str), encoding="utf-8")
    print("\nwrote wbcis_termsheet.csv, wbcis_claims.parquet, wbcis.json")
