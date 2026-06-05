// Mock Data for AP-CropGuard Frontend Fallback Cache
// Matches the exact API shapes specified in CC's v1.0 API Contract Document

export const MOCK_DISTRICT_OVERVIEW = {
  "Kharif_2023": {
    "district": "Kurnool",
    "season": "Kharif_2023",
    "total_mandals": 27,
    "mandals_affected": 24,
    "mandals_above_threshold": 18,
    "total_area_ha": 485000,
    "total_affected_area_ha": 312400,
    "dominant_peril": "Drought",
    "assessment_status": "COMPLETE",
    "assessment_completed_hours": 58,
    "spi_district_average": -1.87,
    "alert_level": "SEVERE"
  },
  "Kharif_2020": {
    "district": "Kurnool",
    "season": "Kharif_2020",
    "total_mandals": 27,
    "mandals_affected": 0,
    "mandals_above_threshold": 0,
    "total_area_ha": 485000,
    "total_affected_area_ha": 0,
    "dominant_peril": "None",
    "assessment_status": "COMPLETE",
    "assessment_completed_hours": 12,
    "spi_district_average": 0.12,
    "alert_level": "NORMAL"
  }
};

const MANDAL_NAMES_LIST = [
  "Adoni-1", "Adoni-2", "Alur", "Aspari", "C. Belagal", "Chippagiri", "Devanakonda", 
  "Gonegandla", "Gudur", "Halaharvi", "Holagunda", "Kallur", "Kodumur", "Kosigi", 
  "Kowthalam", "Krishnagiri", "Kurnool Rural", "Kurnool Urban", "Maddikera", "Mantralayam", 
  "Nandavaram", "Orvakal", "Pattikonda", "Pedda Kadubur", "Tuggali", "Veldurthy", "Yemmiganur"
];

// Helper to generate coordinates
const STATIC_COORDS = {
  "Adoni-1": { x: 120, y: 180 }, "Adoni-2": { x: 140, y: 190 }, "Alur": { x: 60, y: 240 },
  "Aspari": { x: 100, y: 260 }, "C. Belagal": { x: 190, y: 130 }, "Chippagiri": { x: 80, y: 300 },
  "Devanakonda": { x: 140, y: 280 }, "Gonegandla": { x: 180, y: 210 }, "Gudur": { x: 230, y: 180 },
  "Halaharvi": { x: 40, y: 290 }, "Holagunda": { x: 30, y: 200 }, "Kallur": { x: 260, y: 150 },
  "Kodumur": { x: 220, y: 240 }, "Kosigi": { x: 70, y: 120 }, "Kowthalam": { x: 50, y: 160 },
  "Krishnagiri": { x: 190, y: 300 }, "Kurnool Rural": { x: 280, y: 120 }, "Kurnool Urban": { x: 290, y: 100 },
  "Maddikera": { x: 90, y: 340 }, "Mantralayam": { x: 110, y: 100 }, "Nandavaram": { x: 150, y: 140 },
  "Orvakal": { x: 300, y: 200 }, "Pattikonda": { x: 130, y: 330 }, "Pedda Kadubur": { x: 130, y: 220 },
  "Tuggali": { x: 140, y: 370 }, "Veldurthy": { x: 240, y: 320 }, "Yemmiganur": { x: 180, y: 170 }
};

const getMandalId = (index) => `KNL_${String(index + 1).padStart(3, '0')}`;

export const MOCK_MANDALS = {
  "Kharif_2023": MANDAL_NAMES_LIST.map((name, i) => {
    const isSevere = ["Alur", "Aspari", "Adoni-1", "Adoni-2", "Chippagiri", "Devanakonda", "Halaharvi", "Holagunda", "Tuggali"].includes(name);
    const isModerate = ["Pattikonda", "Maddikera", "Veldurthy", "Gudur"].includes(name);
    
    let vci = 65.4;
    let vciStatus = "NORMAL";
    let spi = 0.15;
    let spiCat = "NORMAL";
    let loss = 12.0;
    let color = "#16A34A";
    
    if (isSevere) {
      vci = 24.2 + (i % 5);
      vciStatus = "SEVERE_DROUGHT";
      spi = -1.82 - (i % 4) * 0.1;
      spiCat = "SEVERELY_DRY";
      loss = 58.5 + (i % 8);
      color = "#EA580C";
    } else if (isModerate) {
      vci = 42.1 + (i % 6);
      vciStatus = "MODERATE_STRESS";
      spi = -1.22 - (i % 3) * 0.1;
      spiCat = "MODERATELY_DRY";
      loss = 44.2 + (i % 5);
      color = "#CA8A04";
    }
    
    if (vci < 20) color = "#DC2626"; // Extreme
    
    return {
      "mandal_id": getMandalId(i),
      "mandal_name": name,
      "ndvi_current": isSevere ? 0.31 : (isModerate ? 0.42 : 0.68),
      "ndvi_baseline": 0.58,
      "ndvi_anomaly_pct": isSevere ? -46.6 : (isModerate ? -27.5 : 17.2),
      "vci": parseFloat(vci.toFixed(1)),
      "vci_status": vciStatus,
      "ndwi_current": isSevere ? -0.22 : (isModerate ? -0.05 : 0.18),
      "spi_value": parseFloat(spi.toFixed(2)),
      "spi_category": spiCat,
      "estimated_loss_pct": parseFloat(loss.toFixed(1)),
      "threshold_breached": loss >= 43.0,
      "affected_area_ha": loss >= 43.0 ? 14200 : 0,
      "dominant_crop": ["Alur", "Aspari", "Pattikonda"].includes(name) ? "Groundnut" : "Cotton",
      "map_color": color,
      ...STATIC_COORDS[name]
    };
  }),
  "Kharif_2020": MANDAL_NAMES_LIST.map((name, i) => ({
    "mandal_id": getMandalId(i),
    "mandal_name": name,
    "ndvi_current": 0.65,
    "ndvi_baseline": 0.62,
    "ndvi_anomaly_pct": 4.8,
    "vci": 78.5,
    "vci_status": "NORMAL",
    "ndwi_current": 0.22,
    "spi_value": 0.45,
    "spi_category": "NORMAL",
    "estimated_loss_pct": 8.5,
    "threshold_breached": false,
    "affected_area_ha": 0,
    "dominant_crop": ["Alur", "Aspari", "Pattikonda"].includes(name) ? "Groundnut" : "Cotton",
    "map_color": "#16A34A",
    ...STATIC_COORDS[name]
  }))
};

export const MOCK_TIMESERIES = (mandalId, season) => {
  const is2023 = season === "Kharif_2023";
  const year = is2023 ? 2023 : 2020;
  
  const timeseries = [];
  for (let idx = 0; idx < 9; idx++) {
    const baseNdvi = 0.55;
    let ndvi = baseNdvi + (idx * 0.03) - (idx > 5 ? (idx - 5) * 0.08 : 0);
    
    if (is2023) {
      // Simulate drop in dry vegetative period (weeks 30-34)
      ndvi = 0.42 + (idx * 0.01) - (idx > 3 ? (idx - 3) * 0.04 : 0);
    }
    
    const vci = ((ndvi - 0.15) / (0.85 - 0.15)) * 100;
    
    timeseries.append = timeseries.push({
      "week": `${year}-W${27 + idx}`,
      "date": `${year}-07-${String(idx * 10 + 1).padStart(2, '0')}`,
      "ndvi": parseFloat(ndvi.toFixed(2)),
      "vci": parseFloat(vci.toFixed(1)),
      "ndwi": parseFloat((ndvi * 0.7 - 0.2).toFixed(2)),
      "rainfall_mm": is2023 ? (idx === 2 ? 12.0 : 4.0) : 42.0 + idx * 5,
      "is_baseline": false
    });
  }
  
  return {
    "mandal_id": mandalId,
    "mandal_name": MANDAL_NAMES_LIST[parseInt(mandalId.split("_")[1]) - 1] || "Alur",
    "season": season,
    "timeseries": timeseries,
    "baseline_band": {
      "upper": 0.65,
      "lower": 0.45,
      "mean": 0.55
    }
  };
};

export const MOCK_PIPELINE = {
  "event_name": "Kharif 2023 Drought — Kurnool",
  "event_detected_at": "2023-09-12T06:00:00Z",
  "pipeline_stages": [
    {
      "stage_id": 1,
      "label": "Event Detected",
      "description": "SPI threshold breached — district-level alert triggered",
      "completed_at": "2023-09-12T06:00:00Z",
      "hours_from_event": 0,
      "status": "COMPLETE"
    },
    {
      "stage_id": 2,
      "label": "Satellite Analysis",
      "description": "NDVI/VCI computed for all 27 mandals",
      "completed_at": "2023-09-13T06:00:00Z",
      "hours_from_event": 24,
      "status": "COMPLETE"
    },
    {
      "stage_id": 3,
      "label": "Damage Assessment",
      "description": "Parametric triggers evaluated, loss % calculated",
      "completed_at": "2023-09-13T18:00:00Z",
      "hours_from_event": 36,
      "status": "COMPLETE"
    },
    {
      "stage_id": 4,
      "label": "Ground Verification Dispatch",
      "description": "Photo validation requests sent to field VROs",
      "completed_at": "2023-09-14T06:00:00Z",
      "hours_from_event": 48,
      "status": "COMPLETE"
    },
    {
      "stage_id": 5,
      "label": "Relief Approved",
      "description": "Final compensation order generated",
      "completed_at": "2023-09-14T18:00:00Z",
      "hours_from_event": 60,
      "status": "COMPLETE"
    }
  ],
  "total_hours_taken": 60,
  "target_hours": 72,
  "within_target": true
};

export const MOCK_CALCULATE = (crop, peril, mandalId) => {
  const sumInsured = crop === "Groundnut" ? 45000 : (crop === "Cotton" ? 60000 : 38000);
  const premiumRate = crop === "Groundnut" ? 4.2 : 3.8;
  const premium = sumInsured * (premiumRate / 100);
  
  return {
    "crop": crop,
    "peril": peril,
    "mandal": "Alur",
    "das_at_event": 73,
    "crop_stage": "Flowering/Pegging",
    "kc_multiplier": 2.0,
    "satellite_loss_pct": 61.2,
    "parametric_loss_pct": 58.4,
    "final_loss_pct": 59.8,
    "threshold_43_breached": true,
    "trigger_activated": true,
    "trigger_details": {
      "spi_trigger": true,
      "spi_value": -1.87,
      "spi_threshold": -1.0,
      "cdd_trigger": true,
      "cdd_value": 22,
      "cdd_threshold": 15
    },
    "term_sheet": {
      "crop": crop,
      "peril": peril,
      "sum_insured_per_ha": sumInsured,
      "premium_rate_pct": premiumRate,
      "premium_per_ha": premium,
      "strike_level": "SPI ≤ -1.0 OR CDD > 15",
      "exit_level": "SPI ≤ -2.0 OR CDD > 30",
      "payout_at_43_pct": Math.floor(sumInsured * 0.43),
      "payout_at_60_pct": Math.floor(sumInsured * 0.6),
      "payout_at_80_pct": Math.floor(sumInsured * 0.8),
      "payout_at_100_pct": sumInsured,
      "current_estimated_payout_per_ha": Math.floor(sumInsured * 0.598),
      "currency": "INR"
    },
    "payout_curve": [
      { "loss_pct": 0,   "payout_per_ha": 0 },
      { "loss_pct": 43,  "payout_per_ha": Math.floor(sumInsured * 0.43) },
      { "loss_pct": 50,  "payout_per_ha": Math.floor(sumInsured * 0.5) },
      { "loss_pct": 60,  "payout_per_ha": Math.floor(sumInsured * 0.6) },
      { "loss_pct": 70,  "payout_per_ha": Math.floor(sumInsured * 0.7) },
      { "loss_pct": 80,  "payout_per_ha": Math.floor(sumInsured * 0.8) },
      { "loss_pct": 90,  "payout_per_ha": Math.floor(sumInsured * 0.9) },
      { "loss_pct": 100, "payout_per_ha": sumInsured }
    ]
  };
};

export const MOCK_SIMULATE = (crop, deficit) => {
  const sumInsured = crop === "Groundnut" ? 45000 : (crop === "Cotton" ? 60000 : 38000);
  const loss = Math.min(100, Math.max(0, deficit * 1.05));
  const payout = loss >= 43 ? sumInsured * (loss / 100) : 0;
  
  return {
    "spi_computed": parseFloat((-(deficit / 30)).toFixed(2)),
    "estimated_loss_pct": parseFloat(loss.toFixed(1)),
    "threshold_breached": loss >= 43.0,
    "payout_per_ha": Math.floor(payout),
    "trigger_status": loss >= 43.0 ? "ACTIVATED" : "COMPLIANT",
    "crop_stage": "Flowering/Pegging",
    "kc_multiplier": 2.0
  };
};

export const MOCK_BACKTEST = {
  "overall_correlation": 0.82,
  "meets_target": true,
  "target_correlation": 0.75,
  "data_source": "NCIP Portal (ncip.nic.in) — PMFBY District Claims, Kurnool",
  "events": [
    {
      "event_id": "KNL_2018_DROUGHT",
      "year": 2018,
      "season": "Kharif",
      "peril": "Drought",
      "description": "Extreme meteorological drought, SPI -1.8",
      "mandals_affected": 19,
      "model_predicted_payout_per_ha": 21600,
      "actual_govt_payout_per_ha": 23400,
      "variance_pct": 7.7,
      "correlation": 0.87,
      "model_assessment": "WITHIN_RANGE"
    },
    {
      "event_id": "KNL_2020_NORMAL",
      "year": 2020,
      "season": "Kharif",
      "peril": "None",
      "description": "Normal/excess monsoon — healthy crop baseline",
      "mandals_affected": 0,
      "model_predicted_payout_per_ha": 0,
      "actual_govt_payout_per_ha": 0,
      "variance_pct": 0,
      "correlation": 1.0,
      "model_assessment": "CORRECT_NO_TRIGGER"
    },
    {
      "event_id": "KNL_2022_FLOOD",
      "year": 2022,
      "season": "Kharif",
      "peril": "Flood",
      "description": "Flash flood/excess rainfall, inundation in low-lying plains",
      "mandals_affected": 11,
      "model_predicted_payout_per_ha": 28800,
      "actual_govt_payout_per_ha": 31200,
      "variance_pct": 7.7,
      "correlation": 0.79,
      "model_assessment": "WITHIN_RANGE"
    },
    {
      "event_id": "KNL_2023_DROUGHT",
      "year": 2023,
      "season": "Kharif",
      "peril": "Drought",
      "description": "Severe agricultural drought — 24 mandals declared drought-affected, VCI < 35%",
      "mandals_affected": 24,
      "model_predicted_payout_per_ha": 26910,
      "actual_govt_payout_per_ha": 28500,
      "variance_pct": 5.6,
      "correlation": 0.83,
      "model_assessment": "WITHIN_RANGE"
    }
  ]
};

export const MOCK_PREMIUM_TABLE = {
  "district": "Kurnool",
  "season": "Kharif_2026",
  "table": [
    { "crop": "Groundnut", "peril": "Drought", "sum_insured_per_ha": 45000, "premium_rate_pct": 4.2, "premium_per_ha": 1890, "historical_event_frequency": 3, "risk_level": "HIGH" },
    { "crop": "Cotton", "peril": "Drought", "sum_insured_per_ha": 60000, "premium_rate_pct": 3.8, "premium_per_ha": 2280, "historical_event_frequency": 3, "risk_level": "HIGH" },
    { "crop": "Redgram", "peril": "Drought", "sum_insured_per_ha": 42000, "premium_rate_pct": 3.2, "premium_per_ha": 1344, "historical_event_frequency": 2, "risk_level": "MEDIUM" },
    { "crop": "Jowar", "peril": "Drought", "sum_insured_per_ha": 25000, "premium_rate_pct": 2.5, "premium_per_ha": 625, "historical_event_frequency": 2, "risk_level": "LOW" },
    { "crop": "Sunflower", "peril": "Drought", "sum_insured_per_ha": 32000, "premium_rate_pct": 3.5, "premium_per_ha": 1120, "historical_event_frequency": 2, "risk_level": "MEDIUM" }
  ]
};

export const MOCK_PHOTO_ASSESS = (crop) => {
  return {
    "assessment": {
      "damage_class": "Severely Damaged",
      "confidence_score": 0.87,
      "estimated_photo_loss_pct": 68.0,
      "crop_identified": crop,
      "disease_pest_detected": true,
      "disease_details": [
        {
          "name": crop === "Groundnut" ? "Groundnut Stem Rot (Sclerotium rolfsii)" : "Cotton Pink Bollworm (Pectinophora gossypiella)",
          "confidence": 0.76,
          "severity": "HIGH",
          "agronomic_advice": "Apply Carbendazim 0.1% or Thiophanate Methyl. Avoid waterlogging. Remove and destroy infected plants."
        }
      ],
      "analysis_source": "Claude Vision API"
    },
    "fraud_check": {
      "overall_status": "CLEAN",
      "geofence_check": {
        "status": "PASS",
        "exif_lat": 15.4289,
        "exif_lon": 78.0098,
        "claimed_mandal": "Alur",
        "coordinates_inside_mandal": true
      },
      "temporal_check": {
        "status": "PASS",
        "photo_timestamp": "2023-09-14T09:23:11Z",
        "satellite_stress_window_start": "2023-09-10T00:00:00Z",
        "satellite_stress_window_end": "2023-09-20T00:00:00Z",
        "within_window": true
      },
      "edit_signature_check": {
        "status": "PASS",
        "editor_detected": null,
        "flag": false
      },
      "gps_embedded": true,
      "gps_missing_note": null
    },
    "satellite_loss_percent": 60.0,
    "final_consensus_loss": 62.4,
    "payout_threshold_crossed": "YES",
    "weights_applied": {
      "W_sat": 0.70,
      "W_photo": 0.30
    }
  };
};

export const MOCK_WEIGHT_HISTORY = {
  "mandal_id": "KNL_003",
  "mandal_name": "Alur",
  "weight_history": [
    { "entry": 0, "label": "Initial (Prior)", "w_satellite": 0.70, "w_photo": 0.30, "event": "System default" },
    { "entry": 1, "label": "After Dispute #1", "w_satellite": 0.65, "w_photo": 0.35, "event": "VRO disputed satellite" },
    { "entry": 2, "label": "After Dispute #2", "w_satellite": 0.60, "w_photo": 0.40, "event": "VRO disputed satellite" }
  ],
  "current_weights": {
    "w_satellite": 0.60,
    "w_photo": 0.40
  },
  "total_feedbacks": 2
};

export const MOCK_EVIDENCE_LOG = [
  {
    "submission_id": "ASS_20230914_001",
    "submitted_by": "VRO_KNL_042",
    "submitted_at": "2023-09-14T09:23:11Z",
    "crop": "Groundnut",
    "damage_class": "Severely Damaged",
    "photo_loss_pct": 68.0,
    "fraud_status": "CLEAN",
    "vro_feedback": "DISPUTE_SATELLITE",
    "final_consensus_loss_pct": 64.2
  }
];

export const MOCK_CROPS = [
  {
    "name": "Groundnut",
    "soil_type": "Red sandy loam",
    "kharif_sowing_start": "06-20",
    "kharif_sowing_end": "07-15",
    "kc_stages": {
      "sowing_0_30_das": 1.0,
      "vegetative_30_60_das": 1.2,
      "flowering_60_90_das": 2.0,
      "harvest_90_120_das": 0.8
    },
    "critical_stage": "Flowering/Pegging (60-90 DAS)",
    "sum_insured_per_ha": 45000
  },
  {
    "name": "Cotton",
    "soil_type": "Black clay loam",
    "kharif_sowing_start": "06-15",
    "kharif_sowing_end": "07-10",
    "kc_stages": {
      "sowing_0_30_das": 1.0,
      "vegetative_30_60_das": 1.1,
      "flowering_60_140_das": 1.8,
      "harvest_140_180_das": 1.0
    },
    "critical_stage": "Boll Development (60-140 DAS)",
    "sum_insured_per_ha": 60000
  },
  {
    "name": "Redgram",
    "soil_type": "Red sandy loam",
    "kharif_sowing_start": "06-15",
    "kharif_sowing_end": "07-15",
    "kc_stages": {
      "sowing_0_30_das": 1.0,
      "vegetative_30_60_das": 1.0,
      "flowering_60_100_das": 1.9,
      "harvest_100_180_das": 0.9
    },
    "critical_stage": "Flowering & Pod (60-100 DAS)",
    "sum_insured_per_ha": 42000
  },
  {
    "name": "Jowar",
    "soil_type": "Black clay loam",
    "kharif_sowing_start": "06-20",
    "kharif_sowing_end": "07-15",
    "kc_stages": {
      "sowing_0_30_das": 1.0,
      "vegetative_30_60_das": 1.1,
      "flowering_60_90_das": 1.5,
      "harvest_90_120_das": 0.7
    },
    "critical_stage": "Panicle Emergence (60-90 DAS)",
    "sum_insured_per_ha": 25000
  },
  {
    "name": "Sunflower",
    "soil_type": "Red sandy loam",
    "kharif_sowing_start": "06-25",
    "kharif_sowing_end": "07-20",
    "kc_stages": {
      "sowing_0_30_das": 1.0,
      "vegetative_30_60_das": 1.2,
      "flowering_60_90_das": 1.7,
      "harvest_90_120_das": 0.8
    },
    "critical_stage": "Flowering & Heading (60-90 DAS)",
    "sum_insured_per_ha": 32000
  }
];

export const MOCK_DISASTER_HISTORY = [
  {
    "year": 2015,
    "peril": "Drought",
    "severity": "SEVERE",
    "mandals_affected": 16,
    "description": "Deficit southwest monsoon, groundnut crop failure",
    "govt_expenditure_crore": 142
  },
  {
    "year": 2018,
    "peril": "Drought",
    "severity": "EXTREME",
    "mandals_affected": 19,
    "description": "Extreme meteorological drought, SPI -1.8",
    "govt_expenditure_crore": 218
  },
  {
    "year": 2020,
    "peril": "None",
    "severity": "NORMAL",
    "mandals_affected": 0,
    "description": "Normal monsoon, healthy crop season baseline",
    "govt_expenditure_crore": 0
  },
  {
    "year": 2022,
    "peril": "Flood",
    "severity": "MODERATE",
    "mandals_affected": 11,
    "description": "Flash floods in low-lying Tungabhadra plains",
    "govt_expenditure_crore": 97
  },
  {
    "year": 2023,
    "peril": "Drought",
    "severity": "SEVERE",
    "mandals_affected": 24,
    "description": "24 mandals declared drought-affected, VCI < 35%",
    "govt_expenditure_crore": 276
  }
];
