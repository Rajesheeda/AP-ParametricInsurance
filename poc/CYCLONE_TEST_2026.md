# Out-of-pilot test: Cyclones Arnab and Murasu (2026), rules written before our numbers are computed

Written 2026-11-14. **Honest status:** the state's preliminary damage figures (below) were read in the press before
this file was written, so this is not a pre-registration. What is fixed: the detection method was frozen before both
storms (`ee_run.flood_event` physics, corrected pass selection per `SAR_DEPTH_STUDY.md` amendment 1), and the scoring
rule below is written before any number for these districts is computed. Script: `gee_py/cyclone_test.py <ee-project>`.
Arnab inside the pilot districts is covered separately by `ARNAB_PREREGISTRATION.md`.

## Events
| | Cyclone Arnab | Cyclone Murasu |
|---|---|---|
| IMD category | Very severe cyclonic storm | Severe cyclonic storm |
| Crossed the coast | near Yanam, early 28 Oct 2026 | near Ongole (Prakasam), early 3 Nov 2026 |
| Event window | 27-29 Oct 2026 | 2-4 Nov 2026 |

## Ground truth (state figures as published; preliminary, stage and date stated)
District names are the 2022 districts. Earth Engine's FAO GAUL boundaries carry the pre-2022 districts, so figures
are summed into those (old East Godavari = Kakinada + East Godavari + Konaseema; old West Godavari = West Godavari +
Eluru; old Krishna = Krishna + NTR; old Guntur = Guntur + Palnadu + most of Bapatla). Parts of new districts that
cross old boundaries (Bapatla, Alluri Sitharama Raju) make this approximate.

**Arnab**: Chief Minister's statement, crops on 3,33,268 ha in 16 districts; named districts:
West Godavari 76,752 ha, Kakinada 52,253, East Godavari 49,959, Konaseema 46,845, Krishna 44,836 (Deccan Chronicle).
Inundation (ETV Bharat): West Godavari 74,175, Kakinada 50,993, Konaseema 48,449, East Godavari 42,635,
Krishna 40,141, Bapatla 21,927.
-> old districts, reported damage: East Godavari ~149,000 ha, West Godavari >= 76,752, Krishna >= 44,836; others
not itemised.

**Murasu**: agriculture department, Prakasam 3,151 ha in 72 villages of 7 mandals; Bapatla 5,619 ha inundated;
SPSR Nellore "largely escaped"; statewide preliminary 52,740 ha (paddy 30,661, cotton 21,474), later 1,43,617 ha in
the state's report to the Inter-Ministerial Central Team.

## Our side (frozen rules, no new constants)
- Units: every geoBoundaries ADM3 mandal whose centroid is in the scored old districts.
  Arnab: East Godavari, West Godavari, Krishna, Guntur, Visakhapatnam, Vizianagaram, Srikakulam.
  Murasu: Prakasam, Guntur, Krishna, Nellore.
- Radar: corrected per-mandal pass selection, 12-day window after the event end; flooded cropland net of the
  mandal's own dry-date floor (same two dry dates as the pilot, 15 Feb and 1 Mar 2024, same method);
  a mandal with no pass covering half of its cropland is NOT IMAGED.
- Timeliness: hours from landfall to the first usable image, per old district.
- Rain: ERA5 (contract source) maximum 1-day and 3-day totals in the event window +/- 2 days at the mandal centroid,
  classed by IMD's published daily classes (very heavy >= 115.6 mm, extremely heavy >= 204.5 mm).

## Scoring (declared now)
1. **Arnab, where:** the official top three old districts (East Godavari, West Godavari, Krishna) are our top three by
   net flooded cropland among the seven scored. Reported also as Spearman rank over the districts with figures.
2. **Murasu, where:** net flooded cropland in Prakasam and in Guntur (which holds most of Bapatla) each exceeds Nellore.
3. **How much:** our net flooded cropland per old district next to the reported damage / inundation, as a ratio.
   No pass/fail: radar sees standing water on one date, the state counts damage of any kind (wind lodging included).
4. **When:** share of affected districts with a usable radar image within 72 h of landfall.
