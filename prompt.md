Do these final 5 tasks in order. 
Confirm each one before moving to next.

TASK 1 — Wire season prop correctly
In Screen1_Overview.jsx, Screen2_Insurance.jsx,
Screen3_Photo.jsx:
Verify that when TopBar season toggle changes,
all three screens re-fetch their data with 
the new season value.
Test: toggle from Kharif 2023 to Kharif 2020
on Screen 1. Mandal map colors should change
(2020 is green/healthy, 2023 is red/stressed).
Report what changes visually.

TASK 2 — Wire selectedMandal across screens
When a mandal is clicked on Screen 1 grid,
that mandal_id is passed to Screen 2 and 3
via App.jsx state.
Verify: click Adoni on Screen 1, switch to
Screen 2, confirm Adoni is pre-selected in
mandal dropdown.
Report if this works.

TASK 3 — Add Scale-Up Roadmap modal
In Screen 2, add a button at the bottom 
of the right column:
  className="btn ghost" full width
  Text: "View AP State Scale-Up Roadmap →"

onClick opens a modal overlay:
  Background: rgba(0,0,0,0.8)
  Modal box: var(--bg-card) background
    max-width 600px, border-radius 12px
    padding 32px, border var(--border-primary)

Modal title: "AP-CropGuard — Statewide 
Rollout Plan" in Syne 22px

3 phase cards inside modal:
  Phase 1 (NOW):
    Title: "Kurnool Pilot"
    Timeline: "Kharif 2026"
    Details: "27 mandals, 5 crops, 
    2 lakh farmers"
    Status badge: green "ACTIVE"
    Integrations: "PMFBY Portal, APSDMA"
    
  Phase 2 (3 MONTHS):
    Title: "Rayalaseema Expansion"  
    Timeline: "Rabi 2026-27"
    Details: "4 districts, 15 lakh farmers,
    ₹180 Cr premium pool"
    Status badge: amber "PLANNED"
    Integrations: "e-Crop AP, Mee-Seva"
    
  Phase 3 (12 MONTHS):
    Title: "All 26 AP Districts"
    Timeline: "Kharif 2027"
    Details: "26 districts, 1.2 Cr farmers,
    estimated ₹2,400 Cr savings in 
    manual survey costs"
    Status badge: blue "ROADMAP"
    Integrations: "PMFBY, APSDMA, 
    Revenue Dept, AP Fibernet"

Close button top-right: × 
Close on background click also.

TASK 4 — Add loading skeletons everywhere
In all 3 screens, verify that when data 
is loading, skeleton shimmer placeholders
show instead of blank space.
If any screen shows blank/white on load,
add className="skeleton" placeholder divs.
Report which screens needed fixes.

TASK 5 — Final end-to-end test
Run full demo sequence and report:
1. Load app → Screen 1 loads with 
   Kharif 2023 data
2. Click mandal "Alur" → 
   threshold breached banner shows red
3. Switch season to Kharif 2020 → 
   map goes green, banner changes
4. Navigate to Screen 2 → 
   Alur pre-selected in dropdown
5. Select Groundnut + Drought → 
   move rainfall slider to 70 → 
   confirm trigger ACTIVATED
6. Click Calculate → term sheet appears
7. Check backtest correlation is 
   computed value not hardcoded
8. Navigate to Screen 3 → 
   upload any JPG → click Assess
9. Click Dispute Satellite → 
   weight chart updates
10. Check evidence log shows submission

Report pass/fail for each of the 10 steps.
Any failures: fix immediately and re-test.
Confirm when all 10 pass.