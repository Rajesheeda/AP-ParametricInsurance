# Cyclone Arnab: predictions recorded before the radar result and before any damage data

Written 2026-10-30 23:15 IST, code at commit `6d70acd` plus `pipeline/p25_live_event.py` in this commit.
**Nothing below may be changed after this commit.** Any later result is compared with this file as committed (git history is the timestamp).

## Event
- Cyclone Arnab, Very severe cyclonic storm (IMD). Crossed the Andhra Pradesh / Yanam coast near Yanam, early 28 Oct 2026 (IMD: between 02:00 and 08:00 IST).
- Event window 2026-10-27 to 2026-10-29; index window ±2 days (2026-10-25 to 2026-10-31). 72-hour mark: 2026-10-31 08:00 IST.

## Rules (frozen before the storm, unchanged here)
- **Lane 1, catastrophe cover (Cover B):** ERA5 maximum 3-day rainfall, payout linear from the mandal's own 1-in-5 level (L5) to its 1-in-25 level (L25), 2001–2024 (p22). Pays only if Sentinel-1 confirms flood on standing crops above the mandal's dry-date false-alarm floor, outside a paddy planting window (p13).
- ERA5 was published only to 2026-10-24 when this was written, so the rainfall side below is **provisional**: ECMWF IFS (the operational model ERA5 is built from) read against the ERA5 levels. GFS and ICON give the spread. The final rainfall side is ERA5 when it publishes.
- **Radar rule, stated before computing:** frozen flood method (`ee_run.flood_event`: VH, orbit-matched pre/post, 50 m focal median, Otsu water threshold, ≥3 dB drop, JRC permanent water and HAND > 15 m masked). First post-event pass available: Sentinel-1, relative orbit 121, 30 Oct 2026 00:13 UTC; pre-event images from the same orbit (18 Oct and earlier).
- **Lane 2, relief:** PRIORITY ENUMERATION where radar maps flood above the floor within 72 h; ENUMERATION (photo / AEO) where the rain trigger (3-day total above the mandal's 99th percentile, or above L5) fires; else MONITOR. Expected yield loss attached: median 25% (IQR 0–39%, n=30), calibrated on YSR Kadapa CCE, not on Manyam.

## Predictions (provisional rainfall side; radar pending)
| District | Mandal | ECMWF IFS 3-day mm | Model range (IFS, GFS, ICON) | ERA5 L5 / L25 | Rain-side payout | Lane 1 | Lane 2 |
|---|---|---|---|---|---|---|---|
| Chittoor | Vedurukuppam (pilot) | 14 | 1–14 | 131 / 220 | 0.0% | NO PAYOUT | MONITOR |
| Palnadu | Chilakaluripet H/O.Purushotha Patnam | 105 | 43–105 | 170 / 230 | 0.0% | NO PAYOUT | ENUMERATION: PHOTO / AEO |
| Palnadu | Nadendla | 104 | 60–104 | 179 / 228 | 0.0% | NO PAYOUT | ENUMERATION: PHOTO / AEO |
| Palnadu | Edlapadu | 104 | 80–104 | 179 / 228 | 0.0% | NO PAYOUT | ENUMERATION: PHOTO / AEO |
| Palnadu | Sattenapalle (pilot) | 79 | 64–91 | 189 / 207 | 0.0% | NO PAYOUT | MONITOR |
| Palnadu | Gurazala (pilot) | 38 | 6–38 | 151 / 188 | 0.0% | NO PAYOUT | MONITOR |
| Parvathipuram Manyam | Balijipeta (pilot) | 167 | 127–262 | 150 / 256 | 15.4% | AWAITING RADAR | ENUMERATION: PHOTO / AEO |
| Parvathipuram Manyam | Salur | 174 | 157–299 | 164 / 242 | 13.8% | AWAITING RADAR | ENUMERATION: PHOTO / AEO |
| Parvathipuram Manyam | Makkuva | 174 | 157–226 | 164 / 242 | 13.8% | AWAITING RADAR | ENUMERATION: PHOTO / AEO |
| Parvathipuram Manyam | Parvathipuram (pilot) | 174 | 126–194 | 164 / 242 | 13.8% | AWAITING RADAR | ENUMERATION: PHOTO / AEO |
| Parvathipuram Manyam | Palakonda | 185 | 142–302 | 172 / 287 | 11.4% | AWAITING RADAR | ENUMERATION: PHOTO / AEO |
| Parvathipuram Manyam | Pachipenta | 183 | 183–336 | 179 / 256 | 5.6% | AWAITING RADAR | ENUMERATION: PHOTO / AEO |
| Parvathipuram Manyam | Seethampeta | 170 | 170–294 | 187 / 250 | 0.0% | NO PAYOUT | ENUMERATION: PHOTO / AEO |
| Parvathipuram Manyam | Veeraghattam | 170 | 131–260 | 187 / 250 | 0.0% | NO PAYOUT | ENUMERATION: PHOTO / AEO |
| Parvathipuram Manyam | Garugubilli | 148 | 96–227 | 175 / 208 | 0.0% | NO PAYOUT | ENUMERATION: PHOTO / AEO |
| Parvathipuram Manyam | Seethanagaram | 148 | 139–227 | 175 / 208 | 0.0% | NO PAYOUT | ENUMERATION: PHOTO / AEO |
| Parvathipuram Manyam | Jiyyammavalasa | 148 | 96–233 | 175 / 208 | 0.0% | NO PAYOUT | ENUMERATION: PHOTO / AEO |
| Parvathipuram Manyam | Komarada | 116 | 102–175 | 194 / 212 | 0.0% | NO PAYOUT | ENUMERATION: PHOTO / AEO |
| Parvathipuram Manyam | Gummalakshmipuram | 116 | 90–202 | 194 / 212 | 0.0% | NO PAYOUT | ENUMERATION: PHOTO / AEO |
| YSR Kadapa | Khajipet (pilot) | 5 | 0–5 | 119 / 148 | 0.0% | NO PAYOUT | MONITOR |
| YSR Kadapa | Chapad (pilot) | 5 | 0–5 | 119 / 148 | 0.0% | NO PAYOUT | MONITOR |

Counts: 6 mandals above the rainfall trigger (all in Parvathipuram Manyam), 16 mandals for relief enumeration, 0 index payouts until radar confirms.

## How this will be scored (outcome data not yet seen)
1. **Radar:** the Lane 1 decision per mandal once the 30 Oct image is processed with the rule above.
2. **ERA5:** final rainfall side when ERA5 covers 2026-10-31.
3. **Damage:** the Department's / APSDMA's SDRF crop-damage enumeration for Arnab (area with ≥33% damage, by mandal), if shared; otherwise the official district totals as published. Score: share of mandals with reported damage that our Lane 2 list named, and share of our Lane 1 payouts that went to mandals with reported damage.
4. Known limits, stated now: mandal centroid rainfall, Manyam has no cadastral (village level only), loss calibration is from YSR, no CCE is expected for Manyam.
