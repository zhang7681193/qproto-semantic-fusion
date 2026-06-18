from __future__ import annotations

import csv
import math
import os
from collections import defaultdict
from pathlib import Path

_cache_dir = Path(__file__).resolve().parents[1] / ".mplconfig"
_cache_dir.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(_cache_dir))
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "latex_qproto_hop_IF" / "figures" / "adaptive_chop_summary.pdf"
OUT_PNG = ROOT / "latex_qproto_hop_IF" / "figures" / "adaptive_chop_summary.png"

DATASETS = [
    ("UCI HAR", "runs/if_nonquantum_sensor_fusion.csv"),
    ("MFeat", "runs/if_mfeat_fusion.csv"),
    ("PAMAP2", "runs/if_pamap2_fusion.csv"),
    ("MHEALTH", "runs/if_mhealth_fusion.csv"),
]

SERIES = [
    ("Zero-fill RFF", "zero_fill_rff_equal_bytes", "#9c6ade"),
    ("CProto", "cproto_equal_bytes", "#2a9d8f"),
    ("CHOP", "chop_equal_bytes", "#b75d69"),
    ("Adaptive CHOP", "adaptive_chop_equal_bytes", "#264653"),
]


def mean_ci(values: list[float]) -> tuple[float, float]:
    m = sum(values) / len(values)
    if len(values) < 2:
        return m, 0.0
    sd = math.sqrt(sum((v - m) ** 2 for v in values) / (len(values) - 1))
    return m, 1.96 * sd / math.sqrt(len(values))


def seed_means(path: str) -> dict[str, tuple[float, float]]:
    with (ROOT / path).open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    by_method: dict[str, list[float]] = defaultdict(list)
    for row in rows:
        by_method[row["method"]].append(float(row["final_acc"]))
    return {method: mean_ci(vals) for method, vals in by_method.items()}


def main() -> None:
    summaries = {name: seed_means(path) for name, path in DATASETS}
    fig, ax = plt.subplots(figsize=(8.6, 3.4))
    width = 0.18
    xs = list(range(len(DATASETS)))
    offsets = [(i - (len(SERIES) - 1) / 2) * width for i in range(len(SERIES))]
    for offset, (label, method, color) in zip(offsets, SERIES):
        vals = [summaries[name][method][0] for name, _ in DATASETS]
        errs = [summaries[name][method][1] for name, _ in DATASETS]
        ax.bar([x + offset for x in xs], vals, width=width, yerr=errs, capsize=2.5, label=label, color=color, edgecolor="white", linewidth=0.5)
    ax.set_xticks(xs)
    ax.set_xticklabels([name for name, _ in DATASETS], fontsize=9)
    ax.set_ylim(0.0, 1.02)
    ax.set_ylabel("Accuracy")
    ax.set_title("Adaptive high-order gate under matched communication", loc="left", fontsize=11, fontweight="bold")
    ax.grid(axis="y", alpha=0.2, linewidth=0.6)
    ax.legend(ncols=4, loc="upper center", bbox_to_anchor=(0.5, 1.18), frameon=False, fontsize=8)
    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)
    fig.tight_layout(pad=0.8)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT)
    fig.savefig(OUT_PNG, dpi=220)
    print(f"Wrote {OUT} and {OUT_PNG}")


if __name__ == "__main__":
    main()

