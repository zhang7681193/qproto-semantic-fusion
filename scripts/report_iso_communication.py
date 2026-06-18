from __future__ import annotations

import argparse
import csv
import re
import statistics as st
from pathlib import Path


VARIANT_ORDER = [
    "proto_low",
    "hop_low",
    "proto_high",
    "hop_high",
]


def variant_from_run(run: str) -> str | None:
    match = re.match(r"iso_(proto_low|hop_low|proto_high|hop_high)_seed\d+$", run)
    return match.group(1) if match else None


def mean(xs: list[float]) -> float:
    return st.mean(xs) if xs else 0.0


def std(xs: list[float]) -> float:
    return st.stdev(xs) if len(xs) > 1 else 0.0


def main() -> None:
    ap = argparse.ArgumentParser("Summarize iso-communication QProto-HOP runs")
    ap.add_argument("--summary", type=str, default="runs/summary.csv")
    args = ap.parse_args()

    with Path(args.summary).open("r", newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    print("variant,method,n,bytes_mean,acc_mean,acc_std,balanced_acc_mean,sketch_dim,hop_dim")
    for variant in VARIANT_ORDER:
        vr = [r for r in rows if variant_from_run(r["run"]) == variant]
        if not vr:
            continue
        methods = sorted({r["method"] for r in vr})
        for method in methods:
            mr = [r for r in vr if r["method"] == method]
            acc = [float(r["final_acc"]) for r in mr]
            bal = [float(r["final_balanced_acc"]) for r in mr]
            by = [float(r["bytes_per_client_round"]) for r in mr]
            sketch = sorted({r.get("config_sketch_dim", "") for r in mr})
            hop = sorted({r.get("config_hop_dim", "") for r in mr})
            print(
                f"{variant},{method},{len(mr)},{mean(by):.1f},"
                f"{mean(acc):.4f},{std(acc):.4f},{mean(bal):.4f},"
                f"{'/'.join(sketch)},{'/'.join(hop)}"
            )


if __name__ == "__main__":
    main()

