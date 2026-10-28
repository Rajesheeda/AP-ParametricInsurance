"""Fused loss model: weather + satellite features -> real CCE loss event, validated leave-one-year-out.

Declared before running (2026-10-27):
  Rows     : YSR Kadapa mandal x crop x Kharif year with CCE (p15), 2019-2025.
  Target   : CCE yield < 80% of normal (PMFBY middle indemnity level). Normal = mean of the mandal-crop's
             CCE yields in the TRAINING years only (excluding the row's own year), recomputed in every fold,
             so the held-out year never enters any target.
  Features : season stress S and its max stage z for deficit / excess / dry spell (CHIRPS, p10);
             max 3-day rainfall in Jun-Jan from CHIRPS and from ERA5 (z-scored per mandal on 1995-2024);
             cyclone >= 34 kt within 150 km (IBTrACS); MODIS VCI Sep-Oct mean and Aug-Nov peak (Kogan scaling);
             crop.
  Validation: leave-one-year-out (7 folds). Probability threshold chosen on the training folds only
             (maximise balanced accuracy). Models: logistic regression (standardised, L2) and a shallow
             gradient-boosted tree model (depth 2). Baseline: best rule-based system (p15).
"""
import json

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from common import DERIVED, POC

LEVEL = 0.80
v = pd.read_csv(DERIVED / "validation_trigger_vs_cce.csv")
rows = v[["adm3_id", "Mandal", "crop", "year", "kg_ha", "S", "pay_pct"]].copy()

# stage z maxima from the trigger engine
ph = pd.read_parquet(DERIVED / "trigger_phase_stress.parquet")
ph = ph[(ph.district_code == "11") & (ph.season == "Kharif")]
z = ph.groupby(["adm3_id", "crop", "year"])[["z_deficit", "z_excess", "z_dry"]].max().reset_index()
rows = rows.merge(z, on=["adm3_id", "crop", "year"], how="left")


def rx3(path):
    r = pd.read_parquet(DERIVED / path)
    r = r[r.adm3_id.isin(rows.adm3_id.unique())].sort_values(["adm3_id", "date"])
    r["r3"] = r.groupby("adm3_id").rain_mm.transform(lambda s: s.rolling(3).sum())
    r["sy"] = np.where(r.date.dt.month == 1, r.date.dt.year - 1, r.date.dt.year)
    r = r[(r.date.dt.month >= 6) | (r.date.dt.month == 1)]
    m = r.groupby(["adm3_id", "sy"]).r3.max().reset_index()
    base = m[m.sy.between(1995, 2024)].groupby("adm3_id").r3.agg(["mean", "std"])
    m = m.join(base, on="adm3_id")
    m["z"] = (m.r3 - m["mean"]) / m["std"]
    return m.set_index(["adm3_id", "sy"]).z


for src, path in [("chirps", "rain_chirps_daily.parquet"), ("era5", "rain_era5_daily.parquet")]:
    rows[f"rx3_{src}_z"] = [rx3(path).get((a, y), np.nan) if False else None for a, y in zip(rows.adm3_id, rows.year)]
    s = rx3(path)
    rows[f"rx3_{src}_z"] = [s.get((a, y), np.nan) for a, y in zip(rows.adm3_id, rows.year)]

cat = pd.read_csv(DERIVED / "event_catalogue_era5.csv")
cat["start"] = pd.to_datetime(cat.start)
cy = cat[cat.type == "cyclone"].assign(sy=lambda d: np.where(d.start.dt.month == 1, d.start.dt.year - 1, d.start.dt.year))
cy = cy[(cy.start.dt.month >= 6) | (cy.start.dt.month == 1)]
cyc = set(zip(cy.adm3_id, cy.sy))
rows["cyclone"] = [int((a, y) in cyc) for a, y in zip(rows.adm3_id, rows.year)]

m = pd.read_parquet(POC / "data" / "gee_out" / "out_modis_ndvi_2001_2026.parquet")
for k in ("kmid", "kpeak"):
    t = m.melt(id_vars=["mid"], value_vars=[c for c in m.columns if c.startswith(k + "_")], var_name="c", value_name="ndvi").dropna()
    t["year"] = t.c.str[-4:].astype(int)
    t = t[t.year <= 2025]
    g = t.groupby("mid").ndvi
    t["vci"] = 100 * (t.ndvi - g.transform("min")) / (g.transform("max") - g.transform("min"))
    rows = rows.merge(t.rename(columns={"mid": "adm3_id", "vci": f"vci_{k}"})[["adm3_id", "year", f"vci_{k}"]], on=["adm3_id", "year"], how="left")
rows["is_paddy"] = (rows.crop == "Paddy").astype(int)
FEATS = ["S", "z_deficit", "z_excess", "z_dry", "rx3_chirps_z", "rx3_era5_z", "cyclone", "vci_kmid", "vci_kpeak", "is_paddy"]
rows = rows.dropna(subset=FEATS)


def targets(df, train_years):
    """Loss label with the normal from training years only (excluding the row's own year)."""
    out = []
    for (a, c), g in df.groupby(["adm3_id", "crop"]):
        ref = rows[(rows.adm3_id == a) & (rows.crop == c) & rows.year.isin(train_years)]
        for i, r in g.iterrows():
            base = ref[ref.year != r.year].kg_ha
            out.append((i, np.nan if len(base) < 2 else int(r.kg_ha < LEVEL * base.mean())))
    return pd.Series(dict(out))


def best_threshold(p, y):
    ts = np.unique(np.round(p, 3))
    score = [((p >= t) & (y == 1)).sum() / max(1, (y == 1).sum()) / 2 + ((p < t) & (y == 0)).sum() / max(1, (y == 0).sum()) / 2 for t in ts]
    return ts[int(np.argmax(score))]


models = {"logistic": lambda: make_pipeline(StandardScaler(), LogisticRegression(C=0.5, max_iter=2000)),
          "boosted trees (depth 2)": lambda: GradientBoostingClassifier(max_depth=2, n_estimators=150, learning_rate=0.05, random_state=0)}
years = sorted(rows.year.unique())
results = {}
for name, make in models.items():
    preds = []
    for ty in years:
        tr_years = [y for y in years if y != ty]
        tr = rows[rows.year.isin(tr_years)].copy()
        te = rows[rows.year == ty].copy()
        tr["y"], te["y"] = targets(tr, tr_years), targets(te, tr_years)
        tr, te = tr.dropna(subset=["y"]), te.dropna(subset=["y"])
        if tr.y.nunique() < 2 or te.empty:
            continue
        mdl = make().fit(tr[FEATS], tr.y.astype(int))
        thr = best_threshold(mdl.predict_proba(tr[FEATS])[:, 1], tr.y.values)
        te["p"] = mdl.predict_proba(te[FEATS])[:, 1]
        te["pred"] = (te.p >= thr).astype(int)
        preds.append(te)
    P = pd.concat(preds)
    y, f = P.y.astype(int).values, P.pred.values
    res = dict(n=int(len(P)), losses=int(y.sum()), agreement=float((f == y).mean()), pod=float((f & y).sum() / max(1, y.sum())),
               far=float((f & (1 - y)).sum() / max(1, f.sum())), auc=float(roc_auc_score(y, P.p)))
    res["by_year"] = P.groupby("year").apply(lambda d: dict(loss_rate=float(d.y.mean()), flagged=float(d.pred.mean()),
                                                            caught=float(((d.pred == 1) & (d.y == 1)).sum() / max(1, d.y.sum())))).to_dict()
    results[name] = res
    print(f"{name:24s} n={res['n']} losses={res['losses']}  agreement {res['agreement']:.0%}  POD {res['pod']:.0%}  FAR {res['far']:.0%}  AUC {res['auc']:.2f}")
    print("   by held-out year:", {k: {kk: round(vv, 2) for kk, vv in v.items()} for k, v in res["by_year"].items()})

lr = models["logistic"]().fit(rows[FEATS], targets(rows, years).reindex(rows.index).fillna(0).astype(int))
coef = dict(zip(FEATS, lr[-1].coef_[0].round(2)))
print("\nlogistic coefficients (all years, standardised):", dict(sorted(coef.items(), key=lambda x: -abs(x[1]))))
results["logistic_coefficients"] = coef
results["features"] = FEATS
(DERIVED / "loss_model_cv.json").write_text(json.dumps(results, indent=1), encoding="utf-8")
