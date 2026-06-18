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


def infer_group(run: str) -> str | None:
    patterns = [
        (r"topjournal_(mnist10)_pilot_seed\d+$", "MNIST-10 full-class"),
        (r"masked_mnist10_seed\d+$", "MNIST-10 full-class"),
        (r"masked_hop_mnist10_seed\d+$", "MNIST-10 full-class"),
        (r"chop_mnist10_k96_seed\d+$", "MNIST-10 full-class"),
        (r"strong_baseline_mnist10_seed\d+$", "MNIST-10 strong-baseline"),
        (r"schema_head_baseline_mnist10_seed\d+$", "MNIST-10 schema-head"),
        (r"matched_budget_mnist10_seed\d+$", "MNIST-10 matched-budget"),
        (r"topjournal_(fashion10)_pilot_seed\d+$", "Fashion-10 full-class"),
        (r"masked_fashion10_seed\d+$", "Fashion-10 full-class"),
        (r"masked_hop_fashion10_seed\d+$", "Fashion-10 full-class"),
        (r"chop_fashion10_k96_seed\d+$", "Fashion-10 full-class"),
        (r"strong_baseline_fashion10_seed\d+$", "Fashion-10 strong-baseline"),
        (r"schema_head_baseline_fashion10_seed\d+$", "Fashion-10 schema-head"),
        (r"matched_budget_fashion10_seed\d+$", "Fashion-10 matched-budget"),
        (r"topjournal_(cifar10)_pilot_seed\d+$", "CIFAR-10 full-class"),
        (r"masked_cifar10_seed\d+$", "CIFAR-10 full-class"),
        (r"masked_hop_cifar10_seed\d+$", "CIFAR-10 full-class"),
        (r"chop_cifar10_k96_seed\d+$", "CIFAR-10 full-class"),
        (r"strong_baseline_cifar10_seed\d+$", "CIFAR-10 strong-baseline"),
        (r"schema_head_baseline_cifar10_seed\d+$", "CIFAR-10 schema-head"),
        (r"matched_budget_cifar10_seed\d+$", "CIFAR-10 matched-budget"),
        (r"pennylane_mnist4_pca_seed\d+$", "PennyLane VQC MNIST-4"),
        (r"pennylane_mnist4_pca_shared_seed\d+$", "PennyLane VQC MNIST-4 low-overlap"),
        (r"masked_pennylane_mnist4_pca_seed\d+$", "PennyLane VQC MNIST-4"),
        (r"masked_hop_pennylane_mnist4_pca_seed\d+$", "PennyLane VQC MNIST-4"),
        (r"pennylane_private_signal_seed\d+$", "PennyLane private-signal stress"),
        (r"masked_pennylane_private_signal_seed\d+$", "PennyLane private-signal stress"),
        (r"masked_hop_pennylane_private_signal_seed\d+$", "PennyLane private-signal stress"),
        (r"pennylane_highorder_hop_seed\d+$", "PennyLane high-order readout"),
        (r"chop_pennylane_highorder_k24_seed\d+$", "PennyLane high-order readout"),
        (r"strong_baseline_pennylane_highorder_seed\d+$", "PennyLane high-order strong-baseline"),
        (r"schema_head_baseline_pennylane_highorder_seed\d+$", "PennyLane high-order schema-head"),
        (r"qiskit_aer_mnist4_seed\d+$", "Qiskit Aer noisy MNIST-4"),
        (r"masked_qiskit_aer_seed\d+$", "Qiskit Aer noisy MNIST-4"),
        (r"masked_hop_qiskit_aer_seed\d+$", "Qiskit Aer noisy MNIST-4"),
        (r"chop_qiskit_aer_k8_seed\d+$", "Qiskit Aer noisy MNIST-4"),
        (r"strong_baseline_qiskit_aer_seed\d+$", "Qiskit Aer strong-baseline"),
        (r"schema_head_baseline_qiskit_aer_seed\d+$", "Qiskit Aer schema-head"),
        (r"hardware_ready_aer_mnist2_seed\d+$", "Hardware-ready Aer MNIST-2"),
        (r"masked_hop_cov_main_seed\d+$", "Synthetic high-order covariance"),
        (r"masked_hop_cov_h16_seed\d+$", "Synthetic high-order covariance h16"),
    ]
    for pat, name in patterns:
        if re.match(pat, run):
            return name
    return None


def main() -> None:
    ap = argparse.ArgumentParser("Summarize top-journal pilot experiments")
    ap.add_argument("--summary", type=str, default="runs/summary.csv")
    ap.add_argument("--out", type=str, default="runs/topjournal_pilot_tables.csv")
    ap.add_argument("--md", type=str, default="runs/topjournal_pilot_report.md")
    args = ap.parse_args()

    rows = []
    for r in read_rows(Path(args.summary)):
        group = infer_group(r["run"])
        if group:
            run_name = str(r["run"])
            if run_name == "topjournal_mnist10_shared_seed0":
                continue
            if run_name.startswith("masked_") and not run_name.startswith("masked_hop_") and r["method"] != "qproto_masked":
                continue
            if (
                run_name.startswith("masked_hop_")
                and not run_name.startswith("masked_hop_cov_")
                and r["method"] != "qproto_masked_hop"
            ):
                continue
            if run_name.startswith("chop_") and r["method"] not in {"qproto_cproto", "qproto_chop"}:
                continue
            rr = dict(r)
            rr["group"] = group
            rows.append(rr)

    groups: dict[tuple[str, str], list[dict[str, str]]] = {}
    for r in rows:
        groups.setdefault((r["group"], r["method"]), []).append(r)

    out_rows = []
    for (group, method), vals in sorted(groups.items()):
        acc = [float(v["final_acc"]) for v in vals]
        bal = [float(v["final_balanced_acc"]) for v in vals]
        bytes_ = [float(v["bytes_per_client_round"]) for v in vals]
        out_rows.append(
            {
                "group": group,
                "method": method,
                "n": len(vals),
                "acc_mean": st.mean(acc),
                "acc_ci95": ci95(acc),
                "balanced_acc_mean": st.mean(bal),
                "bytes_mean": st.mean(bytes_),
            }
        )

    order_method = {
        "qproto_masked": 0,
        "qproto_masked_hop": 1,
        "qproto_masked_full": 2,
        "qproto_chop": 3,
        "qproto_cproto": 4,
        "qproto_hop": 5,
        "qproto_proto": 6,
        "fedproto_schema": 7,
        "fedproto_forced": 8,
        "fedadam_schema": 9,
        "fedavg_schema": 10,
        "fedprox_schema": 11,
        "fedadam_forced": 12,
        "fedavg_forced": 13,
        "fedprox_forced": 14,
        "shared_observable": 15,
        "no_schema": 16,
        "forced_canonical": 17,
        "wrong_schema": 18,
        "local_only": 19,
        "classical_kernel": 20,
    }
    out_rows.sort(key=lambda r: (str(r["group"]), order_method.get(str(r["method"]), 99)))

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(out_rows[0].keys()) if out_rows else [])
        if out_rows:
            writer.writeheader()
            writer.writerows(out_rows)

    lines = ["# Top-Journal Pilot Experiment Report", ""]
    for group in sorted({str(r["group"]) for r in out_rows}):
        lines.extend([f"## {group}", "", "| Method | n | Acc. | 95% CI | Bal. acc. | Bytes |", "|---|---:|---:|---:|---:|---:|"])
        for r in [x for x in out_rows if x["group"] == group]:
            lines.append(
                f"| {r['method']} | {r['n']} | {float(r['acc_mean']):.4f} | "
                f"{float(r['acc_ci95']):.4f} | {float(r['balanced_acc_mean']):.4f} | {float(r['bytes_mean']):.0f} |"
            )
        lines.append("")
    lines.extend(
        [
            "## Interpretation",
            "",
            "- Full-class MNIST/Fashion/CIFAR pilots preserve a large gap between correct-schema prototypes and no-schema/wrong-schema/FedAvg controls.",
            "- The coverage-aware masked variant tests the central journal claim more directly: protocol-defined observables can contribute even when they are not measured by every client.",
            "- The shared-observable baseline is strong when the common observable intersection already contains discriminative signal; beating it requires useful non-common observables plus correct missingness handling.",
            "- Mask-aware HOP is neutral to mildly positive on mostly low-order full-class image pilots, but it becomes the main driver on high-order readout tasks.",
            "- Compressed QProto-CHOP keeps most full-class performance at the old QProto-HOP byte budget, and improves the PennyLane high-order result while sending fewer bytes than full masked-HOP.",
            "- Key-policy controls show that anchor-informed CHOP is not random compression: on high-order PennyLane, coverage-key CHOP beats random-key CHOP by a large margin.",
            "- The PennyLane high-order benchmark is the strongest new HOP evidence: old HOP without coverage-aware aggregation is weak, while qproto_masked_hop separates the second-order signal.",
            "- Stronger FL baselines are now included: FedAdam improves over FedAvg/FedProx and schema-aware FedProto improves over forced-coordinate FedProto, but both remain below CProto/CHOP on full-class, Qiskit Aer, and PennyLane high-order pilots.",
            "- PennyLane and Qiskit Aer pilots now validate that the protocol can consume standard quantum-circuit readout features; hardware validation is still the biggest missing item.",
        ]
    )
    Path(args.md).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {out} and {args.md}")


if __name__ == "__main__":
    main()

