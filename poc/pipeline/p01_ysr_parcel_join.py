"""Join YSR e-Panta crop bookings to APAIMS cadastral polygons.

Villages are matched within a mandal by overlap of base survey-number sets (robust to
spelling), then each booking joins at the finest survey level that exists in the polygons.
"""
import pandas as pd
from rapidfuzz import fuzz, process

from common import DERIVED, ac, base_survey, norm_name, norm_survey

YEARS = [2023, 2024, 2025, 2026]

cad = ac.load_cadastral("folder1_Y_S_R", farm_only=True)
cad = cad[["objectid", "MANDAL_NM", "VILL_NAME", "VILL_REV_C", "parcel_num", "geometry"]].copy()
cad["mk"] = cad.MANDAL_NM.map(norm_name)
cad["cv"] = cad.VILL_REV_C.astype(str)
cad["sv"] = cad.parcel_num.map(norm_survey)
cad["sb"] = cad.parcel_num.map(base_survey)

ep = pd.read_parquet(ac.extract_path("parametric", "epanta_crop_parcel_11.parquet"),
                     columns=["mandal_en", "village_en", "village", "season", "year", "survey",
                              "crop_name", "variety", "sowing_date", "area"])
ep = ep[ep.crop_name.notna() & ep.year.isin(YEARS)].copy()
ep["mk"] = ep.mandal_en.map(norm_name)
# mandal spellings differ between sources (Thandur/Thondur, Pulivendla/Pulivendula)
cad_mandals = sorted(cad.mk.unique())
mmap = {m: process.extractOne(m, cad_mandals, scorer=fuzz.ratio)[0] for m in ep.mk.unique()}
ep["mk"] = ep.mk.map(mmap)
ep["sv"] = ep.survey.map(norm_survey)
ep["sb"] = ep.survey.map(base_survey)

# --- village match within mandal: share of the e-Panta village's base surveys found in the
# cadastral village (cadastral lists every survey, e-Panta only booked ones, so Jaccard is wrong)
cad_sets = cad.groupby(["mk", "cv"]).sb.agg(lambda s: set(s.dropna()))
cad_names = cad.groupby(["mk", "cv"]).VILL_NAME.first().map(norm_name)
ep_sets = ep.groupby(["mk", "village"]).sb.agg(lambda s: set(s.dropna()))
ep_names = ep.groupby(["mk", "village"]).village_en.first().map(norm_name)
rows = []
for (mk, v), es in ep_sets.items():
    if mk not in cad_sets.index.get_level_values(0) or not es:
        rows.append((mk, v, None, 0.0, 0.0, 0.0))
        continue
    cands = []
    for cv, cs in cad_sets.loc[mk].items():
        cont = len(es & cs) / len(es)
        name = fuzz.ratio(ep_names.get((mk, v), ""), cad_names.get((mk, cv), "")) / 100
        cands.append((cont + 0.25 * name, cont, name, cv))
    cands.sort(reverse=True)
    score, cont, name, cv = cands[0]
    second = cands[1][0] if len(cands) > 1 else 0.0
    rows.append((mk, v, cv, cont, name, score - second))
vm = pd.DataFrame(rows, columns=["mk", "village", "cv", "containment", "name_sim", "margin"])
vm["cv_name"] = [cad_names.get((m, c)) for m, c in zip(vm.mk, vm.cv)]
vm["village_en"] = [ep_names.get((m, v)) for m, v in zip(vm.mk, vm.village)]
vm["village_ok"] = (vm.containment >= 0.6) & ((vm.margin >= 0.15) | (vm.name_sim >= 0.8))
vm.to_csv(DERIVED / "ysr_village_match.csv", index=False, encoding="utf-8-sig")

ep = ep.merge(vm.loc[vm.village_ok, ["mk", "village", "cv"]], on=["mk", "village"], how="left")

# --- survey match: exact normalized, else base survey number
exact = cad.drop_duplicates(["cv", "sv"]).set_index(["cv", "sv"]).objectid
base = cad.drop_duplicates(["cv", "sb"]).set_index(["cv", "sb"]).objectid
cad_multi_base = cad.groupby(["cv", "sb"]).size()
k_exact = pd.MultiIndex.from_arrays([ep.cv, ep.sv])
k_base = pd.MultiIndex.from_arrays([ep.cv, ep.sb])
ep["objectid"] = exact.reindex(k_exact).values
ep["join_level"] = pd.Series("exact", index=ep.index).where(ep.objectid.notna())
miss = ep.objectid.isna()
ep.loc[miss, "objectid"] = base.reindex(k_base[miss.values]).values
ep.loc[miss & ep.objectid.notna(), "join_level"] = "base"
# a base-level join is only unambiguous when the base survey is a single polygon
nb = cad_multi_base.reindex(k_base).values
ep.loc[(ep.join_level == "base") & (nb > 1), "join_level"] = "base_ambiguous"
ep["join_level"] = ep.join_level.fillna("unmatched")

rep = (ep.groupby(["season", "year", "join_level"]).area.sum().unstack(fill_value=0))
rep = rep.div(rep.sum(axis=1), axis=0).round(3)
print("village match rate (villages):", round(vm.village_ok.mean(), 3),
      " acres in matched villages:", round(ep.cv.notna().mean(), 3))
print("share of booked acres by join level:\n", rep.to_string())

ep.drop(columns=["mk"]).to_parquet(DERIVED / "ysr_epanta_parcel_join.parquet", index=False)
cad.drop(columns=["mk"]).to_parquet(DERIVED / "ysr_cadastral_farm.parquet", index=False)
print("written:", DERIVED)
