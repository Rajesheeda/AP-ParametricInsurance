# Running the GEE scripts (user side)

1. Open https://code.earthengine.google.com with the Google account that owns your Earth Engine project.
2. **Upload assets** (Assets tab -> NEW -> Shape files, choose the .zip):
   - `poc/data/derived/gee_upload/poc_mandals.zip` -> asset name `poc_mandals`
   - `poc/data/derived/gee_upload/ysr_parcels.zip` -> asset name `ysr_parcels` (13 MB; ingestion takes 10-20 min)
   Wait until both show under Assets (Tasks tab shows ingestion progress).
3. In each script, set `var ASSETS = 'projects/<your-project-id>/assets/';` (copy the path shown on the asset).
4. Run in this order (paste script -> Run -> Tasks tab -> RUN on each task):
   - `GEE1_chirps_mandal_daily.js` -> 1 task
   - `GEE2_season_timeseries.js`   -> 8 tasks (parcels + mandals x 2023-2026)
   - `GEE3_s1_flood_events.js`     -> after Claude fills the EVENTS list
5. Outputs land in Google Drive folder `ap_poc`. Download the CSVs into
   `C:\AP-ParametricInsurance\poc\data\gee_out\` and tell Claude.

If a task fails, copy the error text from the Tasks tab to Claude.
