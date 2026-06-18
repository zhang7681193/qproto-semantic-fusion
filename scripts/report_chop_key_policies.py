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


def infer(run: str) -> tuple[str, str, int] | None:
    patterns = [
        (r"chop_policy_pennylane_highorder_(variance|coverage|random)_k(\d+)_seed\d+$", "PennyLane high-order"),
        (r"chop_policy_qiskit_aer_(variance|coverage|random)_k(\d+)_seed\d+$", "Qiskit Aer MNIST-4"),
        (r"chop_policy_mnist10_(variance|coverage|random)_k(\d+)_seed\d+$", "MNIST-10"),
        (r"chop_policy_cifar10_(variance|coverage|random)_k(\d+)_seed\d+$", "CIFAR-10"),
    ]
    for pat, group in patterns:
        m = re.match(pat, run)
        if m:
            return group, m.group(1), int(m.group(2))
    return None


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main() -> None:
    ap = argparse.ArgumentParser("Summarize CHOP key policy controls")
    ap.add_argument("--summary", type=str, default="runs/summary.csv")
    ap.add_argument("--out", type=str, default="runs/chop_key_policy_tables.csv")
    ap.add_argument("--md", type=str, default="runs/chop_key_policy_report.md")
    args = ap.parse_args()

    buckets: dict[tuple[str, str, int, str], list[dict[str, str]]] = {}
    for row in read_rows(Path(args.summary)):
        info = infer(row["run"])
        if info is None:
            continue
        group, policy, k = info
        if row["method"] not in {"qproto_cproto", "qproto_chop"}:
            continue
        buckets.setdefault((group, policy, k, row["method"]), []).append(row)

    out_rows = []
    for (group, policy, k, method), vals in sorted(buckets.items()):
        acc = [float(v["final_acc"]) for v in vals]
        bal = [float(v["final_balanced_acc"]) for v in vals]
        bytes_ = [float(v["bytes_per_client_round"]) for v in vals]
        out_rows.append(
            {
                "group": group,
                "policy": policy,
                "k": k,
                "method": method,
                "n": len(vals),
                "acc_mean": st.mean(acc),
                "acc_ci95": ci95(acc),
                "balanced_acc_mean": st.mean(bal),
                "bytes_mean": st.mean(bytes_),
            }
        )
    policy_order = {"variance": 0, "coverage": 1, "random": 2}
    method_order = {"qproto_chop": 0, "qproto_cproto": 1}
    out_rows.sort(key=lambda r: (str(r["group"]), int(r["k"]), policy_order[str(r["policy"])], method_order[str(r["method"])]))

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    if out_rows:
        with out.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(out_rows[0].keys()))
            writer.writeheader()
            writer.writerows(out_rows)

    lines = ["# CHOP Key Policy Control Report", ""]
    for group in sorted({str(r["group"]) for r in out_rows}):
        lines.extend([f"## {group}", "", "| Policy | K | Method | n | Acc. | 95% CI | Bal. acc. | Bytes |", "|---|---:|---|---:|---:|---:|---:|---:|"])
        for r in [x for x in out_rows if x["group"] == group]:
            lines.append(
                f"| {r['policy']} | {r['k']} | {r['method']} | {r['n']} | {float(r['acc_mean']):.4f} | "
                f"{float(r['acc_ci95']):.4f} | {float(r['balanced_acc_mean']):.4f} | {float(r['bytes_mean']):.0f} |"
            )
        lines.append("")

    lines.extend(
        [
            "## Interpretation",
            "",
            "- Variance policy is the proposed public-anchor key selection rule.",
            "- Random policy controls whether compression merely needs any K observables.",
            "- Coverage policy controls whether selecting frequently observed keys is enough without value variation.",
            "- CHOP should be compared against CProto within the same policy and K.",
        ]
    )
    Path(args.md).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {out} and {args.md}")


if __name__ == "__main__":
    main()

