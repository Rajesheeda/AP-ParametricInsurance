"""Parametric rainfall triggers and payout curves per mandal x crop (WBCIS term-sheet structure).

Phases   : FAO-56 crop stages (Allen et al. 1998, Table 11 lengths, Table 12 Kc), anchored on the
           median e-Panta sowing date of that crop in that mandal (2023-2025).
Covers   : per phase -
             deficit   : cumulative rainfall in the phase            (low is bad)
             excess    : maximum 3-day rainfall in the phase         (high is bad)
             dry_spell : longest run of days < 2.5 mm (IMD rainy day) (high is bad)
Stress   : each cover value -> non-exceedance probability within the mandal's 1995-2024 CHIRPS record
           (Weibull plotting position) -> standard normal z, oriented so higher = worse (as SPI).
           Phase stress = worst cover; season stress S = sum(phase weight x phase stress),
           phase weight = crop water demand share (mean Kc x days, FAO-56).
Trigger  : 1-in-5-year level of S for that mandal/crop; exit: 1-in-25-year level.
           Payout rises linearly 0 -> 100% of sum insured. Applying the return period once to S
           (not to 12 separate covers) keeps payout frequency at 1-in-5 by design.
           Return periods are a design choice; sensitivity is reported alongside.
Premium  : pure burn cost = mean annual payout 1995-2024 (% of sum insured); insurer adds loading.
"""
import numpy as np
import pandas as pd

from common import DERIVED, ac

BASE = (1995, 2024)
RP_TRIGGER, RP_EXIT = 5, 25
# FAO-56 Table 11 stage lengths (initial, development, mid, late) and Table 12 Kc (ini, mid, end).
FAO = {
    "Paddy":        ((30, 30, 60, 30), (1.05, 1.20, 0.75)),
    "Cotton":       ((30, 50, 60, 55), (0.35, 1.18, 0.60)),
    "Groundnut":    ((25, 35, 45, 25), (0.40, 1.15, 0.60)),
    "Red Chillies": ((25, 35, 40, 20), (0.60, 1.05, 0.90)),   # FAO 'peppers'; AP chilli runs longer
}
CROPS = {("22", "Kharif"): ["Cotton", "Red Chillies", "Paddy"],
         ("11", "Kharif"): ["Paddy", "Cotton", "Groundnut"],
         ("14", "Kharif"): ["Paddy"],
         ("10", "Rabi"): ["Paddy", "Groundnut"]}
PHASES = ["initial", "development", "mid", "late"]


def phase_kc(kc):
    ini, mid, end = kc
    return [ini, (ini + mid) / 2, mid, (mid + end) / 2]


def sowing_doy():
    """Median e-Panta sowing day-of-season per mandal x crop (2023-2025), in-season dates only."""
    m = pd.read_csv(DERIVED / "poc_mandal_centroids.csv", dtype={"district_code": str})[["district_code", "mandal_te", "adm3_id"]]
    rows = []
    for (code, season), crops in CROPS.items():
        d = pd.read_parquet(ac.extract_path("parametric", f"epanta_crop_parcel_{code}.parquet"),
                            columns=["mandal", "season", "year", "crop_name", "sowing_date"])
        d = d[(d.season == season) & d.year.between(2023, 2025) & d.crop_name.isin(crops)].copy()
        d["sd"] = pd.to_datetime(d.sowing_date, errors="coerce")
        start = pd.to_datetime(d.year.astype(str) + ("-05-01" if season == "Kharif" else "-10-01"))
        d["off"] = (d.sd - start).dt.days
        d = d[d.off.between(0, 150)]
        g = d.groupby(["mandal", "crop_name"]).off.median().round().astype(int).reset_index()
        g["district_code"], g["season"] = code, season
        rows.append(g)
    s = pd.concat(rows).merge(m, left_on=["district_code", "mandal"], right_on=["district_code", "mandal_te"])
    return s[["district_code", "adm3_id", "season", "crop_name", "off"]]


def indices(rain, sow):
    """Index value per mandal x crop x year x phase."""
    out = []
    rain = rain.set_index("date")
    for r in sow.itertuples():
        lens, kc = FAO[r.crop_name]
        series = rain[rain.adm3_id == r.adm3_id].rain_mm
        for yr in range(BASE[0], 2026):
            t0 = pd.Timestamp(yr, 5 if r.season == "Kharif" else 10, 1) + pd.Timedelta(days=r.off)
            for ph, n in zip(PHASES, lens):
                t1 = t0 + pd.Timedelta(days=n - 1)
                x = series.loc[t0:t1]
                if len(x) < n:      # season not yet complete in the series
                    break
                dry = x.lt(2.5)
                out.append(dict(adm3_id=r.adm3_id, district_code=r.district_code, season=r.season, crop=r.crop_name,
                                year=yr, phase=ph, start=t0.date(), end=t1.date(),
                                deficit=x.sum(), excess=x.rolling(3).sum().max(),
                                dry_spell=int(dry.groupby((~dry).cumsum()).sum().max())))
                t0 = t1 + pd.Timedelta(days=1)
    return pd.DataFrame(out)


def _z(base_vals, vals, worse_high):
    """Non-exceedance probability of vals within base_vals (Weibull), as standard-normal z; higher = worse."""
    from scipy.stats import norm
    b = np.sort(base_vals)
    n = len(b)
    rank = np.searchsorted(b, vals, side="right")
    p = np.clip(rank / (n + 1), 1 / (n + 1), n / (n + 1))
    z = norm.ppf(p)
    return z if worse_high else -z


def payouts(ix, rp_trigger=RP_TRIGGER, rp_exit=RP_EXIT):
    key = ["adm3_id", "crop", "phase"]
    parts = []
    for _, g in ix.groupby(key):
        base = g[g.year.between(*BASE)]
        g = g.copy()
        g["z_deficit"] = _z(base.deficit.values, g.deficit.values, worse_high=False)
        g["z_excess"] = _z(base.excess.values, g.excess.values, worse_high=True)
        g["z_dry"] = _z(base.dry_spell.values, g.dry_spell.values, worse_high=True)
        parts.append(g)
    p = pd.concat(parts)
    zc = ["z_deficit", "z_excess", "z_dry"]
    p["phase_stress"] = p[zc].max(axis=1)
    p["phase_driver"] = p[zc].idxmax(axis=1).str[2:]
    w = []
    for crop, (lens, kc) in FAO.items():
        dem = np.array(lens) * np.array(phase_kc(kc))
        w += [dict(crop=crop, phase=ph, weight=v) for ph, v in zip(PHASES, dem / dem.sum())]
    p = p.merge(pd.DataFrame(w), on=["crop", "phase"])
    p["contrib"] = p.phase_stress * p.weight
    seas = p.groupby(["district_code", "adm3_id", "season", "crop", "year"]).agg(
        S=("contrib", "sum"), n_phases=("phase", "size")).reset_index()
    seas = seas[seas.n_phases == 4]
    top = p.loc[p.groupby(["adm3_id", "crop", "year"]).contrib.idxmax(), ["adm3_id", "crop", "year", "phase", "phase_driver"]]
    seas = seas.merge(top.rename(columns={"phase": "driver_phase", "phase_driver": "driver_peril"}), on=["adm3_id", "crop", "year"])
    q = seas[seas.year.between(*BASE)].groupby(["adm3_id", "crop"]).S.agg(
        trig=lambda s: s.quantile(1 - 1 / rp_trigger), exit=lambda s: s.quantile(1 - 1 / rp_exit)).reset_index()
    seas = seas.merge(q, on=["adm3_id", "crop"])
    seas["pay_pct"] = 100 * np.clip((seas.S - seas.trig) / (seas.exit - seas.trig), 0, 1)
    return p, seas


if __name__ == "__main__":
    rain = pd.read_parquet(DERIVED / "rain_chirps_daily.parquet")
    sow = sowing_doy()
    ix = indices(rain, sow)
    p, yr = payouts(ix)
    p.to_parquet(DERIVED / "trigger_phase_stress.parquet", index=False)
    yr.to_parquet(DERIVED / "trigger_annual_payouts.parquet", index=False)
    base = yr[yr.year.between(*BASE)]
    print("payout frequency 1995-2024:", round((base.pay_pct > 0).mean(), 3))
    burn = yr[yr.year.between(*BASE)].groupby(["district_code", "crop"]).pay_pct.mean().round(1)
    print("pure burn cost, % of sum insured (mean over mandals, 1995-2024):\n", burn.to_string())
    print("\nmean payout % by district x crop, 2020-2025:\n",
          yr[yr.year >= 2020].pivot_table(index=["district_code", "crop"], columns="year", values="pay_pct", aggfunc="mean").round(1).to_string())
    sens = {f"{a}/{b}": round(payouts(ix, a, b)[1].query("year <= @BASE[1]").pay_pct.mean(), 1) for a, b in [(3, 15), (5, 25), (10, 50)]}
    d = yr[yr.year >= 2020].groupby(["district_code", "year", "driver_peril"]).size().unstack(fill_value=0)
    print("\nwhat drove the season stress, 2020-2025 (mandal-crop count):\n", d.to_string())
    print("\nburn-cost sensitivity to trigger/exit return periods:", sens)
