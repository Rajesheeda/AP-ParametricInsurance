Add an SDC-driven actionable recommendation panel to 
Screen 1 (District Overview). This turns the Sensor 
Divergence Coefficient into an officer-facing 
recommendation that no satellite-only or weather-only 
system can produce — it's the intelligence layer.

CONCEPT:
For each mandal in the selected season, the system 
already knows: satellite loss (MODIS VCI), weather 
loss (SPI/CDD), and crop stage. From these we derive 
a per-mandal sensor decision. The recommendation 
panel ranks mandals by WHERE field officers should 
act first.

STEP 1 — Backend: add a district recommendation endpoint.
In routers/district.py add:
GET /district/recommendations?season=Kharif_2023&crop=Cotton

For each of the 27 mandals, compute:
- satellite_loss (from real MODIS VCI, latest valid 
  composite)
- weather_loss (from real rainfall SPI/CDD for that 
  mandal — use the weather_loader)
- raw_divergence = weather_loss - satellite_loss
- Classify each mandal into a PRIORITY tier:
  * "PRIORITY_1_FIELD_DISPATCH" — raw_divergence > 30 
    (satellite blind, lagged damage — automated 
    satellite assessment will UNDER-report these, 
    so dispatch field verification FIRST)
  * "PRIORITY_2_MONITOR" — sensors moderately diverge 
    (10-30)
  * "AUTOMATED_PAYOUT_SAFE" — sensors convergent 
    (within 10) — both agree, automated assessment 
    reliable, no field visit needed
  * "NON_WEATHER_REVIEW" — satellite worse than weather 
    by >30 (possible pest/disease, not drought — 
    flag for different review)

Return a dict:
- season, crop
- mandals: list sorted by priority tier then by 
  raw_divergence desc, each with:
  mandal_id, mandal_name, satellite_loss, weather_loss,
  raw_divergence, priority_tier, recommendation_text
- summary: counts per tier
- headline_recommendation: a one-line string like
  "N mandals show satellite-blind lagged damage — 
  dispatch field teams to these first; M mandals are 
  sensor-convergent and safe for automated payout."

The recommendation_text per mandal:
- PRIORITY_1: "Satellite under-reporting due to 
  reproductive-stage lag. Dispatch field verification 
  — automated assessment will miss this loss."
- AUTOMATED_PAYOUT_SAFE: "Both sensors agree. 
  Automated payout reliable. No field visit needed."
- etc.

STEP 2 — Frontend: add a "Field Dispatch Intelligence" 
panel on Screen 1.
Place it in the right column or below the mandal grid.
Title: "Field Dispatch Recommendation"
Subtitle: "SDC-driven officer prioritization"

Show:
- The headline_recommendation prominently at top
- A ranked list/table of mandals grouped by priority 
  tier:
  PRIORITY_1_FIELD_DISPATCH — red header, list mandals
  PRIORITY_2_MONITOR — amber
  AUTOMATED_PAYOUT_SAFE — green
  NON_WEATHER_REVIEW — purple
- Each mandal row: name, satellite vs weather loss 
  (small), and the recommendation text
- A small caption: "This prioritization is only 
  possible because the Sensor Divergence Coefficient 
  identifies where satellite assessment is blind. 
  A satellite-only system would dispatch officers 
  uniformly or miss lagged-damage mandals entirely."

This is the recommendation/intelligence innovation — 
it tells officers WHERE to act, derived from the SDC.

After implementing, call the recommendations endpoint 
for Kharif_2023 + Cotton and report:
- how many mandals in each priority tier
- the headline_recommendation text
- confirm the panel renders on Screen 1
Take a screenshot.