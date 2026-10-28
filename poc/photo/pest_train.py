"""Train and test a pest / disease classifier on the Department's labelled images.

Declared before training (2026-10-27):
  Test set : the 240 benchmark images (pest_benchmark/, 8 classes x 30) that Gemini was scored on, so the
             comparison is like for like. Never used for training or tuning.
  Train set: up to 200 further labelled images per class (pest_train/), task ids disjoint from the test set.
             Near-duplicates of any test image (16x16 average-hash Hamming distance <= 6) are removed from
             training, and duplicates inside the training set are collapsed.
  Model    : ImageNet-pretrained EfficientNet-B0 (torchvision) as a frozen feature extractor at 320 px,
             multinomial logistic regression on the 1280-d features; C chosen by 5-fold CV on training only.
  Report   : test accuracy with Wilson 95% CI, per-class accuracy, confusion matrix, Gemini on the same images.
Outputs (gitignored): poc/data/pest_model/{model.joblib, metrics.json}
"""
import json
import math
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import torch
from PIL import Image
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GridSearchCV, StratifiedKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from torchvision import models, transforms

DATA = Path(__file__).resolve().parents[1] / "data"
TEST, TRAIN, OUT = DATA / "pest_benchmark", DATA / "pest_train", DATA / "pest_model"
OUT.mkdir(exist_ok=True)
torch.set_num_threads(4)


def ahash(path):
    im = Image.open(path).convert("L").resize((16, 16))
    a = np.asarray(im, dtype=np.float32)
    return (a > a.mean()).flatten()


def wilson(k, n, z=1.96):
    p = k / n
    c = (p + z * z / (2 * n)) / (1 + z * z / n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return c - h, c + h


test = pd.DataFrame(json.loads((TEST / "labels.json").read_text(encoding="utf-8")))
test["path"] = test.file.map(lambda f: TEST / f)
train = pd.DataFrame(json.loads((TRAIN / "labels.json").read_text(encoding="utf-8")))
train["path"] = train.file.map(lambda f: TRAIN / f)
assert not set(train.task_id) & set(test.task_id), "train/test task overlap"

th = np.stack([ahash(p) for p in test.path])
keep, seen = [], []
for p in train.path:
    h = ahash(p)
    if (np.count_nonzero(th != h, axis=1) <= 6).any():
        keep.append(False)
        continue
    if seen and (np.count_nonzero(np.stack(seen) != h, axis=1) <= 6).any():
        keep.append(False)
        continue
    seen.append(h)
    keep.append(True)
removed = int((~np.array(keep)).sum())
train = train[keep].reset_index(drop=True)
print(f"train {len(train)} images after removing {removed} near-duplicates; test {len(test)}")
print("train per class:", train.cls.value_counts().to_dict())

weights = models.EfficientNet_B0_Weights.DEFAULT
net = models.efficientnet_b0(weights=weights)
net.classifier = torch.nn.Identity()
net.eval()
tf = transforms.Compose([transforms.Resize(320), transforms.CenterCrop(320), transforms.ToTensor(),
                         transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])])


@torch.no_grad()
def embed(paths, bs=16):
    out = []
    for i in range(0, len(paths), bs):
        x = torch.stack([tf(Image.open(p).convert("RGB")) for p in paths[i:i + bs]])
        out.append(net(x).numpy())
        if i % 320 == 0:
            print(f"  embedded {i}/{len(paths)}", flush=True)
    return np.concatenate(out)


Xtr, Xte = embed(list(train.path)), embed(list(test.path))
clf = GridSearchCV(make_pipeline(StandardScaler(), LogisticRegression(max_iter=3000)),
                   {"logisticregression__C": [0.01, 0.03, 0.1, 0.3, 1.0]},
                   cv=StratifiedKFold(5, shuffle=True, random_state=0), scoring="accuracy")
clf.fit(Xtr, train.cls)
pred = clf.predict(Xte)
test["pred"] = pred
k, n = int((pred == test.cls).sum()), len(test)
lo, hi = wilson(k, n)
print(f"\nchosen C={clf.best_params_['logisticregression__C']}  CV accuracy on train {clf.best_score_:.0%}")
print(f"TEST accuracy (held out): {k}/{n} = {k / n:.0%}  (95% CI {lo:.0%}-{hi:.0%})")
per = test.assign(ok=test.pred == test.cls).groupby("cls").ok.mean()
print(per.round(2).to_string())
cm = pd.crosstab(test.cls, test.pred)
print("\nconfusion (rows = true):\n", cm.to_string())

g = pd.read_csv(TEST / "results.csv")
g = g[(g.model == "gemini") & g.error.isna()]
both = test.merge(g[["file", "named_ok"]], on="file")
print(f"\nsame images, Gemini named correctly {both.named_ok.mean():.0%} vs trained model {(both.pred == both.cls).mean():.0%} (n={len(both)})")

joblib.dump({"clf": clf.best_estimator_, "classes": list(clf.classes_)}, OUT / "model.joblib")
(OUT / "metrics.json").write_text(json.dumps(dict(
    n_train=len(train), removed_near_duplicates=removed, n_test=n, test_accuracy=k / n, ci95=[lo, hi],
    cv_accuracy=clf.best_score_, C=clf.best_params_["logisticregression__C"], per_class=per.to_dict(),
    confusion=cm.to_dict(), gemini_same_images=float(both.named_ok.mean()),
    model_same_images=float((both.pred == both.cls).mean()), n_compare=len(both)), indent=1), encoding="utf-8")
print("saved", OUT)
