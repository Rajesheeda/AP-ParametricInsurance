"""Sample labelled pest/disease images from the Department's Label Studio for a vision benchmark.

Read-only: uses the task list API (no exports are created). URL, key and the MinIO helper are imported
from the Department's own script at runtime, so the key is never copied into this repo.
Output (gitignored): poc/data/pest_benchmark/<class>/<task_id>.jpg + labels.json
"""
import base64
import os
import json
import random
import sys
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from PIL import Image

sys.path.insert(0, r"C:\AP-Agri-Common\data\LabelStudio")
import batch_export_yolo_obb_and_clean as B  # noqa: E402
from label_studio_sdk._extensions.label_studio_tools.core.utils.io import get_local_path  # noqa: E402
from label_studio_sdk.client import LabelStudio  # noqa: E402

import argparse

ap = argparse.ArgumentParser()
ap.add_argument("--out", default="pest_benchmark", help="folder under poc/data")
ap.add_argument("--per-class", type=int, default=30)
ap.add_argument("--exclude", default=None, help="labels.json whose task ids must not be reused (held-out test set)")
ARGS = ap.parse_args()
OUT = Path(__file__).resolve().parent.parent / "data" / ARGS.out
PER_CLASS = ARGS.per_class
SEED = 7
EXCLUDE = ({m["task_id"] for m in json.loads(Path(ARGS.exclude).read_text(encoding="utf-8"))} if ARGS.exclude else set())
# Post-flood / excess-moisture pests and diseases of the pilot crops (paddy, cotton)
CLASSES = [
    (181, "paddy_bacterial_leaf_blight", "Paddy"),
    (133, "paddy_sheath_blight", "Paddy"),
    (125, "paddy_blast", "Paddy"),
    (120, "paddy_brown_spot", "Paddy"),
    (178, "paddy_false_smut", "Paddy"),
    (113, "paddy_brown_plant_hopper", "Paddy"),  # project 44 uses an older link format
    (156, "cotton_bacterial_blight", "Cotton"),
    (151, "cotton_alternaria_leaf_spot", "Cotton"),
]


def labels_of(task):
    out = set()
    for a in task.annotations or []:
        res = a.get("result", []) if isinstance(a, dict) else a.result
        for r in res:
            v = r.get("value", {})
            out.update(v.get("rectanglelabels") or v.get("labels") or v.get("polygonlabels") or [])
    return sorted(out)


def s3_of(task):
    u = next(iter(task.data.values()))
    if str(u).startswith("s3://"):
        return u
    f = parse_qs(urlparse(u).query)["fileuri"][0].replace(" ", "+")
    f += "=" * (-len(f) % 4)
    # some projects use URL-safe base64 ("-", "_")
    return (base64.urlsafe_b64decode(f) if ("-" in f or "_" in f) else base64.b64decode(f)).decode()


ls = LabelStudio(base_url=B.LABEL_STUDIO_URL, api_key=B.LABEL_STUDIO_API_KEY)
manifest = []
for pid, name, crop in CLASSES:
    pool = [t for t in ls.tasks.list(project=pid, fields="all", page_size=100) if labels_of(t) and t.id not in EXCLUDE]
    random.Random(SEED).shuffle(pool)
    d = OUT / name
    d.mkdir(parents=True, exist_ok=True)
    got = 0
    for t in pool:
        if got >= PER_CLASS:
            break
        dst = d / f"{t.id}.jpg"
        try:
            if not dst.exists():
                url, _ = B.s3_to_minio_http(s3_of(t))
                p = get_local_path(url=url, hostname=B.LABEL_STUDIO_URL, access_token=B.LABEL_STUDIO_API_KEY,
                                   task_id=t.id, download_resources=True)
                im = Image.open(p).convert("RGB")
                im.thumbnail((1600, 1600))
                im.save(dst, "JPEG", quality=88)
                im.close()
                try:
                    os.remove(p)  # the SDK caches full-size originals; they filled the disk once
                except OSError:
                    pass
            manifest.append(dict(file=str(dst.relative_to(OUT)), task_id=t.id, project_id=pid, cls=name, crop=crop,
                                 labels=labels_of(t)))
            got += 1
        except Exception as e:
            print("skip", t.id, str(e)[:80], flush=True)
    print(f"{name}: {got} images (pool of {len(pool)} labelled)", flush=True)
(OUT / "labels.json").write_text(json.dumps(manifest, indent=1), encoding="utf-8")
print("total", len(manifest))
