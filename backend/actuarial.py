# -*- coding: utf-8 -*-
"""
AP-CropGuard Actuarial Engine
Implements:
1. True Gamma-distribution SPI calculation using scipy.stats.gamma
2. Crop vulnerability coefficients (Kc) for Kurnool crops
3. Parametric weather payout curves with 43% loss threshold checks
4. Bayesian Adaptive Weight update logic based on VRO feedback loops
"""

import numpy as np
from scipy import stats
from data_engine import HISTORICAL_30YR_RAINFALL, MANDALS

# Sowing Anchor: default Kharif start is July 1st.
# Stage multipliers (Kc) based on crop calendar and vulnerability
CROP_FACTORS = {
    "Groundnut": {
        "sum_insured": 38000,  # Rs/hectare
        "stages": [
            {"name": "Sowing Failure", "min_das": 0, "max_das": 30, "Kc": 1.0},
            {"name": "Vegetative Stage", "min_das": 30, "max_das": 60, "Kc": 1.2},
            {"name": "Flowering & Pegging (Critical)", "min_das": 60, "max_das": 90, "Kc": 2.0},
            {"name": "Maturity & Harvest", "min_das": 90, "max_das": 120, "Kc": 0.8}
        ]
    },
    "Cotton": {
        "sum_insured": 55000,
        "stages": [
            {"name": "Sowing Failure", "min_das": 0, "max_das": 30, "Kc": 1.0},
            {"name": "Vegetative Stage", "min_das": 30, "max_das": 60, "Kc": 1.1},
            {"name": "Boll Development (Critical)", "min_das": 60, "max_das": 140, "Kc": 1.8},
            {"name": "Harvest Pickings", "min_das": 140, "max_das": 180, "Kc": 1.0}
        ]
    },
    "Redgram": {
        "sum_insured": 42000,
        "stages": [
            {"name": "Sowing Failure", "min_das": 0, "max_das": 30, "Kc": 1.0},
            {"name": "Vegetative Growth", "min_das": 30, "max_das": 60, "Kc": 1.0},
            {"name": "Flowering & Pod (Critical)", "min_das": 60, "max_das": 100, "Kc": 1.9},
            {"name": "Pod Maturity & Harvest", "min_das": 100, "max_das": 180, "Kc": 0.9}
        ]
    },
    "Jowar": {
        "sum_insured": 25000,
        "stages": [
            {"name": "Sowing Failure", "min_das": 0, "max_das": 30, "Kc": 1.0},
            {"name": "Vegetative Stage", "min_das": 30, "max_das": 60, "Kc": 1.1},
            {"name": "Panicle Emergence (Critical)", "min_das": 60, "max_das": 90, "Kc": 1.5},
            {"name": "Maturity & Harvest", "min_das": 90, "max_das": 120, "Kc": 0.7}
        ]
    },
    "Sunflower": {
        "sum_insured": 32000,
        "stages": [
            {"name": "Sowing Failure", "min_das": 0, "max_das": 30, "Kc": 1.0},
            {"name": "Vegetative Stage", "min_das": 30, "max_das": 60, "Kc": 1.2},
            {"name": "Flowering & Heading (Critical)", "min_das": 60, "max_das": 90, "Kc": 1.7},
            {"name": "Harvest & Desiccation", "min_das": 90, "max_das": 120, "Kc": 0.8}
        ]
    }
}

# Per-mandal Bayesian weights tracker state
# Format: {mandal_id: {"W_sat": float, "W_photo": float, "disputes": int, "agrees": int}}
BAYESIAN_STATE = {}

def get_bayesian_weights(mandal_id):
    """Retrieve weights for a mandal, initializing defaults if not present."""
    if mandal_id not in BAYESIAN_STATE:
        BAYESIAN_STATE[mandal_id] = {
            "W_sat": 0.7,
            "W_photo": 0.3,
            "disputes": 0,
            "agrees": 0,
            "history": [{"step": 0, "W_sat": 0.7, "W_photo": 0.3}]
        }
    return BAYESIAN_STATE[mandal_id]

def update_bayesian_weights(mandal_id, action):
    """
    Applies the Bayesian consensus update rule:
    Prior: W_sat = 0.7, W_photo = 0.3
    If VRO clicks "Dispute":
      W_sat = max(0.3, W_sat * (1 - 0.05))
      W_photo = 1 - W_sat
    If VRO clicks "Agree":
      W_sat = min(0.9, W_sat * (1 + 0.01))
      W_photo = 1 - W_sat
    """
    state = get_bayesian_weights(mandal_id)
    w_sat = state["W_sat"]
    
    if action == "dispute":
        w_sat = max(0.3, w_sat * 0.95)
        state["disputes"] += 1
    elif action == "agree":
        w_sat = min(0.9, w_sat * 1.01)
        state["agrees"] += 1
        
    w_photo = 1.0 - w_sat
    state["W_sat"] = float(round(w_sat, 4))
    state["W_photo"] = float(round(w_photo, 4))
    
    step = len(state["history"])
    state["history"].append({
        "step": step,
        "W_sat": state["W_sat"],
        "W_photo": state["W_photo"]
    })
    return state

# 1. True Gamma-distribution SPI algorithm
def get_spi_calculator(historical_rainfall):
    """
    Fits a gamma distribution to historical rainfall values.
    Returns a function that calculates the SPI value for any given seasonal rainfall input.
    """
    data = np.array(historical_rainfall)
    data = data[data > 0]  # Gamma fit requires values > 0
    
    if len(data) < 3:
        # Fallback if historical sample is too small
        mean = np.mean(historical_rainfall) or 100.0
        std = np.std(historical_rainfall) or 15.0
        return lambda val: float((val - mean) / std)
        
    alpha, loc, beta = stats.gamma.fit(data, floc=0)
    
    def calculate_spi(current_rainfall):
        if current_rainfall <= 0:
            current_rainfall = 0.001
        
        # Calculate cumulative probability from Gamma CDF
        cdf_val = stats.gamma.cdf(current_rainfall, alpha, loc=loc, scale=beta)
        
        # Clip CDF value to prevent inf on inverse normal CDF
        cdf_val = max(0.0001, min(0.9999, cdf_val))
        
        # Convert cumulative probability to standard normal distribution (Z-score)
        spi_val = stats.norm.ppf(cdf_val)
        return float(round(spi_val, 3))
        
    return calculate_spi

# Initialize SPI calculator using 30-year Kurnool historical record
calculate_spi = get_spi_calculator(HISTORICAL_30YR_RAINFALL)

def calculate_payout(crop_name, peril, loss_percent, sum_insured=None):
    """
    Actuarial Payout Curve with 43% loss threshold checks:
    - If loss_percent <= 43%, payout is 0 (or strictly locked to 0 per AP e-relief rules).
    - If loss_percent > 43%, payout scales linearly between Strike (43% loss) and Exit (100% loss).
    """
    if sum_insured is None:
        sum_insured = CROP_FACTORS.get(crop_name, {}).get("sum_insured", 30000)
        
    if loss_percent < 43.0:
        return 0.0, 0.0
        
    # Scale from 43% strike to 100% exit
    strike = 43.0
    exit_level = 100.0
    
    scale_factor = (loss_percent - strike) / (exit_level - strike)
    scale_factor = min(1.0, max(0.0, scale_factor))
    
    payout_per_hectare = sum_insured * scale_factor
    return float(round(payout_per_hectare, 2)), float(round(scale_factor * 100.0, 1))

def estimate_premium_rate(crop_name, peril, historical_loss_ratio):
    """
    Estimate actuarial crop premium rate based on historical risk, Stage weight,
    and Loading factors (15% expense loading + 10% risk margin).
    """
    base_rate = 0.04  # Default 4% baseline premium rate for standard crops
    
    # Modify base rate based on crop type
    crop_risk_factors = {
        "Groundnut": 1.2, # Red loam dryland, high vulnerability
        "Cotton": 1.1,    # Commercial, medium vulnerability
        "Redgram": 0.9,   # Very hardy pulse
        "Jowar": 0.8,     # Extremely drought-tolerant
        "Sunflower": 1.0  # Medium risk
    }
    
    multiplier = crop_risk_factors.get(crop_name, 1.0)
    pure_premium_rate = base_rate * multiplier * (1.0 + historical_loss_ratio)
    
    # Loadings
    expense_loading = 0.15
    risk_margin = 0.10
    commercial_premium_rate = pure_premium_rate * (1.0 + expense_loading + risk_margin)
    
    return float(round(commercial_premium_rate * 100.0, 2))
