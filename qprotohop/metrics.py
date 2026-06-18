from __future__ import annotations

import json
from pathlib import Path
import numpy as np


def accuracy(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    return float(np.mean(np.asarray(y_true) == np.asarray(y_pred)))


def balanced_accuracy(y_true: np.ndarray, y_pred: np.ndarray, n_classes: int) -> float:
    vals = []
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)
    for c in range(n_classes):
        mask = y_true == c
        if np.any(mask):
            vals.append(np.mean(y_pred[mask] == c))
    return float(np.mean(vals)) if vals else 0.0


def nll_from_logits(logits: np.ndarray, y: np.ndarray) -> float:
    logits = logits - logits.max(axis=1, keepdims=True)
    log_probs = logits - np.log(np.exp(logits).sum(axis=1, keepdims=True) + 1e-12)
    return float(-np.mean(log_probs[np.arange(len(y)), y]))


def save_json(path: str | Path, obj: object) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2), encoding="utf-8")


def append_jsonl(path: str | Path, obj: object) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(obj) + "\n")


