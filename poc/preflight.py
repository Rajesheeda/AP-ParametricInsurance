"""Demo-morning preflight: is everything up, fresh and clean, and which numbers should be said out loud?

Run after the morning refresh and the backend restart:  py -3.13 poc/preflight.py [--no-vision]
Checks (each prints OK / WARN / FAIL):
  backend   - dashboard, compensation, photo events and farmer endpoints answer on 127.0.0.1:8010
  freshness - every step is newer than its inputs (live event -> payouts -> compensation / alerts -> dashboard)
  logs      - no rehearsal entries left in the photo evidence log or the compensation workflow log
  vision    - the vision model answers on a demo photo (not the rule-based fallback); --no-vision skips the API call
  photos    - the two demo photos are in place
Then prints the headline facts from the result files, so what is said matches what is on screen.
"""
import json
import sys
import urllib.request
from datetime import datetime
from pathlib import Path

import numpy as np

POC = Path(__file__).resolve().parent
D = POC / "data" / "derived"
BACK = POC.parent / "ap-cropguard-backend"
BASE = "http://127.0.0.1:8010"
sys.stdout.reconfigure(encoding="utf-8")
bad = []


def say(level, what, detail=""):
    print(f"  {level:4s}  {what}{': ' + detail if detail else ''}")
    if level != "OK":
        bad.append((level, what))


def get(path):
    with urllib.request.urlopen(BASE + path, timeout=90) as r:
        return r.status, r.read()


def js(name):
    p = D / name
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def wilson(h, n, z=1.96):
    p = h / n
    d = 1 + z * z / n
    c, w = (p + z * z / (2 * n)) / d, z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return c - w, c + w


print("== backend")
for path, what in [("/poc/", "dashboard"), ("/poc/capture.html", "phone capture page"),
                   ("/api/v1/poc/compensation", "compensation workflow"), ("/api/v1/poc/photo/events", "photo events"),
                   ("/api/v1/poc/farmer/villages?mandal=Gurazala&year=2023", "farmer look-up")]:
    try:
        st, body = get(path)
        say("OK" if st == 200 else "FAIL", what, f"HTTP {st}, {len(body) // 1024} KB")
    except Exception as e:
        say("FAIL", what, f"{type(e).__name__}: {e} (start the poc-backend, wait a minute, re-run)")

print("== freshness (each output newer than its inputs)")
chain = [("farmer_payouts.parquet", ["live_event_mandals.csv"]),
         ("compensation.json", ["farmer_payouts.parquet", "live_event_mandals.csv", "loss_calibration.json"]),
         ("alerts.csv", ["live_event_mandals.csv"]),
         ("../dashboard/index.html", ["live_event_arnab.json", "compensation.json", "alerts.csv", "farmer_payouts_summary.json"])]
for out, ins in chain:
    o = D / out
    if not o.exists():
        say("FAIL", out, "missing")
        continue
    stale = [i for i in ins if (D / i).exists() and (D / i).stat().st_mtime > o.stat().st_mtime]
    say("WARN" if stale else "OK", out, ("older than " + ", ".join(stale) + ": re-run the refresh in order") if stale
        else datetime.fromtimestamp(o.stat().st_mtime).strftime("built %d %b %H:%M"))

print("== logs (rehearsal entries must be removed before the demo)")
ev = POC / "data" / "photo_evidence.jsonl"
n_ev = len([x for x in ev.read_text(encoding="utf-8").splitlines() if x.strip()]) if ev.exists() else 0
say("OK" if n_ev <= 2 else "WARN", "photo evidence log", f"{n_ev} entries" + ("" if n_ev <= 2 else ": remove rehearsal uploads"))
cl = POC / "data" / "compensation_log.jsonl"
say("WARN" if cl.exists() else "OK", "compensation workflow log",
    "exists: delete poc/data/compensation_log.jsonl to start clean" if cl.exists() else "empty")

print("== demo photos")
for f in ["1_clear_paddy_brown_plant_hopper.jpg", "2_blurry_shaken.jpg"]:
    say("OK" if (POC / "data" / "demo_photos" / f).exists() else "FAIL", f)

print("== vision model")
if "--no-vision" in sys.argv:
    say("WARN", "vision", "skipped (--no-vision)")
else:
    try:
        sys.path.insert(0, str(BACK))
        import os
        os.chdir(BACK)  # photo_engine loads .env from the working directory
        from engines.photo_engine import assess_photo
        img = (POC / "data" / "demo_photos" / "1_clear_paddy_brown_plant_hopper.jpg").read_bytes()
        reads = [assess_photo(img, "") for _ in range(3)]  # the model is not deterministic: the demo photo must read as paddy every time
        srcs = [str(r.get("analysis_source")) for r in reads]
        crops = [str(r.get("crop_identified")) for r in reads]
        down = any("fallback" in x.lower() for x in srcs)
        paddy = sum(("paddy" in c.lower() or "rice" in c.lower()) for c in crops)
        say("FAIL" if down or paddy < 3 else "OK", "vision (demo photo, 3 reads)", f"{srcs[0]} · crops {crops} · {reads[0].get('damage_class')}"
            + (" (no internet or key: photos will read VISION UNAVAILABLE, FIELD VISIT; pest model still runs offline)" if down
               else "" if paddy == 3 else " (not read as paddy every time: crop match may fail live)"))
    except Exception as e:
        say("FAIL", "vision", f"{type(e).__name__}: {e}")

print("\n== headline facts (say these, they are what the screens show)")
L = js("live_event_arnab.json")
if L:
    c, rows = L["counts"], L["rows"]
    radar = [r for r in rows if r.get("radar_mapped")]
    h = min(r["hours_after_landfall"] for r in radar) if radar else None
    print(f"  {L['event']['name']}: rain index {'ERA5 (final)' if L['era5_complete'] else 'PROVISIONAL (ERA5 published to ' + L['era5_published_to'] + ')'}; "
          f"{c['enumeration']} mandals relief enumeration ({c['standing_acres_enumeration']:,.0f} standing acres); "
          f"{c['rain_side']} above the rainfall trigger; {c['index_payout']} index payouts; first radar T+{h:.0f} h" if h else "no radar yet")
C = js("compensation.json")
if C:
    t = C["lane2"]["totals"]
    print(f"  Relief budget: {t['cases']} cases, Rs {t['budget_rs'][1] / 1e7:.1f}-{t['budget_rs'][2] / 1e7:.1f} cr "
          f"(CI {t['budget_rs'][0] / 1e7:.1f}-{t['budget_rs'][3] / 1e7:.1f}); share >=33% {C['calibration']['share_33']:.0%}")
    for b in C["lane1_batches"]:
        print(f"  Settlement batch {b['batch_id']}: {b['lines']:,} lines, {b['si_acres']:,.0f} sum-insured acres")
V = js("dual_trigger_validation.json")
if V:
    for test in ["Season cover, rainfall only (WBCIS structure)", "Lane 1 product: both covers, dual-triggered"]:
        r = next((x for x in V["rows"] if x["test"] == test and x["crop"] == "All" and x["indemnity"] == 80), None)
        if r and r["fired"]:
            lo, hi = wilson(r["hits"], r["fired"])
            print(f"  CCE (YSR, 80% indemnity) {test}: {r['fired']} payouts, {r['hits']} real ({r['hits'] / r['fired']:.0%}, "
                  f"CI {lo:.0%}-{hi:.0%}), catches {r['hits'] / r['losses']:.0%} of {r['losses']} losses")
P = POC / "data" / "pest_model" / "metrics.json"
if P.exists():
    m = json.loads(P.read_text(encoding="utf-8"))
    acc = m.get("test_accuracy") or m.get("accuracy")
    if acc:
        print(f"  Pest model held-out accuracy: {acc:.0%}")
for f in ["SAR_DEPTH_RESULTS.md", "CYCLONE_TEST_2026.md", "ARNAB_PREREGISTRATION.md"]:
    if (POC / f).exists():
        print(f"  See poc/{f}")

print(f"\n{'ALL CLEAR' if not bad else str(len(bad)) + ' item(s) to fix: ' + '; '.join(w for _, w in bad)}")
