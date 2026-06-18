from __future__ import annotations

import argparse
import csv
import re
import statistics as st
from pathlib import Path


def summarize(rows: list[dict[str, str]], prefix_re: str, x_name: str) -> list[str]:
    items = []
    for row in rows:
        match = re.match(prefix_re, row["run"])
        if match:
            items.append((int(match.group(1)), row))

    lines = ["sweep,x_value,method,n,acc_mean,acc_std,balanced_acc_mean,bytes_mean"]
    for x in sorted({x for x, _ in items}):
        for method in sorted({r["method"] for xx, r in items if xx == x}):
            mr = [r for xx, r in items if xx == x and r["method"] == method]
            acc = [float(r["final_acc"]) for r in mr]
            bal = [float(r["final_balanced_acc"]) for r in mr]
            by = [float(r["bytes_per_client_round"]) for r in mr]
            lines.append(
                f"{x_name},{x},{method},{len(acc)},"
                f"{st.mean(acc):.4f},{(st.stdev(acc) if len(acc) > 1 else 0.0):.4f},"
                f"{st.mean(bal):.4f},{st.mean(by):.1f}"
            )
    return lines


def main() -> None:
    ap = argparse.ArgumentParser("Summarize sketch/HOP dimension sensitivity")
    ap.add_argument("--summary", type=str, default="runs/summary.csv")
    args = ap.parse_args()

    with Path(args.summary).open("r", newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    out = []
    out.extend(summarize(rows, r"sketchdim(\d+)_seed\d+$", "sketch_dim"))
    hop = summarize(rows, r"hopdim(\d+)_seed\d+$", "hop_dim")
    out.extend(hop[1:] if hop else [])
    print("\n".join(out))


if __name__ == "__main__":
    main()

