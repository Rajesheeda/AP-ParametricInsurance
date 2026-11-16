# Cyclones Arnab and Murasu: results against the rules in `CYCLONE_TEST_2026.md`

Computed 2026-11-14 to 16 with `gee_py/cyclone_test.py` (corrected per-mandal radar pass selection) and
`pipeline/p25_live_event.py --event ARNAB|MURASU` (pilot districts, full two-lane rules). Result files (gitignored):
`data/derived/cyclone_test.json`, `cyclone_test_rain.parquet`, `cyclone_test_wind.parquet`,
`live_event_arnab.json`, `live_event_murasu.json`.

## One-line answer
The radar sees real cyclone flooding where it gets a timely image (Prakasam after Murasu: 9.6% of cropland vs 0.9%
in the same weeks of 2024), but **it saw neither storm within 72 hours in most districts**, and the worst Arnab damage
(Godavari delta, mostly wind on mature paddy) was neither a rain nor a radar signal. Relief (Lane 2) reacted to both
storms in the pilot districts; the index (Lane 1) paid once (Salur, Arnab), on a weak radar signal.

## Declared scores
| # | Score | Result |
|---|---|---|
| 1 | Arnab, where: the state's top three old districts (East Godavari, West Godavari, Krishna) are our top three by net flooded cropland | **FAIL.** Ours: Guntur 16,071 ha, Srikakulam 9,964, West Godavari 5,795, East Godavari 4,748, Krishna 4,478. Spearman on the three named districts 0.5 (n = 3, uninformative). |
| 2 | Murasu, where: Prakasam and Guntur (holds most of Bapatla) each above Nellore | **PASS.** Prakasam 73,451 ha, Guntur 19,042, Nellore 14,496. |
| 3 | How much (no pass/fail) | Arnab delta: radar water is 3-8% of the reported damage (East Godavari 4,748 vs 149,057 ha; West Godavari 5,795 vs 76,752; Krishna 4,478 vs 44,836). Murasu: radar water is above the early figures (Prakasam 73,451 vs 3,151 ha in 7 mandals; Guntur 19,042 vs 5,619 ha Bapatla inundation); the later statewide figure is 1,43,617 ha. |
| 4 | When: districts with a usable image within 72 h of landfall | **Arnab 2 of 7** (Srikakulam, Vizianagaram at 52 h); delta 172 h. **Murasu 1 of 4** (Krishna at 29 h); Prakasam, Guntur, Nellore 149 h. |

## What explains the failures (checked, not assumed)
- **Arnab's delta damage was not a rain signal.** ERA5 3-day rain peaked in Vizianagaram / Visakhapatnam / Srikakulam
  (district medians ~200 mm, 19-23 mandals "very heavy"); the delta had 80-96 mm and no mandal reached "very heavy".
  ERA5 wind (exploratory, amendment 1) ranks East Godavari (median daily max 42 km/h, gust 85) > West Godavari >
  Visakhapatnam > Krishna, the damage order, but no mandal reaches IMD's 63 km/h cyclone threshold: ERA5's ~31 km grid
  flattens the storm's core. Late October is mature paddy, so lodging by wind is the likely loss.
- **The delta was not imaged until 4 Nov**, and Murasu rained 93-145 mm there on 3 Nov, so the delta radar mixes the
  two storms; Guntur's water (2 Nov pass, before Murasu) and Arnab cannot be tied together with the data we have.
- **Murasu, seasonal check (amendment 2):** Prakasam 9.6% water after Murasu vs 0.9% on the same weeks in 2024 and
  1.1-1.7% on the February/March floors: a real signal, not Rabi land preparation. Nellore 3.0% vs 7.7% in 2024: no
  signal over its own season, consistent with "largely escaped". The February/March floor left Nellore 14,496 ha of
  apparent flood; a same-season floor would not. ERA5 showed little rain at Prakasam (median 15-20 mm/day) because
  landfall rain is convective and the coast had a 1.0-1.5 m surge forecast: here radar caught what rain missed.

## Pilot districts, full two-lane rules
| | Arnab (pre-registered, ERA5 final) | Murasu (not pre-registered) |
|---|---|---|
| Rain trigger | the same 6 Manyam mandals as pre-registered | none: all below each mandal's 1-in-5 level (Amaravathi 189.0 vs 189.1 mm) |
| Lane 2 relief | 15 mandals enumeration (pre-registered 16; 4 Palnadu dropped below p99 on ERA5); 0 priority | 20 Palnadu mandals enumeration incl. Sattenapalle, Gurazala; 0 priority |
| First radar | 30 Oct (orbit 121, 52 h) for 5 mandals; 4 Nov (172 h) for 10 after the coverage fix | 9 Nov (149 h) |
| Lane 1 index | as registered 0; corrected **1: Salur 34.5% of sum insured** (0.60% flooded vs 0.07% floor, 4 Nov pass) | 0 |
| Basis risk | Salur: index pays on a weak radar signal (0.6% of cropland) | Chilakaluripet: radar 22.4% flooded vs 2.0% floor, no index payout (rain below L5) |

## What we change for next season (each through the index qualification gate on CCE)
1. **Seasonal false-alarm floor**: same calendar weeks in non-event years instead of February / March.
2. **Minimum radar signal**: a confirmation must exceed the floor by a measured margin, not by any amount.
3. **Wind peril** for late-season cyclones: ERA5 wind relative to each mandal's own history (absolute IMD thresholds
   are unreachable on ERA5), tested on CCE before it can enter the contract.
4. **72 hours is not a radar promise** over these districts (one Sentinel-1 track every 12 days): relief keeps the
   rain / photo / AEO route inside 72 h; radar confirms later.
