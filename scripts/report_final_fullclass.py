from __future__ import annotations

import argparse
import csv
import math
import re
import statistics as st
from pathlib import Path


T_CRIT_95 = {1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571}

DATASET_LABELS = {
    "mnist10": "MNIST-10",
    "fashion10": "Fashion-10",
    "cifar10": "CIFAR-10",
}

METHOD_ORDER = {
    "qproto_masked_hop": 0,
    "qproto_masked": 1,
    "qproto_chop": 2,
    "qproto_cproto": 3,
    "shared_observable": 4,
    "fedproto_schema": 5,
    "fedadam_schema": 6,
    "scaffold_schema": 7,
    "feddyn_schema": 8,
    "fedavg_schema": 9,
    "fedprox_schema": 10,
    "fedproto_forced": 11,
    "fedadam_forced": 12,
    "fedavg_forced": 13,
    "fedprox_forced": 14,
    "no_schema": 15,
    "wrong_schema": 16,
}

METHOD_LABELS = {
    "qproto_masked_hop": "Masked-HOP",
    "qproto_masked": "Masked",
    "qproto_chop": "CHOP",
    "qproto_cproto": "CProto",
    "shared_observable": "Shared",
    "fedproto_schema": "FedProto schema",
    "fedadam_schema": "FedAdam schema",
    "scaffold_schema": "SCAFFOLD schema",
    "feddyn_schema": "FedDyn schema",
    "fedavg_schema": "FedAvg schema",
    "fedprox_schema": "FedProx schema",
    "fedproto_forced": "FedProto forced",
    "fedadam_forced": "FedAdam forced",
    "fedavg_forced": "FedAvg forced",
    "fedprox_forced": "FedProx forced",
    "no_schema": "No schema",
    "wrong_schema": "Wrong schema",
}


def ci95(xs: list[float]) -> float:
    if len(xs) <= 1:
        return 0.0
    return T_CRIT_95.get(len(xs) - 1, 1.96) * st.stdev(xs) / math.sqrt(len(xs))


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main() -> None:
    ap = argparse.ArgumentParser("Summarize final 5-seed full-class runs")
    ap.add_argument("--summary", type=str, default="runs/summary.csv")
    ap.add_argument("--out", type=str, default="runs/final_fullclass_report.csv")
    ap.add_argument("--md", type=str, default="runs/final_fullclass_report.md")
    args = ap.parse_args()

    grouped: dict[tuple[str, str], list[dict[str, str]]] = {}
    for row in read_rows(Path(args.summary)):
        m = re.match(r"final_fullclass_(mnist10|fashion10|cifar10)_seed\d+$", str(row["run"]))
        if not m:
            continue
        method = str(row["method"])
        if method not in METHOD_ORDER:
            continue
        grouped.setdefault((m.group(1), method), []).append(row)

    out_rows = []
    for (dataset, method), vals in grouped.items():
        acc = [float(v["final_acc"]) for v in vals]
        bal = [float(v["final_balanced_acc"]) for v in vals]
        bytes_ = [float(v["bytes_per_client_round"]) for v in vals]
        out_rows.append(
            {
                "dataset": DATASET_LABELS[dataset],
                "method": method,
                "n": len(vals),
                "acc_mean": st.mean(acc),
                "acc_ci95": ci95(acc),
                "balanced_acc_mean": st.mean(bal),
                "bytes_mean": st.mean(bytes_),
            }
        )
    out_rows.sort(key=lambda r: (str(r["dataset"]), METHOD_ORDER.get(str(r["method"]), 99)))

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    fields = ["dataset", "method", "n", "acc_mean", "acc_ci95", "balanced_acc_mean", "bytes_mean"]
    with out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(out_rows)

    lines = ["# Final Full-Class 5-Seed Report", ""]
    for dataset in sorted({str(r["dataset"]) for r in out_rows}):
        lines.extend([f"## {dataset}", "", "| Method | n | Acc. | 95% CI | Bal. acc. | Bytes |", "|---|---:|---:|---:|---:|---:|"])
        for r in [x for x in out_rows if x["dataset"] == dataset]:
            lines.append(
                f"| {METHOD_LABELS.get(str(r['method']), str(r['method']))} | {r['n']} | "
                f"{float(r['acc_mean']):.4f} | {float(r['acc_ci95']):.4f} | "
                f"{float(r['balanced_acc_mean']):.4f} | {float(r['bytes_mean']):.0f} |"
            )
        lines.append("")
    Path(args.md).write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {out} and {args.md}")


if __name__ == "__main__":
    main()

