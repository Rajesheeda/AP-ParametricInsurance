"""Run the whole POC pipeline in order.

  py -3.13 poc/run_all.py                      rebuild decisions, validation, alerts and dashboard from local data
  py -3.13 poc/run_all.py --live <ee-project>  first refresh this season's rainfall, events and radar flood maps
"""
import subprocess
import sys
from pathlib import Path

PIPE = Path(__file__).resolve().parent / "pipeline"
STEPS = [
    "p10_triggers.py",           # triggers, payout curves, burn cost
    "p11_validate_modis.py",     # second-sensor check
    "p15_validate_cce.py",       # real CCE validation
    "p17_soil_moisture.py",      # soil moisture index + CCE check
    "p18_loss_calibration.py",   # CCE-calibrated yield loss per trigger type
    "p22_dual_trigger.py",       # Lane 1 catastrophe cover: rainfall consensus x Sentinel-1, tested on CCE
    "p13_assessment.py",         # pilot decisions, two lanes
    "p23_farmer_payouts.py",     # Lane 1 per-farmer payouts on own sowing dates (YSR pilot)
    "p24_premium_power.py",      # Lane 1 premium; how much evidence the CCE data can carry
    "p19_alerts.py",             # Telugu / English alerts
    "p14_dashboard_data.py",     # dashboard
]

if "--live" in sys.argv:
    project = sys.argv[sys.argv.index("--live") + 1]
    print("== live refresh", flush=True)
    subprocess.run([sys.executable, "p20_live_refresh.py", project], cwd=PIPE, check=True)
for s in STEPS:
    print("==", s, flush=True)
    subprocess.run([sys.executable, s], cwd=PIPE, check=True, stdout=subprocess.DEVNULL)
print("done: open poc/data/dashboard/index.html (or http://127.0.0.1:8010/poc/ with the backend running)")
