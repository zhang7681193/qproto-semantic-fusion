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


def infer(run: str) -> tuple[str, int] | None:
    patterns = [
        (r"chop_sweep_pennylane_highorder_k(\d+)_seed\d+$", "PennyLane high-order"),
        (r"chop_sweep_qiskit_aer_k(\d+)_seed\d+$", "Qiskit Aer MNIST-4"),
        (r"chop_sweep_mnist10_k(\d+)_seed\d+$", "MNIST-10"),
        (r"chop_sweep_fashion10_k(\d+)_seed\d+$", "Fashion-10"),
        (r"chop_sweep_cifar10_k(\d+)_seed\d+$", "CIFAR-10"),
    ]
    for pat, group in patterns:
        m = re.match(pat, run)
        if m:
            return group, int(m.group(1))
    return None


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main() -> None:
    ap = argparse.ArgumentParser("Summarize CHOP communication sweeps")
    ap.add_argument("--summary", type=str, default="runs/summary.csv")
    ap.add_argument("--out", type=str, default="runs/chop_sweep_tables.csv")
    ap.add_argument("--md", type=str, default="runs/chop_sweep_report.md")
    args = ap.parse_args()

    buckets: dict[tuple[str, int, str], list[dict[str, str]]] = {}
    for row in read_rows(Path(args.summary)):
        info = infer(row["run"])
        if info is None:
            continue
        group, k = info
        if row["method"] not in {"qproto_cproto", "qproto_chop"}:
            continue
        buckets.setdefault((group, k, row["method"]), []).append(row)

    out_rows = []
    for (group, k, method), vals in sorted(buckets.items()):
        acc = [float(v["final_acc"]) for v in vals]
        bal = [float(v["final_balanced_acc"]) for v in vals]
        bytes_ = [float(v["bytes_per_client_round"]) for v in vals]
        out_rows.append(
            {
                "group": group,
                "k": k,
                "method": method,
                "n": len(vals),
                "acc_mean": st.mean(acc),
                "acc_ci95": ci95(acc),
                "balanced_acc_mean": st.mean(bal),
                "bytes_mean": st.mean(bytes_),
            }
        )
    out_rows.sort(key=lambda r: (str(r["group"]), int(r["k"]), str(r["method"])))

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    if out_rows:
        with out.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(out_rows[0].keys()))
            writer.writeheader()
            writer.writerows(out_rows)

    lines = ["# CHOP Communication Sweep Report", ""]
    for group in sorted({str(r["group"]) for r in out_rows}):
        lines.extend([f"## {group}", "", "| K | Method | n | Acc. | 95% CI | Bal. acc. | Bytes |", "|---:|---|---:|---:|---:|---:|---:|"])
        for r in [x for x in out_rows if x["group"] == group]:
            lines.append(
                f"| {r['k']} | {r['method']} | {r['n']} | {float(r['acc_mean']):.4f} | "
                f"{float(r['acc_ci95']):.4f} | {float(r['balanced_acc_mean']):.4f} | {float(r['bytes_mean']):.0f} |"
            )
        lines.append("")

    lines.extend(
        [
            "## Interpretation",
            "",
            "- CHOP should be compared to CProto at the same K because they use the same selected observable keys.",
            "- On high-order readout, a widening gap between CHOP and CProto supports the claim that HOP captures second-order information rather than merely benefiting from key selection.",
            "- On mostly low-order image tasks, a small CHOP-CProto gap is acceptable; the goal there is communication-efficient preservation of coverage-aware QProto performance.",
        ]
    )
    Path(args.md).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {out} and {args.md}")


if __name__ == "__main__":
    main()

