from __future__ import annotations

import argparse
import csv
import re
import statistics as st
from pathlib import Path


def parse_variant(run: str) -> tuple[str, int] | None:
    match = re.match(r"comm_(proto|hop)_(\d+)_seed\d+$", run)
    if not match:
        return None
    return match.group(1), int(match.group(2))


def main() -> None:
    ap = argparse.ArgumentParser("Summarize communication budget curve")
    ap.add_argument("--summary", type=str, default="runs/summary.csv")
    args = ap.parse_args()

    with Path(args.summary).open("r", newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    items = []
    for row in rows:
        parsed = parse_variant(row["run"])
        if parsed is not None:
            items.append((parsed[0], parsed[1], row))

    print("variant,total_dim,method,n,bytes_mean,acc_mean,acc_std,balanced_acc_mean")
    for total_dim in sorted({d for _, d, _ in items}):
        for variant in ["proto", "hop"]:
            mr = [r for v, d, r in items if v == variant and d == total_dim]
            if not mr:
                continue
            acc = [float(r["final_acc"]) for r in mr]
            bal = [float(r["final_balanced_acc"]) for r in mr]
            by = [float(r["bytes_per_client_round"]) for r in mr]
            method = mr[0]["method"]
            print(
                f"{variant},{total_dim},{method},{len(acc)},"
                f"{st.mean(by):.1f},{st.mean(acc):.4f},"
                f"{(st.stdev(acc) if len(acc) > 1 else 0.0):.4f},{st.mean(bal):.4f}"
            )


if __name__ == "__main__":
    main()

