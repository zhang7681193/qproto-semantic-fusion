from __future__ import annotations

import argparse
import csv
import math
import re
import statistics as st
from pathlib import Path


T_CRIT_95 = {1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571}


GROUPS = [
    (r"drift_baseline_qiskit_aer_seed\d+$", "Qiskit Aer MNIST-4"),
    (r"drift_baseline_pennylane_highorder_seed\d+$", "PennyLane high-order"),
]


METHOD_ORDER = {
    "fedadam_schema": 0,
    "fedproto_schema": 1,
    "scaffold_schema": 2,
    "feddyn_schema": 3,
    "qproto_cproto": 4,
    "qproto_chop": 5,
    "qproto_masked_hop": 6,
}


METHOD_LABELS = {
    "fedadam_schema": "FedAdam schema",
    "fedproto_schema": "FedProto schema",
    "scaffold_schema": "SCAFFOLD schema",
    "feddyn_schema": "FedDyn schema",
    "qproto_cproto": "CProto",
    "qproto_chop": "CHOP",
    "qproto_masked_hop": "Masked-HOP",
}


def ci95(xs: list[float]) -> float:
    if len(xs) <= 1:
        return 0.0
    return T_CRIT_95.get(len(xs) - 1, 1.96) * st.stdev(xs) / math.sqrt(len(xs))


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def infer_group(run: str) -> str | None:
    for pattern, group in GROUPS:
        if re.match(pattern, run):
            return group
    return None


def main() -> None:
    ap = argparse.ArgumentParser("Summarize drift-control FL baselines")
    ap.add_argument("--summary", type=str, default="runs/summary.csv")
    ap.add_argument("--out", type=str, default="runs/drift_baseline_report.csv")
    ap.add_argument("--md", type=str, default="runs/drift_baseline_report.md")
    args = ap.parse_args()

    groups: dict[tuple[str, str], list[dict[str, str]]] = {}
    for row in read_rows(Path(args.summary)):
        group = infer_group(str(row["run"]))
        method = str(row["method"])
        if group is None or method not in METHOD_ORDER:
            continue
        groups.setdefault((group, method), []).append(row)

    out_rows = []
    for (group, method), vals in groups.items():
        acc = [float(v["final_acc"]) for v in vals]
        bal = [float(v["final_balanced_acc"]) for v in vals]
        bytes_ = [float(v["bytes_per_client_round"]) for v in vals]
        out_rows.append(
            {
                "group": group,
                "method": method,
                "n": len(vals),
                "acc_mean": st.mean(acc),
                "acc_ci95": ci95(acc),
                "balanced_acc_mean": st.mean(bal),
                "bytes_mean": st.mean(bytes_),
            }
        )

    out_rows.sort(key=lambda r: (str(r["group"]), METHOD_ORDER.get(str(r["method"]), 99)))
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    fields = ["group", "method", "n", "acc_mean", "acc_ci95", "balanced_acc_mean", "bytes_mean"]
    with out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(out_rows)

    lines = ["# Drift-Control Baseline Report", ""]
    for group in sorted({str(r["group"]) for r in out_rows}):
        lines.extend([f"## {group}", "", "| Method | n | Acc. | 95% CI | Bal. acc. | Bytes |", "|---|---:|---:|---:|---:|---:|"])
        for r in [x for x in out_rows if x["group"] == group]:
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

