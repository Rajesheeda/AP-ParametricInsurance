"""Mandal polygons for the POC districts from geoBoundaries IND ADM3 (open data).

Telugu-only e-Panta mandal names (Palnadu, Manyam) are transliterated, then fuzzy-matched
against ADM3 units restricted to the district's bounding box.
"""
import geopandas as gpd
import pandas as pd
from indic_transliteration import sanscript
from rapidfuzz import fuzz, process

from common import DERIVED, OPEN, ac, norm_name

BBOX = {  # lon_min, lat_min, lon_max, lat_max (generous)
    "22": (78.9, 15.7, 80.5, 17.0),   # Palnadu
    "14": (82.9, 18.2, 84.1, 19.3),   # Parvathipuram Manyam
    "11": (77.9, 13.8, 79.5, 15.2),   # YSR Kadapa
    "10": (78.2, 12.6, 79.7, 13.8),   # Chittoor
}


def translit(te):
    s = sanscript.transliterate(str(te).split("(")[0], sanscript.TELUGU, sanscript.HK)
    for a, b in [("M", "n"), ("c", "ch"), ("z", "s"), ("S", "s"), ("A", "a"), ("I", "i"),
                 ("U", "u"), ("R", "r"), ("T", "t"), ("D", "d"), ("N", "n"), ("j", "z")]:
        s = s.replace(a, b)
    return norm_name(s)


g = gpd.read_file(OPEN / "gb_ind_adm3.geojson")
rows = []
for code, bb in BBOX.items():
    units = g.cx[bb[0]:bb[2], bb[1]:bb[3]].copy()
    units["k"] = units.shapeName.map(norm_name)
    ep = pd.read_parquet(ac.extract_path("parametric", f"epanta_crop_parcel_{code}.parquet"),
                         columns=["mandal", "mandal_en"]).drop_duplicates("mandal")
    for te, en in zip(ep.mandal, ep.mandal_en):
        key = norm_name(en) if isinstance(en, str) and en else translit(te)
        cands = units.k.str.replace("j", "z").tolist()
        name, score, idx = process.extractOne(key.replace("j", "z"), cands, scorer=fuzz.ratio)
        u = units.iloc[idx]
        rows.append(dict(district_code=code, mandal_te=te, mandal_en=en, key=key,
                         adm3_name=u.shapeName, adm3_id=u.shapeID, score=score, geometry=u.geometry))
m = gpd.GeoDataFrame(rows, crs=g.crs)
# Low-score matches checked by hand (2026-09-30): spelling variants of the same mandal.
REVIEWED_OK = {"achchanpeta", "chilakaluripeta", "syavalyapuran", "sitanpeta", "cuddapah",
               "chaudepalli", "chitturu", "chittoorrural", "chittoorurban"}
REVIEWED_BAD = {"sadun"}  # matched Kodur; no Sadum unit in geoBoundaries ADM3
m["ok"] = ((m.score >= 75) | m.key.isin(REVIEWED_OK)) & ~m.key.isin(REVIEWED_BAD)
m["dup"] = m.duplicated("adm3_id", keep=False)
print(m.groupby("district_code").agg(mandals=("ok", "size"), matched=("ok", "sum"), dup=("dup", "sum")).to_string())
print(m.loc[~m.ok | m.dup, ["district_code", "mandal_te", "key", "adm3_name", "score"]].to_string())
m.to_file(DERIVED / "poc_mandals.geojson", driver="GeoJSON")
