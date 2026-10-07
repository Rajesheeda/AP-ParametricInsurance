# Positive control for the Sentinel-1 flood detector (declared before running)

**Written:** 2026-10-08, before any imagery for this event was processed.

## Why
None of the 22 pilot events produced radar flood above the dry-season false-alarm floor. That fits two explanations:
(a) the pilot events caused little standing-water flooding on cropland, or (b) the detector cannot see real floods.
A positive control separates the two.

## Event (chosen from independent public reporting, not from our outputs)
- **Budameru / Krishna floods, 31 Aug – 2 Sep 2024.** Extreme rain around Vijayawada. Widely reported flooding of
  Vijayawada city and surrounding farmland, and documented in our own catalogue as the heaviest Palnadu event (294 mm in 3 days).
- Standing crop at the time: Kharif paddy is transplanted by August, so field-preparation water is not expected.

## Area (fixed rule)
- All geoBoundaries ADM3 units whose centroid lies within **30 km of Vijayawada (16.506 N, 80.648 E)**.

## Method (frozen: identical to the pilot runs in `gee_py/ee_run.py`)
- Sentinel-1 VH, IW; first post-event image after 2 Sep 2024 within 12 days, from an orbit that also has a
  pre-event image in the 60 days before 31 Aug; 50 m focal median.
- Water threshold: Otsu on a balanced sample of JRC permanent water and WorldCover cropland.
- Change: ≥ 3 dB backscatter drop. Masks: JRC permanent water, HAND > 15 m, clusters < 8 pixels.
- Same algorithm on the dry control dates 15 Feb and 1 Mar 2024 gives each unit's false-alarm floor.

## Pass rule (fixed)
- **Pass:** flooded cropland share in the AOI exceeds the AOI's dry-control false-alarm share (the same gate used for
  the pilot mandals), and the excess is concentrated in the units nearest the reported flooding.
- **Fail:** event share is within the control range.
- Both outcomes are reported, whatever they are.

## Result (run 2026-10-08, project ap-parametricinsurance)
**PASS.**
- AOI flooded cropland: **5.61%** for the event vs **1.41%** maximum on the dry control dates.
- Largest excess over the control: Vijayawada Urban (21.6% vs 1.6%), Mangalagiri (20.8% vs 0.4%), Vijayawada Rural (18.3% vs 0.7%) and Ibrahimpatnam (9.9% vs 1.2%).
- Post-event image 13 Sep 2024 00:31, 265 h after the rain ended (outside 72 h); orbit-matched; Otsu water threshold −23.5 dB.
- Excess vs distance from Vijayawada: Spearman −0.31.
- Raw outputs: `poc/data/gee_out/out_PC_*.parquet`.
