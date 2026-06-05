<USER_REQUEST>
i am telling CC is the backend developer and youre the frontent developer , you did without even my confirmation but anyways just cross verify CC wants to inform you about the api calls "# AP-CropGuard — API Contract Document
**Version:** 1.0 | **Date:** 2026-06-05  
**Backend Owner:** Claude Code (CC)  
**Frontend Owner:** Antigravity  
**Base URL:** `http://localhost:8000/api/v1`  
**Stack:** FastAPI (Python) + React (TypeScript)

> This document is the single source of truth. Frontend builds against mock responses.  
> Backend implements exact shapes. No deviations without updating this document first.

---

## Global Standards

### Response Envelope
Every response is wrapped in:
```json
{
  "success": true,
  "data": { ... },
  "error": null,
  "timestamp": "2026-06-05T10:30:00Z"
}
```
On error:
```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "INVALID_CROP",
    "message": "Crop 'wheat' is not modelled for Kurnool district."
  },
  "timestamp": "2026-06-05T10:30:00Z"
}
```

### Static Constants (use these everywhere in frontend)
```typescript
export const CROPS = ["Cotton", "Groundnut", "Redgram", "Jowar", "Sunflower"];
export const PERILS = ["Drought", "Flood", "DrySpell", "Heatwave"];
export const SEASONS = ["Kharif_2020", "Kharif_2023"];
export const THRESHOLD_LOSS_PCT = 43; // 43% — eligibility threshold
export const KURNOOL_MANDALS_COUNT = 27;
```

---

## SCREEN 1 ENDPOINTS — District Overview

---

### GET `/district/overview`
Returns top-level district summary for the Kurnool dashboard header.

**Query Params:**
| Param | Type | Required | Values |
|---|---|---|---|
| `season` | string | Yes | `Kharif_2020`, `Kharif_2023` |

**Response:**
```json
{
  "success": true,
  "data": {
    "district": "Kurnool",
    "season": "Kharif_2023",
    "total_mandals": 27,
    "mandals_affected": 24,
    "mandals_above_threshold": 18,
    "total_area_ha": 485000,
    "total_affected_area_ha": 312400,
 
<truncated 19751 bytes>
e — Frontend Enforcement
The 43% threshold must appear visually on ALL THREE screens:
- **Screen 1:** Red border on mandal card when `threshold_breached: true`
- **Screen 2:** Vertical `ReferenceLine` on payout curve chart at x=43
- **Screen 3:** Highlight `final_consensus_loss_pct` in red when ≥ 43

### Error States
Every API call must have a loading state and error state. Never show blank panels. On error show: "Assessment data unavailable — using last cached values."

### API Call Timing
- `/district/overview` + `/district/mandals` — called on page load and on season toggle
- `/parametric/simulate` — debounced 300ms on slider change
- `/photo/assess` — called on file upload complete (show progress bar)
- `/photo/feedback` — called immediately on VRO button click

---

## Endpoint Summary Table

| Screen | Method | Endpoint | Purpose |
|---|---|---|---|
| 1 | GET | `/district/overview` | District header stats |
| 1 | GET | `/district/mandals` | Per-mandal map data |
| 1 | GET | `/district/satellite-timeseries` | NDVI trend graph |
| 1 | GET | `/district/pipeline-status` | 72-hr timeline |
| 2 | POST | `/parametric/calculate` | Full insurance calculation |
| 2 | POST | `/parametric/simulate` | Slider real-time simulation |
| 2 | GET | `/backtest/results` | Historical back-test panel |
| 2 | GET | `/insurance/premium-table` | Premium table all crops |
| 3 | POST | `/photo/assess` | Photo CV + fraud check |
| 3 | POST | `/photo/feedback` | VRO agree/dispute |
| 3 | GET | `/photo/weight-history` | Bayesian weight chart |
| 3 | GET | `/photo/evidence-log` | Evidence log table |
| All | GET | `/meta/crops` | Crop dropdown data |
| All | GET | `/meta/mandals` | Mandal list + coordinates |
| All | GET | `/meta/disaster-history` | Kurnool history timeline |

---

*Document Version 1.0 — CC Backend / Antigravity Frontend — AP-CropGuard Hackathon 2026*"
</USER_REQUEST>
<ADDITIONAL_METADATA>
The current local time is: 2026-06-05T03:23:14+05:30.
</ADDITIONAL_METADATA>