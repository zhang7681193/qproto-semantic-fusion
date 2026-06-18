from __future__ import annotations

import argparse
import csv
import re
import statistics as st
from pathlib import Path


def parse_alpha(run: str) -> float | None:
    match = re.match(r"noniid_a(\d+)p(\d+)_seed\d+$", run)
    if not match:
        return None
    return float(match.group(1) + "." + match.group(2))


def main() -> None:
    ap = argparse.ArgumentParser("Summarize Dirichlet non-IID sensitivity")
    ap.add_argument("--summary", type=str, default="runs/summary.csv")
    args = ap.parse_args()

    with Path(args.summary).open("r", newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    items = []
    for row in rows:
        alpha = parse_alpha(row["run"])
        if alpha is not None:
            items.append((alpha, row))

    methods = ["qproto_full", "qproto_proto", "no_schema", "wrong_schema", "fedavg_forced", "fedprox_forced"]
    print("alpha,method,n,acc_mean,acc_std,balanced_acc_mean,bytes_mean")
    for alpha in sorted({a for a, _ in items}):
        for method in methods:
            mr = [r for a, r in items if a == alpha and r["method"] == method]
            if not mr:
                continue
            acc = [float(r["final_acc"]) for r in mr]
            bal = [float(r["final_balanced_acc"]) for r in mr]
            by = [float(r["bytes_per_client_round"]) for r in mr]
            print(
                f"{alpha:.2f},{method},{len(acc)},"
                f"{st.mean(acc):.4f},{(st.stdev(acc) if len(acc) > 1 else 0.0):.4f},"
                f"{st.mean(bal):.4f},{st.mean(by):.1f}"
            )


if __name__ == "__main__":
    main()

