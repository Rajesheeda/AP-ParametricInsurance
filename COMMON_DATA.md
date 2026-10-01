# Shared department data for this repo (Parametric Insurance, case 100075)

Department data shared across all of hierachAi's AP agri POCs lives in **`C:\AP-Agri-Common`**
(overview: `C:\AP-Agri-Common\README.md`). This repo uses only its slice, which is prebuilt in
**`C:\AP-Agri-Common\extracts\parametric\`**; see `MANIFEST.md` there for the tables, row counts and columns.
Never copy raw department files into this repo, and never commit extracted department data.

## Official POC scope (Digital Agriculture Cell mail, 03-09-2026)

SPOC: Sri MM Mohiuddin / Sri Kalyan, Crop Insurance Section, 83310 56039

- **Kharif:** Palnadu, YSR Kadapa, Parvathipuram Manyam
- **Rabi:** East Godavari, Chittoor, Prakasam

> **Demo → POC.** The demo stage used the department's demo location (**Kurnool, 27 mandals, drought**).
> The POC stage moves to the districts above, which cover flood/cyclone-prone paddy (Parvathipuram Manyam, East Godavari), cotton, chilli and paddy (Palnadu),
> and drought-prone YSR and Prakasam. Plan the MODIS/ERA5/SAR exports for these districts.
> The PPT success metrics are **>=75% trigger-vs-loss correlation**, a **72-hour assessment** and a **5-year back-test vs PMFBY and CCE**.

## What to use

Files are split per district: suffix `_22` Palnadu, `_11` YSR, `_14` Parvathipuram Manyam, `_10` Chittoor, `_08` Prakasam.

| File in `extracts\parametric\` | Use it for |
|---|---|
| `epanta_crop_parcel_{22,11,14}.parquet` | Kharif 2023-2026 per-parcel crop, variety, sowing date and acres: the **insured exposure** per parcel/village/mandal |
| `epanta_crop_parcel_10.parquet` | Chittoor Kharif 2023-26 **and Rabi 2023-25** (the Rabi POC) |
| `crop_area_by_village_*.csv/.parquet` | Village x season x crop acres: exposure tables for the payout engine |
| `epanta_crop_status_{11,08}.parquet` | YSR K2025/R2025/K2026 and Prakasam sown/fallow. **Prakasam Rabi has no crop names, only status** |
| `irrigation_source_parcel_{11,10,08}.parquet` | Rainfed share, for drought-trigger weighting (Kharif 2026 only) |
| `..\_shared\village_crosswalk.csv` | Telugu e-Panta names <-> English names |

Only YSR has cadastral: `C:\AP-Agri-Common\data\cadastral\folder1_Y_S_R\` (full district).

```python
import sys; sys.path.insert(0, r"C:\AP-Agri-Common"); import agri_common as ac
import pandas as pd
exposure = pd.read_parquet(ac.extract_path("parametric", "crop_area_by_village_22.parquet"))
```

## Traps

- e-Panta names are in **Telugu**. Use `mandal_en`/`village_en` to join with ERA5/MODIS mandal polygons or English lists.
- 2023/2024 files list only booked parcels, while 2025+ list all parcels (a blank crop means unbooked). For year-on-year exposure use `crop_area_by_village`, not row counts.
- Kharif 2026 was still being reported when the data was cut, so treat it as partial.
- Irrigation `NA` means unknown, not rainfed.

## Gaps: request these from the department (purpose, fields, geography, period, format)

1. **PMFBY claims/compensation**, village or mandal level, 5 years, for all 6 POC districts. Needed for the back-test, and **none was sent**.
2. **CCE yield data** for the same districts and period. **None was sent.**
3. **East Godavari**: nothing at all was sent (Rabi POC).
4. Prakasam Rabi crop-level e-Panta (only sown/fallow status was sent).
5. Cadastral for Palnadu, Parvathipuram Manyam, Chittoor and Prakasam.
6. APSDMA flood/drought maps for past events (the PPT lists them as a validation source).
