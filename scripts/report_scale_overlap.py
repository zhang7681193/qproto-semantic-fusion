from __future__ import annotations

import argparse
import csv
import math
import re
import statistics as st
from pathlib import Path


T_CRIT_95 = {1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571}

METHOD_ORDER = {
    "qproto_masked_hop": 0,
    "qproto_chop": 1,
    "qproto_cproto": 2,
    "fedadam_schema": 3,
    "fedavg_schema": 4,
    "fedproto_schema": 5,
    "shared_observable": 6,
    "no_schema": 7,
    "wrong_schema": 8,
}


def ci95(xs: list[float]) -> float:
    if len(xs) <= 1:
        return 0.0
    return T_CRIT_95.get(len(xs) - 1, 1.96) * st.stdev(xs) / math.sqrt(len(xs))


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def infer_sweep(run: str) -> tuple[str, str, float] | None:
    m = re.match(r"scale_mnist10_c(\d+)_seed\d+$", run)
    if m:
        return ("MNIST-10 clients", "clients", float(m.group(1)))
    m = re.match(r"scale_fashion10_c(\d+)_seed\d+$", run)
    if m:
        return ("Fashion-10 clients", "clients", float(m.group(1)))
    m = re.match(r"scale_cifar10_c(\d+)_seed\d+$", run)
    if m:
        return ("CIFAR-10 clients", "clients", float(m.group(1)))
    m = re.match(r"overlap_mnist10_o([0-9p]+)_seed\d+$", run)
    if m:
        return ("MNIST-10 overlap", "overlap", float(m.group(1).replace("p", ".")))
    m = re.match(r"overlap_fashion10_o([0-9p]+)_seed\d+$", run)
    if m:
        return ("Fashion-10 overlap", "overlap", float(m.group(1).replace("p", ".")))
    m = re.match(r"overlap_cifar10_o([0-9p]+)_seed\d+$", run)
    if m:
        return ("CIFAR-10 overlap", "overlap", float(m.group(1).replace("p", ".")))
    m = re.match(r"overlap_pennylane_highorder_o([0-9p]+)_seed\d+$", run)
    if m:
        return ("PennyLane high-order overlap", "overlap", float(m.group(1).replace("p", ".")))
    return None


def main() -> None:
    ap = argparse.ArgumentParser("Summarize scale and observable-overlap sweeps")
    ap.add_argument("--summary", type=str, default="runs/summary.csv")
    ap.add_argument("--out", type=str, default="runs/scale_overlap_report.csv")
    ap.add_argument("--md", type=str, default="runs/scale_overlap_report.md")
    args = ap.parse_args()

    groups: dict[tuple[str, str, float, str], list[dict[str, str]]] = {}
    for r in read_rows(Path(args.summary)):
        inferred = infer_sweep(r["run"])
        if inferred is None:
            continue
        setting, axis, value = inferred
        groups.setdefault((setting, axis, value, r["method"]), []).append(r)

    out_rows = []
    for (setting, axis, value, method), vals in groups.items():
        acc = [float(v["final_acc"]) for v in vals]
        bal = [float(v["final_balanced_acc"]) for v in vals]
        bytes_ = [float(v["bytes_per_client_round"]) for v in vals]
        out_rows.append(
            {
                "setting": setting,
                "axis": axis,
                "value": value,
                "method": method,
                "n": len(vals),
                "acc_mean": st.mean(acc),
                "acc_ci95": ci95(acc),
                "balanced_acc_mean": st.mean(bal),
                "bytes_mean": st.mean(bytes_),
            }
        )
    out_rows.sort(key=lambda r: (str(r["setting"]), float(r["value"]), METHOD_ORDER.get(str(r["method"]), 99)))

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as f:
        fields = ["setting", "axis", "value", "method", "n", "acc_mean", "acc_ci95", "balanced_acc_mean", "bytes_mean"]
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(out_rows)

    lines = ["# Scale and Observable-Overlap Report", ""]
    for setting in sorted({str(r["setting"]) for r in out_rows}):
        lines.extend([f"## {setting}", ""])
        values = sorted({float(r["value"]) for r in out_rows if r["setting"] == setting})
        for value in values:
            axis = next(str(r["axis"]) for r in out_rows if r["setting"] == setting and float(r["value"]) == value)
            label = f"{axis}={int(value) if axis == 'clients' else value:.2f}" if axis != "clients" else f"{axis}={int(value)}"
            lines.extend([f"### {label}", "", "| Method | n | Acc. | 95% CI | Bal. acc. | Bytes |", "|---|---:|---:|---:|---:|---:|"])
            for r in [x for x in out_rows if x["setting"] == setting and float(x["value"]) == value]:
                lines.append(
                    f"| {r['method']} | {r['n']} | {float(r['acc_mean']):.4f} | "
                    f"{float(r['acc_ci95']):.4f} | {float(r['balanced_acc_mean']):.4f} | {float(r['bytes_mean']):.0f} |"
                )
            lines.append("")
    Path(args.md).write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {out} and {args.md}")


if __name__ == "__main__":
    main()

