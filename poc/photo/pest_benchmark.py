"""Benchmark the vision models on the Department's labelled pest/disease images (post-flood classes).

Each image goes to each model blind (no crop or label named). Scored against the Label Studio label:
  crop_ok     - crop identified as the labelled crop
  detected    - model reports any pest/disease
  named_ok    - model's pest/disease name matches the label (keyword list per class, written before scoring)
Wilson 95% intervals; n = 30 per class. Results: poc/data/pest_benchmark/results.csv
"""
import json
import math
import sys
import time
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "ap-cropguard-backend"))
from engines.photo_engine import assess_with_gemini, assess_with_groq  # noqa: E402

DIR = ROOT / "poc" / "data" / "pest_benchmark"
BLIND = "Unknown (identify it from the photo)"
CROP_KEYS = {"Paddy": ["paddy", "rice"], "Cotton": ["cotton"]}
NAME_KEYS = {
    "paddy_bacterial_leaf_blight": ["bacterial leaf blight", "bacterial blight", "blb", "xanthomonas"],
    "paddy_sheath_blight": ["sheath blight", "rhizoctonia"],
    "paddy_blast": ["blast", "pyricularia", "magnaporthe"],
    "paddy_brown_spot": ["brown spot", "helminthosporium", "bipolaris", "cochliobolus"],
    "paddy_false_smut": ["false smut", "ustilaginoidea"],
    "paddy_brown_plant_hopper": ["brown plant hopper", "brown planthopper", "bph", "nilaparvata", "hopper burn", "hopperburn", "planthopper"],
    "cotton_bacterial_blight": ["bacterial blight", "black arm", "angular leaf spot", "xanthomonas"],
    "cotton_alternaria_leaf_spot": ["alternaria"],
}
MODELS = {"gemini": assess_with_gemini, "groq": assess_with_groq}


def call(fn, b):
    for attempt in range(4):
        try:
            return fn(b, BLIND)
        except Exception as e:
            msg = str(e)
            print(f"   retry {attempt + 1}: {msg[:90]}", flush=True)
            if "429" in msg or "RESOURCE_EXHAUSTED" in msg or "rate" in msg.lower():
                time.sleep(15 * (attempt + 1))
                continue
            return {"error": msg[:120]}
    return {"error": "rate limited"}


def wilson(k, n):
    if n == 0:
        return (math.nan, math.nan)
    z, p = 1.96, k / n
    c = (p + z * z / (2 * n)) / (1 + z * z / n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return (c - h, c + h)


man = json.loads((DIR / "labels.json").read_text(encoding="utf-8"))
out_f = DIR / "results.csv"
done = pd.read_csv(out_f) if out_f.exists() else pd.DataFrame(columns=["file", "model"])
seen = set(zip(done.file, done.model))
rows = done.to_dict("records")
for i, m in enumerate(man):
    b = (DIR / m["file"]).read_bytes()
    for name, fn in MODELS.items():
        if (m["file"], name) in seen:
            continue
        t0 = time.time()
        r = call(fn, b)
        print(f"{i + 1:3d} {name:6s} {time.time() - t0:5.1f}s {m['cls']:28s} -> {str(r.get('crop_identified'))[:20]:20s} "
              f"{[d.get('name') for d in r.get('disease_details', []) if isinstance(d, dict)]}", flush=True)
        text = " ".join([str(r.get("crop_identified", "")), json.dumps(r.get("disease_details", [])),
                         str(r.get("analysis_notes", ""))]).lower()
        names = " ".join([json.dumps(r.get("disease_details", [])), str(r.get("analysis_notes", ""))]).lower()
        rows.append(dict(file=m["file"], cls=m["cls"], crop=m["crop"], model=name, error=r.get("error"),
                         crop_seen=r.get("crop_identified"), damage=r.get("damage_class"),
                         detected=bool(r.get("disease_pest_detected")),
                         named=json.dumps([d.get("name") for d in r.get("disease_details", []) if isinstance(d, dict)]),
                         crop_ok=any(k in str(r.get("crop_identified", "")).lower() for k in CROP_KEYS[m["crop"]]),
                         named_ok=any(k in names for k in NAME_KEYS[m["cls"]])))
        time.sleep(2)
    if i % 10 == 9:
        pd.DataFrame(rows).to_csv(out_f, index=False)
        print(f"{i + 1}/{len(man)}", flush=True)
res = pd.DataFrame(rows)
res.to_csv(out_f, index=False)

ok = res[res.error.isna()]
print("\nerrors by model:", res[res.error.notna()].groupby("model").size().to_dict())
for model, g in ok.groupby("model"):
    print(f"\n=== {model}  (n={len(g)})")
    tab = g.groupby("cls").agg(n=("file", "size"), crop_ok=("crop_ok", "mean"), detected=("detected", "mean"), named_ok=("named_ok", "mean"))
    print(tab.round(2).to_string())
    for col in ["crop_ok", "detected", "named_ok"]:
        k, n = int(g[col].sum()), len(g)
        lo, hi = wilson(k, n)
        print(f"  overall {col}: {k}/{n} = {k / n:.0%}  (95% CI {lo:.0%}-{hi:.0%})")
