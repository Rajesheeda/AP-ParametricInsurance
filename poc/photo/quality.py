"""Photo quality gate for Module B: reject blurred, dark, washed-out or low-resolution photos before any check.

Measures (each on the photo resized to 1024 px on the long side, so values do not depend on the camera):
  sharpness  : variance of the Laplacian of the grey image (Pech-Pacheco et al. 2000, the standard focus measure)
  brightness : mean grey level (0-255)
  clipped    : share of pixels that are near-black (<5) or near-white (>250)
  min_side   : shorter side of the original photo, in pixels
Thresholds are NOT chosen by hand. They are percentiles of the same measures on the Department's own labelled
field photos (Label Studio sample, poc/data/pest_train + pest_benchmark): a photo is rejected if it is blurrier
than the 5th percentile, darker / brighter than the 1st / 99th percentile, more clipped than the 99th
percentile, or smaller than the 1st percentile of those photos.

Usage: py -3.13 quality.py calibrate   writes data/photo_quality.json and a held-out test on degraded copies
"""
import glob
import json
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter

POC = Path(__file__).resolve().parent.parent
CAL = POC / "data" / "photo_quality.json"
_T = None


def measure(img):
    w, h = img.size
    s = 1024 / max(w, h)
    g = np.asarray(img.convert("L").resize((max(1, round(w * s)), max(1, round(h * s))), Image.BILINEAR))
    return dict(sharpness=float(cv2.Laplacian(g, cv2.CV_64F).var()), brightness=float(g.mean()),
                clipped=float(((g < 5) | (g > 250)).mean()), min_side=int(min(w, h)))


def thresholds(ms):
    a = {k: np.array([m[k] for m in ms]) for k in ms[0]}
    return dict(sharpness_min=float(np.percentile(a["sharpness"], 5)),
                brightness_min=float(np.percentile(a["brightness"], 1)),
                brightness_max=float(np.percentile(a["brightness"], 99)),
                clipped_max=float(np.percentile(a["clipped"], 99)),
                min_side=int(np.percentile(a["min_side"], 1)))


def failures(m, t):
    out = []
    if m["sharpness"] < t["sharpness_min"]:
        out.append(f"blurred (sharpness {m['sharpness']:.0f} < {t['sharpness_min']:.0f})")
    if m["brightness"] < t["brightness_min"]:
        out.append(f"too dark (brightness {m['brightness']:.0f} < {t['brightness_min']:.0f})")
    if m["brightness"] > t["brightness_max"]:
        out.append(f"overexposed (brightness {m['brightness']:.0f} > {t['brightness_max']:.0f})")
    if m["clipped"] > t["clipped_max"]:
        out.append(f"{m['clipped']:.0%} of pixels black/white (> {t['clipped_max']:.0%})")
    if m["min_side"] < t["min_side"]:
        out.append(f"low resolution ({m['min_side']} px < {t['min_side']} px)")
    return out


def check(img):
    """dict(ok, detail, measures) for a PIL image, using the calibrated thresholds."""
    global _T
    if _T is None:
        _T = json.loads(CAL.read_text(encoding="utf-8"))["thresholds"] if CAL.exists() else None
    m = measure(img)
    if _T is None:
        return dict(ok=None, detail="quality gate not calibrated", measures=m)
    f = failures(m, _T)
    return dict(ok=not f, detail="; ".join(f) if f else f"sharp, well exposed ({m['min_side']} px)", measures=m)


def degrade(img, kind):
    if kind == "blur_r2":
        return img.filter(ImageFilter.GaussianBlur(2 * max(img.size) / 1024))
    if kind == "blur_r4":
        return img.filter(ImageFilter.GaussianBlur(4 * max(img.size) / 1024))
    if kind == "motion":
        k = np.zeros((15, 15)); k[7, :] = 1 / 15
        return Image.fromarray(cv2.filter2D(np.asarray(img), -1, cv2.resize(k, None, fx=max(img.size) / 1024, fy=max(img.size) / 1024)))
    if kind == "dark":
        return ImageEnhance.Brightness(img).enhance(0.25)
    if kind == "overexposed":
        return ImageEnhance.Brightness(img).enhance(2.5)
    if kind == "low_res":
        return img.resize((img.size[0] // 4, img.size[1] // 4))
    raise ValueError(kind)


if __name__ == "__main__" and sys.argv[1:] == ["calibrate"]:
    files = sorted(glob.glob(str(POC / "data" / "pest_train" / "*" / "*.jpg")) + glob.glob(str(POC / "data" / "pest_benchmark" / "*" / "*.jpg")))
    rng = np.random.default_rng(0)
    test = set(rng.choice(len(files), size=len(files) // 3, replace=False))
    imgs = {i: Image.open(f).convert("RGB") for i, f in enumerate(files)}
    ms = {i: measure(im) for i, im in imgs.items()}
    t = thresholds([ms[i] for i in ms if i not in test])
    res = {"genuine (held-out Department photos)": float(np.mean([not failures(ms[i], t) for i in test]))}
    kinds = ["blur_r2", "blur_r4", "motion", "dark", "overexposed", "low_res"]
    for k in kinds:
        res[f"{k} copies rejected"] = float(np.mean([bool(failures(measure(degrade(imgs[i], k)), t)) for i in test]))
    out = dict(thresholds=t, n_calibration=len(files) - len(test), n_test=len(test), test=res,
               source="Department Label Studio field photos (8 paddy/cotton classes), 2/3 calibration, 1/3 held-out")
    CAL.write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(json.dumps(out, indent=1))
