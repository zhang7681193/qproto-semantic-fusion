from __future__ import annotations

import argparse
import csv
import math
import re
import statistics as st
from pathlib import Path


T_CRIT_95 = {1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571, 6: 2.447, 7: 2.365, 8: 2.306, 9: 2.262, 10: 2.228}


def ci95(xs: list[float]) -> float:
    if len(xs) <= 1:
        return 0.0
    return T_CRIT_95.get(len(xs) - 1, 1.96) * st.stdev(xs) / math.sqrt(len(xs))


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, str | float | int]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0].keys()) if rows else []
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        if fields:
            writer.writeheader()
            writer.writerows(rows)


def summarize(rows: list[dict[str, str]]) -> list[dict[str, str | float | int]]:
    groups: dict[tuple[str, str], list[dict[str, str]]] = {}
    for r in rows:
        groups.setdefault((r["dataset_name"], r["method"]), []).append(r)
    out = []
    for (dataset, method), vals in sorted(groups.items()):
        acc = [float(v["final_acc"]) for v in vals]
        bal = [float(v["final_balanced_acc"]) for v in vals]
        bytes_ = [float(v["bytes_per_client_round"]) for v in vals]
        out.append(
            {
                "dataset": dataset,
                "method": method,
                "n": len(vals),
                "acc_mean": st.mean(acc),
                "acc_ci95": ci95(acc),
                "balanced_acc_mean": st.mean(bal),
                "bytes_mean": st.mean(bytes_),
            }
        )
    order_dataset = {"mnist4": 0, "fashion4": 1, "cifar4": 2}
    order_method = {
        "centralized_qproto": 0,
        "qproto_full": 1,
        "qproto_hop": 2,
        "qproto_proto": 3,
        "no_schema": 4,
        "forced_canonical": 5,
        "wrong_schema": 6,
        "fedavg_forced": 7,
        "fedprox_forced": 8,
        "local_only": 9,
        "classical_kernel": 10,
        "centralized_kernel": 11,
    }
    return sorted(out, key=lambda r: (order_dataset.get(str(r["dataset"]), 99), order_method.get(str(r["method"]), 99)))


def table(rows: list[dict[str, str | float | int]], dataset: str) -> str:
    rr = [r for r in rows if r["dataset"] == dataset]
    lines = [
        f"## {dataset}",
        "",
        "| Method | n | Acc. mean | 95% CI | Bal. acc. | Bytes |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for r in rr:
        lines.append(
            f"| {r['method']} | {r['n']} | {float(r['acc_mean']):.4f} | {float(r['acc_ci95']):.4f} | "
            f"{float(r['balanced_acc_mean']):.4f} | {float(r['bytes_mean']):.0f} |"
        )
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser("Summarize real image datasets")
    ap.add_argument("--summary", type=str, default="runs/summary.csv")
    ap.add_argument("--out", type=str, default="runs/real_image_dataset_tables.csv")
    ap.add_argument("--md", type=str, default="runs/real_image_dataset_tables.md")
    args = ap.parse_args()

    rows = []
    for r in read_rows(Path(args.summary)):
        for name in ["mnist4", "fashion4", "cifar4"]:
            if re.match(rf"real_{name}_main_seed\d+$", r["run"]) or re.match(rf"real_{name}_hop_seed\d+$", r["run"]):
                rr = dict(r)
                rr["dataset_name"] = name
                rows.append(rr)
                break

    out = summarize(rows)
    write_csv(Path(args.out), out)
    md = ["# Real Image Dataset Tables", ""]
    for name in ["mnist4", "fashion4", "cifar4"]:
        md.append(table(out, name))
        md.append("")
    Path(args.md).write_text("\n".join(md), encoding="utf-8")
    print(f"Wrote {args.out} and {args.md}")


if __name__ == "__main__":
    main()

