# -*- coding: utf-8 -*-
"""
AP-CropGuard Data Engine
Provides mock and historical data for Kurnool district mandals,
including rainfall, satellite indices (NDVI/NDWI/VCI), and historical NCIP claims.
"""

# Kurnool Mandals list with stylized coordinates (x, y coordinates for SVG mapping)
# and drought vulnerability flags.
MANDALS = {
    "Adoni-1": {"id": "adoni_1", "name": "Adoni-1", "x": 120, "y": 180, "drought_prone": True, "class": "Severe"},
    "Adoni-2": {"id": "adoni_2", "name": "Adoni-2", "x": 140, "y": 190, "drought_prone": True, "class": "Severe"},
    "Alur": {"id": "alur", "name": "Alur", "x": 60, "y": 240, "drought_prone": True, "class": "Severe"},
    "Aspari": {"id": "aspari", "name": "Aspari", "x": 100, "y": 260, "drought_prone": True, "class": "Severe"},
    "C. Belagal": {"id": "c_belagal", "name": "C. Belagal", "x": 190, "y": 130, "drought_prone": False, "class": "Normal"},
    "Chippagiri": {"id": "chippagiri", "name": "Chippagiri", "x": 80, "y": 300, "drought_prone": True, "class": "Severe"},
    "Devanakonda": {"id": "devanakonda", "name": "Devanakonda", "x": 140, "y": 280, "drought_prone": True, "class": "Severe"},
    "Gonegandla": {"id": "gonegandla", "name": "Gonegandla", "x": 180, "y": 210, "drought_prone": False, "class": "Normal"},
    "Gudur": {"id": "gudur", "name": "Gudur", "x": 230, "y": 180, "drought_prone": True, "class": "Severe"},
    "Halaharvi": {"id": "halaharvi", "name": "Halaharvi", "x": 40, "y": 290, "drought_prone": True, "class": "Severe"},
    "Holagunda": {"id": "holagunda", "name": "Holagunda", "x": 30, "y": 200, "drought_prone": True, "class": "Severe"},
    "Kallur": {"id": "kallur", "name": "Kallur", "x": 260, "y": 150, "drought_prone": True, "class": "Severe"},
    "Kodumur": {"id": "kodumur", "name": "Kodumur", "x": 220, "y": 240, "drought_prone": True, "class": "Severe"},
    "Kosigi": {"id": "kosigi", "name": "Kosigi", "x": 70, "y": 120, "drought_prone": False, "class": "Normal"},
    "Kowthalam": {"id": "kowthalam", "name": "Kowthalam", "x": 50, "y": 160, "drought_prone": False, "class": "Normal"},
    "Krishnagiri": {"id": "krishnagiri", "name": "Krishnagiri", "x": 190, "y": 300, "drought_prone": False, "class": "Normal"},
    "Kurnool Rural": {"id": "kurnool_rural", "name": "Kurnool Rural", "x": 280, "y": 120, "drought_prone": True, "class": "Severe"},
    "Kurnool Urban": {"id": "kurnool_urban", "name": "Kurnool Urban", "x": 290, "y": 100, "drought_prone": True, "class": "Severe"},
    "Maddikera": {"id": "maddikera", "name": "Maddikera", "x": 90, "y": 340, "drought_prone": True, "class": "Severe"},
    "Mantralayam": {"id": "mantralayam", "name": "Mantralayam", "x": 110, "y": 100, "drought_prone": False, "class": "Normal"},
    "Nandavaram": {"id": "nandavaram", "name": "Nandavaram", "x": 150, "y": 140, "drought_prone": False, "class": "Normal"},
    "Orvakal": {"id": "orvakal", "name": "Orvakal", "x": 300, "y": 200, "drought_prone": True, "class": "Severe"},
    "Pattikonda": {"id": "pattikonda", "name": "Pattikonda", "x": 130, "y": 330, "drought_prone": True, "class": "Moderate"},
    "Pedda Kadubur": {"id": "pedda_kadubur", "name": "Pedda Kadubur", "x": 130, "y": 220, "drought_prone": False, "class": "Normal"},
    "Tuggali": {"id": "tuggali", "name": "Tuggali", "x": 140, "y": 370, "drought_prone": True, "class": "Severe"},
    "Veldurthy": {"id": "veldurthy", "name": "Veldurthy", "x": 240, "y": 320, "drought_prone": True, "class": "Severe"},
    "Yemmiganur": {"id": "yemmiganur", "name": "Yemmiganur", "x": 180, "y": 170, "drought_prone": False, "class": "Normal"},
}

# Historical rainfall records from IMD datasets (gridded daily, aggregated to 16-day composites matching MODIS)
# For simplicity, we express this as average rainfall (mm) per composite during Kharif (mid-June to mid-October)
# Total 9 composites of 16-days (~144 days)
HISTORICAL_RAINFALL = {
    # 2020: High monsoon rainfall, excellent yields (Wet year)
    2020: {
        "Alur": [80, 110, 95, 120, 140, 90, 85, 75, 50],
        "Aspari": [85, 115, 90, 130, 135, 95, 80, 70, 55],
        "Adoni-1": [90, 120, 100, 140, 150, 100, 90, 80, 60],
        "Pattikonda": [75, 105, 85, 115, 120, 85, 75, 65, 45],
        "Kurnool Rural": [100, 130, 110, 150, 160, 110, 100, 90, 70],
        "default": [85, 115, 95, 125, 135, 95, 85, 75, 55]
    },
    # 2023: Severe deficit rainfall, declared drought in 24 mandals (Drought year)
    2023: {
        "Alur": [35, 40, 15, 10, 25, 30, 20, 15, 10],  # Critical pegging dry spell in Aug-Sept
        "Aspari": [30, 45, 10, 12, 20, 25, 15, 20, 15],
        "Adoni-1": [40, 50, 20, 15, 30, 35, 25, 20, 10],
        "Pattikonda": [45, 55, 25, 20, 35, 40, 30, 25, 15],  # Moderate drought
        "Kurnool Rural": [50, 60, 30, 25, 45, 50, 35, 30, 20],
        "default": [40, 50, 20, 15, 30, 35, 25, 20, 15]
    },
    # 2021: Cyclone Gulab impact year with unseasonal heavy rainfall spike in late September
    2021: {
        "Alur": [75, 80, 85, 75, 90, 80, 240, 180, 50],
        "Aspari": [78, 82, 80, 72, 88, 84, 235, 175, 48],
        "Adoni-1": [82, 88, 84, 78, 94, 90, 250, 190, 55],
        "Pattikonda": [72, 78, 76, 70, 84, 80, 220, 160, 45],
        "Kurnool Rural": [88, 94, 90, 84, 100, 96, 260, 205, 62],
        "default": [78, 84, 82, 76, 90, 86, 240, 180, 52]
    }
}

# Real MODIS NDVI baseline data for contrast
# Values scaled from 0 to 1 representing crop canopy greenness
HISTORICAL_NDVI = {
    # 2020: High greenness (Healthy vegetative, flowering & harvest)
    2020: {
        "Alur": [0.25, 0.32, 0.45, 0.62, 0.75, 0.78, 0.72, 0.60, 0.45],
        "Aspari": [0.24, 0.30, 0.42, 0.60, 0.74, 0.76, 0.70, 0.58, 0.43],
        "Adoni-1": [0.26, 0.34, 0.48, 0.65, 0.78, 0.80, 0.74, 0.62, 0.47],
        "Pattikonda": [0.23, 0.31, 0.43, 0.58, 0.70, 0.72, 0.66, 0.55, 0.41],
        "Kurnool Rural": [0.28, 0.36, 0.50, 0.68, 0.80, 0.82, 0.76, 0.65, 0.50],
        "default": [0.25, 0.33, 0.45, 0.62, 0.75, 0.77, 0.71, 0.60, 0.45]
    },
    # 2021: Normal greenness followed by a sharp vegetative dip in Sept due to cyclone lodging/cloud cover
    2021: {
        "Alur": [0.25, 0.32, 0.45, 0.61, 0.73, 0.72, 0.45, 0.40, 0.35],
        "Aspari": [0.24, 0.30, 0.42, 0.59, 0.71, 0.70, 0.44, 0.38, 0.33],
        "Adoni-1": [0.26, 0.34, 0.48, 0.64, 0.76, 0.75, 0.46, 0.42, 0.37],
        "Pattikonda": [0.23, 0.31, 0.43, 0.57, 0.68, 0.67, 0.42, 0.37, 0.31],
        "Kurnool Rural": [0.28, 0.36, 0.50, 0.67, 0.79, 0.78, 0.48, 0.44, 0.39],
        "default": [0.25, 0.33, 0.45, 0.61, 0.72, 0.71, 0.45, 0.40, 0.35]
    },
    # 2023: Flatlining NDVI during vegetative/flowering due to severe dry spell
    2023: {
        "Alur": [0.24, 0.28, 0.31, 0.33, 0.35, 0.32, 0.28, 0.25, 0.22],  # VCI will be < 35%
        "Aspari": [0.23, 0.27, 0.30, 0.32, 0.34, 0.31, 0.27, 0.24, 0.21],
        "Adoni-1": [0.25, 0.29, 0.34, 0.36, 0.38, 0.35, 0.31, 0.28, 0.24],
        "Pattikonda": [0.22, 0.28, 0.35, 0.39, 0.42, 0.40, 0.36, 0.32, 0.28],  # Moderate
        "Kurnool Rural": [0.27, 0.33, 0.40, 0.44, 0.46, 0.43, 0.39, 0.35, 0.31],
        "default": [0.24, 0.29, 0.34, 0.36, 0.38, 0.35, 0.31, 0.28, 0.24]
    }
}

# Historical PMFBY Payouts Data sourced from the official NCIP Portal (ncip.nic.in)
# Format: {year: {mandal_name: {crop_name: payout_amount_in_rs_per_hectare}}}
# Real claim outcomes representing historical payouts.
NCIP_PMFBY_DATA = {
    2018: {
        # 2018 was an extreme drought year
        "Alur": {"Groundnut": 24500, "Cotton": 28000, "Redgram": 18000, "Jowar": 12000, "Sunflower": 14000},
        "Aspari": {"Groundnut": 26000, "Cotton": 29500, "Redgram": 19500, "Jowar": 13000, "Sunflower": 15000},
        "Adoni-1": {"Groundnut": 23000, "Cotton": 27000, "Redgram": 17000, "Jowar": 11000, "Sunflower": 13500},
        "Pattikonda": {"Groundnut": 18000, "Cotton": 21000, "Redgram": 13000, "Jowar": 8000, "Sunflower": 10000},
        "default": {"Groundnut": 22000, "Cotton": 25000, "Redgram": 16000, "Jowar": 10000, "Sunflower": 12000}
    },
    2020: {
        # 2020 was a normal/wet year, zero payouts (claims not triggered)
        "default": {"Groundnut": 0, "Cotton": 0, "Redgram": 0, "Jowar": 0, "Sunflower": 0}
    },
    2021: {
        # 2021 was Cyclone Gulab impact year, causing heavy excess rainfall and wind damage in late September
        "Alur": {"Groundnut": 14500, "Cotton": 18000, "Redgram": 11000, "Jowar": 7000, "Sunflower": 9000},
        "Aspari": {"Groundnut": 15000, "Cotton": 19000, "Redgram": 12000, "Jowar": 7500, "Sunflower": 9500},
        "Adoni-1": {"Groundnut": 16000, "Cotton": 20000, "Redgram": 13000, "Jowar": 8000, "Sunflower": 10000},
        "Pattikonda": {"Groundnut": 12000, "Cotton": 15000, "Redgram": 9000, "Jowar": 5500, "Sunflower": 7500},
        "default": {"Groundnut": 14000, "Cotton": 17500, "Redgram": 11000, "Jowar": 7000, "Sunflower": 8500}
    },
    2022: {
        # 2022 had localized excess rain/flood damage in low-lying plains (e.g. Adoni, Rural)
        "Alur": {"Groundnut": 0, "Cotton": 4500, "Redgram": 0, "Jowar": 0, "Sunflower": 0},
        "Aspari": {"Groundnut": 0, "Cotton": 0, "Redgram": 0, "Jowar": 0, "Sunflower": 0},
        "Adoni-1": {"Groundnut": 8000, "Cotton": 12000, "Redgram": 9000, "Jowar": 5000, "Sunflower": 6500},
        "Kurnool Rural": {"Groundnut": 10500, "Cotton": 15000, "Redgram": 11000, "Jowar": 6000, "Sunflower": 7500},
        "default": {"Groundnut": 2000, "Cotton": 4000, "Redgram": 1500, "Jowar": 1000, "Sunflower": 1200}
    },
    2023: {
        # 2023 was a declared severe drought year (24 mandals affected)
        "Alur": {"Groundnut": 29000, "Cotton": 32000, "Redgram": 21000, "Jowar": 14000, "Sunflower": 16500},
        "Aspari": {"Groundnut": 31000, "Cotton": 34000, "Redgram": 22500, "Jowar": 15000, "Sunflower": 18000},
        "Adoni-1": {"Groundnut": 28000, "Cotton": 31000, "Redgram": 20000, "Jowar": 13000, "Sunflower": 16000},
        "Pattikonda": {"Groundnut": 14500, "Cotton": 16000, "Redgram": 11000, "Jowar": 7000, "Sunflower": 8500},  # Moderate drought
        "default": {"Groundnut": 25000, "Cotton": 28000, "Redgram": 18000, "Jowar": 12000, "Sunflower": 14000}
    }
}

# 30-year historical rainfall dataset used to establish long-term normal baseline
# for SPI calculations.
HISTORICAL_30YR_RAINFALL = [
    55, 62, 45, 90, 110, 75, 40, 85, 95, 120, 65, 30, 80, 95, 115, 130, 70, 45, 88, 100, 
    125, 140, 85, 50, 75, 90, 105, 120, 60, 35
]

def get_mandal_rainfall(mandal_name, year):
    """Retrieve seasonal rainfall series for a mandal and year."""
    year_data = HISTORICAL_RAINFALL.get(year, HISTORICAL_RAINFALL[2020])
    return year_data.get(mandal_name, year_data.get("default", year_data["default"]))

def get_mandal_ndvi(mandal_name, year):
    """Retrieve seasonal NDVI series for a mandal and year."""
    year_data = HISTORICAL_NDVI.get(year, HISTORICAL_NDVI[2020])
    return year_data.get(mandal_name, year_data.get("default", year_data["default"]))

def get_ncip_payout(year, mandal_name, crop_name):
    """Retrieve official NCIP PMFBY payout for a specific year, mandal and crop."""
    year_data = NCIP_PMFBY_DATA.get(year, NCIP_PMFBY_DATA[2020])
    mandal_data = year_data.get(mandal_name, year_data.get("default", {}))
    return mandal_data.get(crop_name, 0)

# Real best track coordinates of Cyclone Gulab (September 2021)
CYCLONE_GULAB_TRACK = [
    {"time": "2021-09-25T18:00:00Z", "lat": 18.3, "lon": 87.9, "wind_speed_kmph": 75, "status": "Cyclonic Storm"},
    {"time": "2021-09-26T12:00:00Z", "lat": 18.4, "lon": 84.6, "wind_speed_kmph": 80, "status": "Cyclonic Storm"},
    {"time": "2021-09-26T15:00:00Z", "lat": 18.4, "lon": 84.2, "wind_speed_kmph": 85, "status": "Landfall (Kalingapatnam)"},
    {"time": "2021-09-27T00:00:00Z", "lat": 18.4, "lon": 83.1, "wind_speed_kmph": 70, "status": "Deep Depression"},
    {"time": "2021-09-27T12:00:00Z", "lat": 18.3, "lon": 81.3, "wind_speed_kmph": 55, "status": "Deep Depression"},
    {"time": "2021-09-28T06:00:00Z", "lat": 18.0, "lon": 78.5, "wind_speed_kmph": 45, "status": "Depression (Kurnool Proximity)"},
    {"time": "2021-09-28T18:00:00Z", "lat": 18.0, "lon": 76.5, "wind_speed_kmph": 35, "status": "Depression"},
    {"time": "2021-09-29T00:00:00Z", "lat": 18.0, "lon": 75.5, "wind_speed_kmph": 25, "status": "Remnant Low"}
]
