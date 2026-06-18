from __future__ import annotations

import argparse
import csv
import re
import statistics as st
from pathlib import Path


def main() -> None:
    ap = argparse.ArgumentParser("Summarize anchor-size sensitivity runs")
    ap.add_argument("--summary", type=str, default="runs/summary.csv")
    args = ap.parse_args()

    with Path(args.summary).open("r", newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    items: list[tuple[int, dict[str, str]]] = []
    for row in rows:
        match = re.match(r"anchor(\d+)_seed\d+$", row["run"])
        if match:
            items.append((int(match.group(1)), row))

    print("anchor,method,n,acc_mean,acc_std,balanced_acc_mean,distortion_mean")
    for anchor in sorted({a for a, _ in items}):
        methods = sorted({r["method"] for a, r in items if a == anchor})
        for method in methods:
            mr = [r for a, r in items if a == anchor and r["method"] == method]
            acc = [float(r["final_acc"]) for r in mr]
            bal = [float(r["final_balanced_acc"]) for r in mr]
            dist = [float(r["distortion_proxy"]) for r in mr]
            print(
                f"{anchor},{method},{len(acc)},"
                f"{st.mean(acc):.4f},{(st.stdev(acc) if len(acc) > 1 else 0.0):.4f},"
                f"{st.mean(bal):.4f},{st.mean(dist):.4f}"
            )


if __name__ == "__main__":
    main()

