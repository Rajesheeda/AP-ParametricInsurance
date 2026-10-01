# POC data ask: internal note

**Send:** Monday 2026-09-28 to Sri MM Mohiuddin / Sri Kalyan (Crop Insurance Section), Cc Digital Agriculture Cell.
**Email draft:** `C:\AP-Agri-Common\requests\parametric_100075_data_request.md`
**POC window:** 15 days from 2026-09-25, so it ends about 2026-10-10. We do not wait for the department. We build on what we have now and plug their data in when it arrives.

---

## 1. Scope decisions stated in the mail

| Decision | Why | Murthy question | Our answer |
|---|---|---|---|
| **Rabi pilot: Chittoor instead of East Godavari** | Zero East Godavari data was received. Chittoor Rabi e-Panta 2023-25 is in hand (Rabi 2025: 1.73 lakh parcels, 1 lakh acres). | "The department nominated East Godavari. Why did you change it?" | "We did not change it on our own; we proposed it in writing with the reason. The method is district-agnostic: East Godavari needs only its e-Panta and cadastral in the same format, and runs through the same pipeline." |
| **Kharif pilot: Palnadu, YSR Kadapa, Parvathipuram Manyam** | As nominated. Each district covers one peril: chilli and unseasonal rain (Palnadu), drought (YSR), paddy flood and cyclone (Manyam). | "Why these crops?" | "They are the department's focus crops in the problem statement, and they are the largest booked crops in each district in e-Panta." |
| **5-7 pilot mandals** | The PPT asks for 5-7 mandals prone to flood, drought or cyclone. | "Who chose the mandals?" | "The Section, if it names them. Otherwise we choose by recorded events, and the selection rule is written down." |
| **Live season = Kharif 2026** | The PPT specifies "1 disaster season". Kharif 2026 is under way and its e-Panta is already in hand. | "Is this only a back-test?" | "No. We back-test 2020-25 and monitor Kharif 2026 live." |

---

## 2. The asks, in priority order

### Ask 1: Insurance claims with CCE yields, 2020-25 (MUST)
- **Why:** The success criterion is ≥75% correlation between triggers and actual losses. CCE yield against threshold yield *is* the actual loss, and the claim paid is the benchmark payout. No open substitute exists.
- **Scope note:** Frame it as "PMFBY, and the State scheme for the years it applied", because AP ran its own free crop insurance scheme for part of this period. Asking only for "PMFBY" risks getting back empty years.
- **Murthy question:** "Your 75% correlation: against what?" → "Insurance-unit CCE yield loss and claims paid, 2020-25, supplied by the Crop Insurance Section."
- **If not given:** We report correlation against Ask 2 (damage enumeration) and against district-level yield statistics, and we label it "interim validation". **We never present a proxy as PMFBY again.** The demo was hit on exactly that.

### Ask 2: Crop damage enumeration (input-subsidy) records, 2020-25 (MUST)
- **Why:** This is the department's own post-disaster survey: village × crop × affected acres at 33%+ damage. It is the ground truth for "quantify affected crop area within 72 hours" and for the flood-mapping accuracy target. It replaces asking for APSDMA maps, which belong to a different agency and would be a slower request.
- **Murthy question:** "Flood accuracy ≥80% vs APSDMA: where are your APSDMA maps?" → "We validate against the department's own damage enumeration, which is what feeds the SDRF payments. That is a stricter test than a flood-extent map, because it measures crop damage, not water."
- **If not given:** We validate flood extent against Sentinel-1 flood-extent references from published event reports, and we state that the gap exists.

### Ask 3: APAIMS cadastral boundaries for Palnadu and Parvathipuram Manyam (HIGH)
- **Why:** The PPT requires parcel-level assessment. Today only YSR has parcel boundaries. These come from the same APAIMS system they already exported for YSR, so it is a cheap ask.
- **Murthy question:** "Parcel level in which districts?" → "YSR now. Palnadu and Manyam as soon as the cadastral is shared. Until then they run at village level with the same method."
- **If not given:** Village-level assessment for those two districts, using open village boundaries and name matching.

### Ask 4: PlanetScope access, if the department or APSAC holds a licence (CONDITIONAL)
- **Is it mandatory? No.** It is listed under "Datasets to be used" in the problem statement, so we must be able to answer for it.
- **The real reason we want it: the 72-hour window.**
  - Sentinel-1 SAR revisit over AP was **12 days** from 2022 to 2024 (Sentinel-1B failed in December 2021) and about **6 days** after Sentinel-1C came online in 2025.
  - A 72-hour promise cannot rest on Sentinel-1 alone.
  - PlanetScope is daily at 3 m. It is still optical, so clouds block it, but it adds many more chances for a clear view after an event.
- **Small parcels:**
  - The median YSR parcel is 0.82 ha, about 80 Sentinel-2 pixels, which is fine.
  - The smallest 10% are under 0.125 ha, about 12 pixels, which is marginal. At 3 m, the same parcel has about 140 pixels.
- **Murthy question:** "72 hours with a 12-day SAR revisit?" → "The 72-hour output is built from the next available acquisition of any of Sentinel-1, Sentinel-2 and PlanetScope (if licensed), plus the weather trigger, which is daily. Every parcel's result carries the date of the image it came from and a confidence level. We don't claim a satellite picture exists when it doesn't."
- **If not given:** Sentinel-1 + Sentinel-2 + daily weather triggers. The confidence level is shown per parcel, and the report states the revisit limitation openly.

---

## 3. Deliberately not asked (and why)

| Item | Reason |
|---|---|
| East Godavari data | Replaced by the Chittoor Rabi proposal (section 1). |
| Prakasam Rabi crop-level e-Panta | Not needed once Chittoor is the Rabi pilot. |
| Cadastral for Chittoor and Prakasam | Rabi runs at village level in Chittoor for this POC. Keeping the ask short improves the response. |
| APSDMA flood maps | Different agency, so a slower request. Ask 2 is the better ground truth. |
| IMD weather, soil, SAR, Sentinel-2 | Open data: IMD gridded rainfall, ERA5-Land, Sentinel-1/2 via Earth Engine, IBTrACS cyclone tracks. |

---

## 4. Proceeding now with what we have (verified 2026-09-25)

| Data | State | Use |
|---|---|---|
| e-Panta Kharif 2023-26 for Palnadu, YSR, Manyam, and Chittoor Kharif + Rabi 2023-25 | Clean: no bad areas; sowing dates 96% in-season in Palnadu | Insured exposure per parcel/village. Per-parcel sowing date gives the real crop stage. |
| YSR cadastral (2.2 lakh farm parcels) | Join rate to e-Panta is only **6% exact / 38% at base survey number** | Must fix: village-name matching plus rolling sub-divisions (`123-4`) up to the base survey number (`123`). |
| Irrigation source (Kharif 2026) | About 70% of YSR acreage is unknown | Supports drought triggers (rainfed share) but cannot decide them. |
| Palnadu, Manyam | Telugu names only, no English | Transliterate and match to open village boundaries. |
| Palnadu | 23% repeated (survey, crop) rows | Check: probably several farmers on one survey number, not a data error. |

---

## 5. Murthy rules for the whole POC

1. **Never present a proxy as actuals.** Every number shown carries its source and its data maturity.
2. **State the limit before he finds it:** revisit gaps, cloud cover, parcel size, irrigation unknowns.
3. **No hand-picked constants.** Every threshold comes from a citation (FAO-56, the GoI PMFBY guidelines, a named paper) or is measured from our own data.
4. **Name methods correctly.** Change detection is change detection. Don't call it "AI" unless a model is trained and validated with a held-out test.
5. **Satellite depth first.** Explain SAR backscatter behaviour for flooded paddy, the speckle filter, the orbit-direction choice, and the cloud mask before showing any payout.
