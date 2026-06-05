"""
AP-CropGuard — Crop Master Data
================================
Source: FAO Irrigation & Drainage Paper No. 56 + AP Dept of
Agriculture Kharif crop calendars for Kurnool/Rayalaseema region.
Kc values represent crop stage vulnerability multipliers for
parametric loss calculation. DAS = Days After Sowing.
Sowing anchor: Kharif midpoint July 1 (range June 20 - July 15).
"""

from datetime import datetime

CROPS = {
    "Groundnut": {
        "name": "Groundnut",
        "telugu_name": "వేరుశనగ",
        "soil_type": "Red sandy loam",
        "kharif_sowing_start": "06-20",
        "kharif_sowing_end": "07-15",
        "sowing_anchor_doy": 182,
        "total_duration_days": 120,
        "sum_insured_per_ha": 45000,
        "kc_stages": {
            "sowing":     {"das_start": 0,  "das_end": 30,  "kc": 1.0, "label": "Sowing/Germination"},
            "vegetative": {"das_start": 30, "das_end": 60,  "kc": 1.2, "label": "Vegetative"},
            "flowering":  {"das_start": 60, "das_end": 90,  "kc": 2.0, "label": "Flowering/Pegging"},
            "harvest":    {"das_start": 90, "das_end": 120, "kc": 0.8, "label": "Maturity/Harvest"},
        },
        "critical_stage": "Flowering/Pegging (60-90 DAS)",
        "primary_perils": ["Drought", "DrySpell"],
        "diseases": ["Stem Rot (Sclerotium rolfsii)", "Early Leaf Spot", "Late Leaf Spot"],
    },
    "Cotton": {
        "name": "Cotton",
        "telugu_name": "పత్తి",
        "soil_type": "Black cotton soil (Vertisol)",
        "kharif_sowing_start": "06-15",
        "kharif_sowing_end": "07-10",
        "sowing_anchor_doy": 182,
        "total_duration_days": 150,
        "sum_insured_per_ha": 60000,
        "kc_stages": {
            "sowing":     {"das_start": 0,   "das_end": 30,  "kc": 1.0, "label": "Sowing/Germination"},
            "vegetative": {"das_start": 30,  "das_end": 60,  "kc": 1.1, "label": "Vegetative"},
            "flowering":  {"das_start": 60,  "das_end": 100, "kc": 1.8, "label": "Boll Development"},
            "harvest":    {"das_start": 100, "das_end": 150, "kc": 1.0, "label": "Boll Opening/Harvest"},
        },
        "critical_stage": "Boll Development (60-100 DAS)",
        "primary_perils": ["Drought", "Flood", "Heatwave"],
        "diseases": ["Pink Bollworm", "American Bollworm", "Cotton Leaf Curl Virus"],
    },
    "Redgram": {
        "name": "Redgram",
        "telugu_name": "కందులు",
        "soil_type": "Red loam / Black soil",
        "kharif_sowing_start": "06-20",
        "kharif_sowing_end": "07-15",
        "sowing_anchor_doy": 182,
        "total_duration_days": 150,
        "sum_insured_per_ha": 38000,
        "kc_stages": {
            "sowing":     {"das_start": 0,   "das_end": 30,  "kc": 1.0, "label": "Sowing/Germination"},
            "vegetative": {"das_start": 30,  "das_end": 60,  "kc": 1.0, "label": "Vegetative"},
            "flowering":  {"das_start": 60,  "das_end": 100, "kc": 1.9, "label": "Flowering/Pod Initiation"},
            "harvest":    {"das_start": 100, "das_end": 150, "kc": 0.9, "label": "Pod Filling/Harvest"},
        },
        "critical_stage": "Flowering/Pod Initiation (60-100 DAS)",
        "primary_perils": ["Drought", "DrySpell"],
        "diseases": ["Fusarium Wilt", "Sterility Mosaic Disease", "Pod Borer"],
    },
    "Jowar": {
        "name": "Jowar",
        "telugu_name": "జొన్న",
        "soil_type": "Red sandy loam / Shallow black",
        "kharif_sowing_start": "06-20",
        "kharif_sowing_end": "07-20",
        "sowing_anchor_doy": 182,
        "total_duration_days": 110,
        "sum_insured_per_ha": 28000,
        "kc_stages": {
            "sowing":     {"das_start": 0,  "das_end": 25, "kc": 1.0, "label": "Sowing/Germination"},
            "vegetative": {"das_start": 25, "das_end": 55, "kc": 1.1, "label": "Vegetative"},
            "flowering":  {"das_start": 55, "das_end": 80, "kc": 1.5, "label": "Panicle Emergence/Flowering"},
            "harvest":    {"das_start": 80, "das_end": 110,"kc": 0.7, "label": "Grain Filling/Harvest"},
        },
        "critical_stage": "Panicle Emergence (55-80 DAS)",
        "primary_perils": ["Drought", "DrySpell", "Heatwave"],
        "diseases": ["Grain Mold", "Downy Mildew", "Shoot Fly"],
    },
    "Sunflower": {
        "name": "Sunflower",
        "telugu_name": "పొద్దుతిరుగుడు",
        "soil_type": "Red loam / Sandy loam",
        "kharif_sowing_start": "06-25",
        "kharif_sowing_end": "07-15",
        "sowing_anchor_doy": 182,
        "total_duration_days": 100,
        "sum_insured_per_ha": 35000,
        "kc_stages": {
            "sowing":     {"das_start": 0,  "das_end": 25, "kc": 1.0, "label": "Sowing/Germination"},
            "vegetative": {"das_start": 25, "das_end": 50, "kc": 1.2, "label": "Vegetative"},
            "flowering":  {"das_start": 50, "das_end": 75, "kc": 1.7, "label": "Flowering/Heading"},
            "harvest":    {"das_start": 75, "das_end": 100,"kc": 0.8, "label": "Seed Filling/Harvest"},
        },
        "critical_stage": "Flowering/Heading (50-75 DAS)",
        "primary_perils": ["Drought", "Heatwave"],
        "diseases": ["Alternaria Leaf Blight", "Downy Mildew", "Stem Canker"],
    },
}

CROP_NAMES = list(CROPS.keys())
PERILS = ["Drought", "Flood", "DrySpell", "Heatwave"]
THRESHOLD_LOSS_PCT = 43.0

def get_crop(name: str) -> dict:
    if name not in CROPS:
        raise ValueError(f"Crop '{name}' not modelled. Valid crops: {CROP_NAMES}")
    return CROPS[name]

def get_kc_and_stage(crop_name: str, das: int) -> tuple:
    crop = get_crop(crop_name)
    for stage_data in crop["kc_stages"].values():
        if stage_data["das_start"] <= das < stage_data["das_end"]:
            return stage_data["kc"], stage_data["label"]
    last = list(crop["kc_stages"].values())[-1]
    return last["kc"], last["label"]

def compute_das(sowing_date_str: str, disaster_date_str: str) -> int:
    sowing = datetime.strptime(sowing_date_str, "%Y-%m-%d")
    disaster = datetime.strptime(disaster_date_str, "%Y-%m-%d")
    return max(0, (disaster - sowing).days)
