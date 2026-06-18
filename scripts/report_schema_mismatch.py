from __future__ import annotations

import argparse
import csv
import statistics as st
from pathlib import Path


def main() -> None:
    ap = argparse.ArgumentParser("Summarize wrong-schema shift severity runs")
    ap.add_argument("--summary", type=str, default="runs/summary.csv")
    args = ap.parse_args()

    with Path(args.summary).open("r", newline="", encoding="utf-8") as f:
        rows = [r for r in csv.DictReader(f) if r["run"].startswith("mismatch_shift")]

    print("wrong_shift,method,n,acc_mean,acc_std,balanced_acc_mean,distortion_mean")
    shifts = sorted({int(float(r.get("config_wrong_shift") or 0)) for r in rows})
    order = ["qproto_full", "forced_canonical", "no_schema", "wrong_schema"]
    for shift in shifts:
        for method in order:
            mr = [
                r
                for r in rows
                if int(float(r.get("config_wrong_shift") or 0)) == shift and r["method"] == method
            ]
            if not mr:
                continue
            acc = [float(r["final_acc"]) for r in mr]
            bal = [float(r["final_balanced_acc"]) for r in mr]
            dist = [float(r["distortion_proxy"]) for r in mr]
            print(
                f"{shift},{method},{len(acc)},"
                f"{st.mean(acc):.4f},{(st.stdev(acc) if len(acc) > 1 else 0.0):.4f},"
                f"{st.mean(bal):.4f},{st.mean(dist):.4f}"
            )


if __name__ == "__main__":
    main()

