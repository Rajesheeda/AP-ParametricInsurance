# SAR depth study: rules declared before computing

Written 2026-11-14, before any of the numbers below were computed. Git history is the timestamp; nothing in this
file may change after the commit that adds it. Results go to `SAR_DEPTH_RESULTS.md` and are scored against this file.
Script: `gee_py/sar_depth.py <ee-project> <study>`. The frozen flood method (`ee_run.flood_event`) and the frozen
contract are **not changed** by this study; a better variant can only enter next season's contract through the
index qualification gate.

## A. Flood-map accuracy against an independent optical reference (PPT criterion: >= 80%)
APSDMA maps were requested and not received, so the reference is Sentinel-2, an independent sensor.
- **Events:** every event already mapped with the frozen method (22 GEE-3 events, the Budameru 2024 positive
  control, Cyclone Arnab 2026). No event is added or dropped by hand.
- **Optical reference image:** Sentinel-2 L2A (`COPERNICUS/S2_SR_HARMONIZED`) acquired within 1 day of the
  Sentinel-1 post-event image the frozen method used. Clear pixels: s2cloudless probability < 40 and SCL not
  3, 8, 9, 10 (same mask as the NDVI pipeline).
- **Reference flood:** new surface water = MNDWI (Xu 2006, bands B3, B11) > 0 on the post image AND not > 0
  on the clear-pixel median of the 60 days before the event.
- **Domain scored:** the domain the map claims: clear optical pixels, WorldCover cropland, JRC seasonality < 10,
  HAND <= 15 m (the frozen method's own masks).
- **Sample design:** stratified random sampling by map class (frozen-method flood / not flood), up to 300 points per
  stratum per event at 20 m, seed 1. Estimator: Olofsson et al. (2014) area-weighted error matrix, strata weights
  = mapped class areas in the scored domain; variants scored on the same points with the Stehman (2014) estimator
  (strata differ from the variant's map classes). 95% intervals from the stratified standard errors.
- **Scored only if:** the event yields at least 30 reference-flood points (otherwise reported as "no clear optical
  view within 1 day", with the counts).
- **Reported:** overall accuracy (the PPT metric), and flood-class user's accuracy (precision), producer's accuracy
  (recall) and F1, because overall accuracy is inflated when flood is a rare class. **PPT criterion met if the pooled
  area-weighted overall accuracy is >= 80%**; the flood-class numbers are reported whatever they are.
- **Known limits, stated now:** optical sees open water only, so flood under a crop canopy is missed by the
  reference and scores as a radar false alarm; up to 1 day between the two images (water recedes or spreads);
  20 m mixed pixels at field edges; only cloud-free events can be scored, which biases towards post-cyclone clearing.

## B. Processing sensitivity (same points as A)
Each variant changes one thing in the frozen method:
| Variant | Change |
|---|---|
| `v1` | frozen method, unchanged (computed by calling `ee_run.flood_event`) |
| `lee` | Lee (1980) adaptive speckle filter, 7x7 window, ENL 4.4 (ESA Sentinel-1 IW GRDH), instead of the 50 m focal median |
| `d2`, `d4` | change criterion 2 dB / 4 dB instead of 3 dB |
| `tm1`, `tp1` | water threshold 1 dB below / above the Otsu value |
| `single` | post image below the Otsu threshold only, no change detection |

Report each variant's overall accuracy and flood F1 with intervals. No variant replaces `v1` in this season's
contract.

## C. Flooded vegetation (double bounce)
Flooded paddy and other emergent crops can raise C-band backscatter (trunk/stem-water double bounce) instead of
lowering it, so a drop-only rule can miss them.
- **Rule:** cropland pixel, VV post - VV pre >= +3 dB and not open-water flood (variant `fv`).
- It cannot be scored against optical water (canopy hides the water). Instead it is tested like the positive control:
  share of cropland flagged on the Budameru 2024 event vs the two declared dry control dates (15 Feb, 1 Mar 2024).
  **Signal if the event share exceeds the higher control share by a factor of 2 or more**; otherwise reported as no
  usable signal at C-band for this event.

## D. Revisit: probability of a radar image within 72 h
- For each pilot mandal: all Sentinel-1 IW acquisitions with VH, 2021-01-01 to 2026-11-13, with their relative orbit.
- An acquisition is usable for an event if its relative orbit also has an image in the 60 days before.
- For every hour of each period, time to the next usable acquisition; **P(image within 72 h)** per mandal and period:
  2021 (S1A + S1B), 2022-2024 (S1A only, after S1B failed Dec 2021), 2025-2026 (current constellation).
- Pure metadata; no threshold is involved.
