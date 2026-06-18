from __future__ import annotations

import csv
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "latex_qproto_hop_IF" / "tables" / "table_adaptive_chop_ablation.tex"

DATASETS = [
    ("UCI HAR", ROOT / "runs" / "if_nonquantum_sensor_fusion.csv"),
    ("MFeat", ROOT / "runs" / "if_mfeat_fusion.csv"),
    ("PAMAP2", ROOT / "runs" / "if_pamap2_fusion.csv"),
    ("MHEALTH", ROOT / "runs" / "if_mhealth_fusion.csv"),
]

METHODS = [
    ("Zero-fill RFF", "zero_fill_rff_equal_bytes"),
    ("CProto", "cproto_equal_bytes"),
    ("Random HOP", "random_key_hop_equal_bytes"),
    ("CHOP", "chop_equal_bytes"),
    ("Adaptive CHOP", "adaptive_chop_equal_bytes"),
]


def mean_acc(path: Path) -> dict[str, float]:
    vals: dict[str, list[float]] = {}
    with path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            vals.setdefault(row["method"], []).append(float(row["final_acc"]))
    return {k: float(np.mean(v)) for k, v in vals.items()}


def main() -> None:
    lines = [
        "\\begin{table*}[t]",
        "\\centering",
        "\\caption{Adaptive CHOP ablation under matched communication. All method columns use the same per-client payload within each dataset. The table separates low-order coverage fusion, random high-order sketches, protocol-selected CHOP, and the train-calibrated mixture/fallback gate.}",
        "\\label{tab:adaptive-chop-ablation}",
        "\\resizebox{\\textwidth}{!}{%",
        "\\begin{tabular}{lccccc}",
        "\\toprule",
        "Dataset & Zero-fill RFF & CProto & Random HOP & CHOP & Adaptive CHOP \\\\",
        "\\midrule",
    ]
    for name, path in DATASETS:
        acc = mean_acc(path)
        cells = [f"{acc[key]:.3f}" for _, key in METHODS]
        lines.append(f"{name} & " + " & ".join(cells) + " \\\\")
    lines.extend(["\\bottomrule", "\\end{tabular}%", "}", "\\end{table*}", ""])
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()

