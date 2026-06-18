from __future__ import annotations

import argparse
import csv
import math
import re
import statistics as st
from pathlib import Path


T_CRIT_95 = {1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571}


def ci95(xs: list[float]) -> float:
    if len(xs) <= 1:
        return 0.0
    return T_CRIT_95.get(len(xs) - 1, 1.96) * st.stdev(xs) / math.sqrt(len(xs))


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def seed_from_run(run: str) -> int | None:
    m = re.search(r"_seed(\d+)$", run)
    return int(m.group(1)) if m else None


def by_run_method(rows: list[dict[str, str]]) -> dict[tuple[str, str], dict[str, str]]:
    return {(r["run"], r["method"]): r for r in rows}


def collect_direct_delta(
    rows: list[dict[str, str]],
    *,
    pattern: str,
    group: str,
    method_a: str,
    method_b: str,
    label: str,
) -> dict[str, object] | None:
    keyed = by_run_method(rows)
    deltas = []
    for r in rows:
        if r["method"] != method_a or not re.match(pattern, r["run"]):
            continue
        b = keyed.get((r["run"], method_b))
        if b is None:
            continue
        deltas.append(float(r["final_acc"]) - float(b["final_acc"]))
    if not deltas:
        return None
    return {
        "comparison": label,
        "group": group,
        "n": len(deltas),
        "delta_acc_mean": st.mean(deltas),
        "delta_acc_ci95": ci95(deltas),
        "wins": sum(1 for x in deltas if x > 0),
    }


def collect_policy_delta(
    rows: list[dict[str, str]],
    *,
    group_pattern_a: str,
    group_pattern_b: str,
    group: str,
    method: str,
    label: str,
) -> dict[str, object] | None:
    a_by_seed = {}
    b_by_seed = {}
    for r in rows:
        if r["method"] != method:
            continue
        seed = seed_from_run(r["run"])
        if seed is None:
            continue
        if re.match(group_pattern_a, r["run"]):
            a_by_seed[seed] = float(r["final_acc"])
        if re.match(group_pattern_b, r["run"]):
            b_by_seed[seed] = float(r["final_acc"])
    seeds = sorted(set(a_by_seed).intersection(b_by_seed))
    deltas = [a_by_seed[s] - b_by_seed[s] for s in seeds]
    if not deltas:
        return None
    return {
        "comparison": label,
        "group": group,
        "n": len(deltas),
        "delta_acc_mean": st.mean(deltas),
        "delta_acc_ci95": ci95(deltas),
        "wins": sum(1 for x in deltas if x > 0),
    }


def main() -> None:
    ap = argparse.ArgumentParser("Report paired deltas for key QProto comparisons")
    ap.add_argument("--summary", type=str, default="runs/summary.csv")
    ap.add_argument("--out", type=str, default="runs/pairwise_deltas.csv")
    ap.add_argument("--md", type=str, default="runs/pairwise_deltas.md")
    args = ap.parse_args()

    rows = read_rows(Path(args.summary))
    comparisons = [
        collect_direct_delta(
            rows,
            pattern=r"pennylane_highorder_hop_seed\d+$",
            group="PennyLane high-order",
            method_a="qproto_masked_hop",
            method_b="qproto_masked",
            label="masked-HOP minus masked",
        ),
        collect_direct_delta(
            rows,
            pattern=r"pennylane_highorder_hop_seed\d+$",
            group="PennyLane high-order",
            method_a="qproto_masked_hop",
            method_b="qproto_hop",
            label="masked-HOP minus old-HOP",
        ),
        collect_direct_delta(
            rows,
            pattern=r"chop_sweep_pennylane_highorder_k8_seed\d+$",
            group="PennyLane high-order K=8",
            method_a="qproto_chop",
            method_b="qproto_cproto",
            label="CHOP minus CProto",
        ),
        collect_policy_delta(
            rows,
            group_pattern_a=r"chop_policy_pennylane_highorder_coverage_k8_seed\d+$",
            group_pattern_b=r"chop_policy_pennylane_highorder_random_k8_seed\d+$",
            group="PennyLane high-order K=8",
            method="qproto_chop",
            label="coverage-key CHOP minus random-key CHOP",
        ),
        collect_policy_delta(
            rows,
            group_pattern_a=r"chop_policy_mnist10_variance_k96_seed\d+$",
            group_pattern_b=r"chop_policy_mnist10_random_k96_seed\d+$",
            group="MNIST-10 K=96",
            method="qproto_chop",
            label="variance-key CHOP minus random-key CHOP",
        ),
        collect_policy_delta(
            rows,
            group_pattern_a=r"chop_policy_cifar10_coverage_k96_seed\d+$",
            group_pattern_b=r"chop_policy_cifar10_random_k96_seed\d+$",
            group="CIFAR-10 K=96",
            method="qproto_chop",
            label="coverage-key CHOP minus random-key CHOP",
        ),
        collect_direct_delta(
            rows,
            pattern=r"strong_baseline_mnist10_seed\d+$",
            group="MNIST-10 strong-baseline",
            method_a="qproto_chop",
            method_b="fedproto_schema",
            label="CHOP minus schema-FedProto",
        ),
        collect_direct_delta(
            rows,
            pattern=r"strong_baseline_cifar10_seed\d+$",
            group="CIFAR-10 strong-baseline",
            method_a="qproto_chop",
            method_b="fedproto_schema",
            label="CHOP minus schema-FedProto",
        ),
        collect_direct_delta(
            rows,
            pattern=r"strong_baseline_qiskit_aer_seed\d+$",
            group="Qiskit Aer strong-baseline",
            method_a="qproto_chop",
            method_b="fedproto_schema",
            label="CHOP minus schema-FedProto",
        ),
        collect_direct_delta(
            rows,
            pattern=r"strong_baseline_pennylane_highorder_seed\d+$",
            group="PennyLane high-order strong-baseline",
            method_a="qproto_chop",
            method_b="fedproto_schema",
            label="CHOP minus schema-FedProto",
        ),
        collect_direct_delta(
            rows,
            pattern=r"strong_baseline_pennylane_highorder_seed\d+$",
            group="PennyLane high-order strong-baseline",
            method_a="qproto_chop",
            method_b="fedadam_forced",
            label="CHOP minus FedAdam",
        ),
        collect_direct_delta(
            rows,
            pattern=r"schema_head_baseline_mnist10_seed\d+$",
            group="MNIST-10 schema-head",
            method_a="qproto_chop",
            method_b="fedadam_schema",
            label="CHOP minus schema-FedAdam",
        ),
        collect_direct_delta(
            rows,
            pattern=r"schema_head_baseline_cifar10_seed\d+$",
            group="CIFAR-10 schema-head",
            method_a="qproto_chop",
            method_b="fedadam_schema",
            label="CHOP minus schema-FedAdam",
        ),
        collect_direct_delta(
            rows,
            pattern=r"schema_head_baseline_pennylane_highorder_seed\d+$",
            group="PennyLane high-order schema-head",
            method_a="qproto_chop",
            method_b="fedadam_schema",
            label="CHOP minus schema-FedAdam",
        ),
    ]
    out_rows = [c for c in comparisons if c is not None]

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    if out_rows:
        with out.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(out_rows[0].keys()))
            writer.writeheader()
            writer.writerows(out_rows)

    lines = ["# Pairwise Delta Report", "", "| Comparison | Group | n | Mean acc. delta | 95% CI | Wins |", "|---|---|---:|---:|---:|---:|"]
    for r in out_rows:
        lines.append(
            f"| {r['comparison']} | {r['group']} | {r['n']} | "
            f"{float(r['delta_acc_mean']):.4f} | {float(r['delta_acc_ci95']):.4f} | {r['wins']}/{r['n']} |"
        )
    Path(args.md).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {out} and {args.md}")


if __name__ == "__main__":
    main()

