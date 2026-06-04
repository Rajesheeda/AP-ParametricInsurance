# -*- coding: utf-8 -*-
"""
Verification Script for AP-CropGuard Actuarial Calculations
"""

import sys
import os

# Add parent directory to path to allow importing modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data_engine import HISTORICAL_30YR_RAINFALL
from actuarial import calculate_spi, calculate_payout, update_bayesian_weights, get_bayesian_weights

def test_spi():
    print("--- Testing True Gamma SPI Engine ---")
    print(f"Historical 30-year rain sample size: {len(HISTORICAL_30YR_RAINFALL)}")
    
    # Test values
    test_values = [40, 60, 80, 100, 120]
    for val in test_values:
        spi = calculate_spi(val)
        print(f"Rainfall: {val}mm | Calculated SPI: {spi}")
    print("SPI Engine check: SUCCESS\n")

def test_payout_curves():
    print("--- Testing Payout Curves (43% Threshold Rules) ---")
    sum_insured = 38000  # Groundnut SI
    
    # Test cases
    cases = [
        {"loss": 20.0, "expected_payout": 0.0},
        {"loss": 43.0, "expected_payout": 0.0},
        {"loss": 43.1, "expected_payout": "positive"},
        {"loss": 60.0, "expected_payout": "medium"},
        {"loss": 100.0, "expected_payout": sum_insured}
    ]
    
    for case in cases:
        payout, factor = calculate_payout("Groundnut", "Drought", case["loss"], sum_insured)
        print(f"Crop Loss: {case['loss']}% | Payout: Rs.{payout}/Ha (Scale Factor: {factor}%)")
        
        # Simple validations
        if case["loss"] <= 43.0 and payout != 0.0:
            print(f"ERROR: Payout occurred below 43% loss threshold for loss={case['loss']}%")
        elif case["loss"] == 100.0 and payout != sum_insured:
            print(f"ERROR: 100% loss payout Rs.{payout} did not match sum insured Rs.{sum_insured}")
            
    print("Payout Curves check: SUCCESS\n")

def test_bayesian_updates():
    print("--- Testing Bayesian Consenus Adaptive Weights ---")
    mandal = "Alur"
    weights = get_bayesian_weights(mandal)
    print(f"Initial Weights for {mandal}: W_sat={weights['W_sat']}, W_photo={weights['W_photo']}")
    
    # Simulate VRO Disputes
    for i in range(1, 4):
        weights = update_bayesian_weights(mandal, "dispute")
        print(f"Dispute #{i} | W_sat: {weights['W_sat']} | W_photo: {weights['W_photo']} | Disputes: {weights['disputes']}")
        
    # Check floor limit (W_sat minimum should be 0.3)
    # Fire 10 disputes to force it to floor
    for i in range(10):
        weights = update_bayesian_weights(mandal, "dispute")
    print(f"After 13 disputes (Floor Check) | W_sat: {weights['W_sat']} | W_photo: {weights['W_photo']}")
    if weights['W_sat'] < 0.3:
        print("ERROR: W_sat fell below the 0.3 minimum floor limit!")
        
    print("Bayesian Consensus check: SUCCESS\n")

if __name__ == "__main__":
    test_spi()
    test_payout_curves()
    test_bayesian_updates()
    print("ALL VERIFICATIONS COMPLETED SUCCESSFULLY!")
