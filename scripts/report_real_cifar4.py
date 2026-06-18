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


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def ci95(xs: list[float]) -> float:
    if len(xs) <= 1:
        return 0.0
    t = T_CRIT_95.get(len(xs) - 1, 1.96)
    return t * st.stdev(xs) / math.sqrt(len(xs))


def mean(xs: list[float]) -> float:
    return st.mean(xs) if xs else 0.0


def summarize_group(rows: list[dict[str, str]], group_fields: list[str]) -> list[dict[str, str | float | int]]:
    groups: dict[tuple[str, ...], list[dict[str, str]]] = {}
    for row in rows:
        key = tuple(row[field] for field in group_fields)
        groups.setdefault(key, []).append(row)
    out = []
    for key, vals in sorted(groups.items()):
        acc = [float(v["final_acc"]) for v in vals]
        bal = [float(v["final_balanced_acc"]) for v in vals]
        bytes_ = [float(v["bytes_per_client_round"]) for v in vals]
        rec: dict[str, str | float | int] = {field: key[i] for i, field in enumerate(group_fields)}
        rec.update(
            {
                "n": len(vals),
                "acc_mean": mean(acc),
                "acc_ci95": ci95(acc),
                "balanced_acc_mean": mean(bal),
                "bytes_mean": mean(bytes_),
            }
        )
        out.append(rec)
    return out


def write_csv(path: Path, rows: list[dict[str, str | float | int]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fields = list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def markdown_table(rows: list[dict[str, str | float | int]], fields: list[str]) -> str:
    lines = ["| " + " | ".join(fields) + " |", "|" + "|".join(["---"] * len(fields)) + "|"]
    for row in rows:
        vals = []
        for field in fields:
            value = row[field]
            if isinstance(value, float):
                vals.append(f"{value:.4f}")
            else:
                vals.append(str(value))
        lines.append("| " + " | ".join(vals) + " |")
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser("Summarize real CIFAR-4 QProto-HOP experiments")
    ap.add_argument("--summary", type=str, default="runs/summary.csv")
    ap.add_argument("--out-dir", type=str, default="runs")
    args = ap.parse_args()

    rows = read_rows(Path(args.summary))
    out_dir = Path(args.out_dir)

    main_rows = [r for r in rows if re.match(r"real_cifar4_main_seed\d+$", r["run"])]
    main_stats = summarize_group(main_rows, ["method"])
    order = [
        "centralized_qproto",
        "qproto_full",
        "qproto_hop",
        "qproto_proto",
        "no_schema",
        "forced_canonical",
        "wrong_schema",
        "fedavg_forced",
        "fedprox_forced",
        "local_only",
        "classical_kernel",
        "centralized_kernel",
    ]
    main_stats = sorted(main_stats, key=lambda r: order.index(str(r["method"])) if str(r["method"]) in order else 999)
    write_csv(out_dir / "real_cifar4_main_table.csv", main_stats)

    shot_rows = []
    for r in rows:
        m = re.match(r"real_cifar4_shot(\d+)_seed\d+$", r["run"])
        if m:
            rr = dict(r)
            rr["shots"] = m.group(1)
            shot_rows.append(rr)
    shot_stats = summarize_group(shot_rows, ["shots", "method"])
    shot_stats = sorted(shot_stats, key=lambda r: (int(str(r["shots"])), str(r["method"])))
    write_csv(out_dir / "real_cifar4_shot_sweep.csv", shot_stats)

    comm_rows = []
    for r in rows:
        m = re.match(r"real_cifar4_comm_(.+)_seed\d+$", r["run"])
        if m:
            rr = dict(r)
            variant = m.group(1)
            rr["variant"] = variant
            rr["pair"] = re.sub(r"^(proto|hop)", "", variant)
            rr["family"] = "hop" if variant.startswith("hop") else "proto"
            comm_rows.append(rr)
    comm_stats = summarize_group(comm_rows, ["pair", "family", "variant"])
    comm_stats = sorted(comm_stats, key=lambda r: (float(r["bytes_mean"]), str(r["family"])))
    write_csv(out_dir / "real_cifar4_comm_budget.csv", comm_stats)

    md = [
        "# Real CIFAR-4 Experiment Tables",
        "",
        "## Main Baselines",
        "",
        markdown_table(main_stats, ["method", "n", "acc_mean", "acc_ci95", "balanced_acc_mean", "bytes_mean"]),
        "",
        "## Shot Sweep",
        "",
        markdown_table(shot_stats, ["shots", "method", "n", "acc_mean", "acc_ci95", "balanced_acc_mean"]),
        "",
        "## Matched Communication",
        "",
        markdown_table(comm_stats, ["pair", "family", "variant", "n", "acc_mean", "acc_ci95", "bytes_mean"]),
        "",
    ]
    (out_dir / "real_cifar4_tables.md").write_text("\n".join(md), encoding="utf-8")
    print(f"Wrote real CIFAR-4 reports to {out_dir}")


if __name__ == "__main__":
    main()

