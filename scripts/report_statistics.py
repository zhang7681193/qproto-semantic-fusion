from __future__ import annotations

import argparse
import csv
import math
import re
import statistics as st
from pathlib import Path


T_CRIT_95 = {
    1: 12.706,
    2: 4.303,
    3: 3.182,
    4: 2.776,
    5: 2.571,
    6: 2.447,
    7: 2.365,
    8: 2.306,
    9: 2.262,
    10: 2.228,
}


def seed_key(run: str) -> str:
    match = re.search(r"seed(\d+)$", run)
    return match.group(1) if match else run


def ci95(xs: list[float]) -> float:
    if len(xs) <= 1:
        return 0.0
    t = T_CRIT_95.get(len(xs) - 1, 1.96)
    return t * st.stdev(xs) / math.sqrt(len(xs))


def main() -> None:
    ap = argparse.ArgumentParser("Report means, 95% CIs, and paired deltas")
    ap.add_argument("--summary", type=str, default="runs/summary.csv")
    ap.add_argument("--prefix", type=str, required=True)
    ap.add_argument("--reference", type=str, default="qproto_full")
    ap.add_argument("--out", type=str, default="")
    args = ap.parse_args()

    with Path(args.summary).open("r", newline="", encoding="utf-8") as f:
        rows = [r for r in csv.DictReader(f) if r["run"].startswith(args.prefix)]

    methods = sorted({r["method"] for r in rows})
    out_rows = []
    ref_by_seed = {seed_key(r["run"]): float(r["final_acc"]) for r in rows if r["method"] == args.reference}
    for method in methods:
        mr = [r for r in rows if r["method"] == method]
        acc = [float(r["final_acc"]) for r in mr]
        bal = [float(r["final_balanced_acc"]) for r in mr]
        bytes_ = [float(r["bytes_per_client_round"]) for r in mr]
        deltas = []
        for r in mr:
            sk = seed_key(r["run"])
            if sk in ref_by_seed and method != args.reference:
                deltas.append(ref_by_seed[sk] - float(r["final_acc"]))
        out_rows.append(
            {
                "prefix": args.prefix,
                "method": method,
                "n": len(acc),
                "acc_mean": st.mean(acc) if acc else 0.0,
                "acc_ci95": ci95(acc),
                "balanced_acc_mean": st.mean(bal) if bal else 0.0,
                "bytes_mean": st.mean(bytes_) if bytes_ else 0.0,
                "ref_minus_method_mean": st.mean(deltas) if deltas else "",
                "ref_minus_method_ci95": ci95(deltas) if deltas else "",
                "paired_wins": sum(1 for d in deltas if d > 0),
                "paired_n": len(deltas),
            }
        )

    fields = [
        "prefix",
        "method",
        "n",
        "acc_mean",
        "acc_ci95",
        "balanced_acc_mean",
        "bytes_mean",
        "ref_minus_method_mean",
        "ref_minus_method_ci95",
        "paired_wins",
        "paired_n",
    ]
    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            writer.writerows(out_rows)
        print(f"Wrote {len(out_rows)} rows to {out}")
    else:
        writer = csv.DictWriter(__import__("sys").stdout, fieldnames=fields)
        writer.writeheader()
        writer.writerows(out_rows)


if __name__ == "__main__":
    main()

