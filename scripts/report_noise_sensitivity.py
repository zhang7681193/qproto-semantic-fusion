from __future__ import annotations

import argparse
import csv
import re
import statistics as st
from pathlib import Path


ORDER = {"low": 0, "mid": 1, "high": 2}


def main() -> None:
    ap = argparse.ArgumentParser("Summarize hardware/readout noise heterogeneity runs")
    ap.add_argument("--summary", type=str, default="runs/summary.csv")
    args = ap.parse_args()

    with Path(args.summary).open("r", newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    items = []
    for row in rows:
        match = re.match(r"noise_(low|mid|high)_seed\d+$", row["run"])
        if match:
            items.append((match.group(1), row))

    print("noise,method,n,acc_mean,acc_std,balanced_acc_mean,bytes_mean")
    methods = ["qproto_full", "qproto_hop", "qproto_proto", "no_schema", "wrong_schema", "fedavg_forced", "fedprox_forced"]
    for noise in sorted({n for n, _ in items}, key=lambda x: ORDER[x]):
        for method in methods:
            mr = [r for n, r in items if n == noise and r["method"] == method]
            if not mr:
                continue
            acc = [float(r["final_acc"]) for r in mr]
            bal = [float(r["final_balanced_acc"]) for r in mr]
            bytes_ = [float(r["bytes_per_client_round"]) for r in mr]
            print(
                f"{noise},{method},{len(acc)},"
                f"{st.mean(acc):.4f},{(st.stdev(acc) if len(acc) > 1 else 0.0):.4f},"
                f"{st.mean(bal):.4f},{st.mean(bytes_):.1f}"
            )


if __name__ == "__main__":
    main()

