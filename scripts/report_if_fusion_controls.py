from __future__ import annotations

import argparse
import csv
import math
import re
import statistics as st
from pathlib import Path


T_CRIT_95 = {1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571}

GROUPS = [
    (r"if_fusion_fullclass_mnist10_seed\d+$", "MNIST-10"),
    (r"if_fusion_fullclass_fashion10_seed\d+$", "Fashion-10"),
    (r"if_fusion_fullclass_cifar10_seed\d+$", "CIFAR-10"),
]

METHOD_ORDER = {
    "schema_mask_only": 0,
    "schema_zero_fill": 1,
    "no_schema": 2,
    "forced_canonical": 3,
    "shared_observable": 4,
    "qproto_proto": 5,
    "qproto_cproto": 6,
    "qproto_chop": 7,
    "qproto_masked": 8,
    "qproto_masked_hop": 9,
}

METHOD_LABELS = {
    "schema_mask_only": "Mask-only metadata",
    "schema_zero_fill": "Schema zero-fill",
    "no_schema": "No schema",
    "forced_canonical": "Forced canonical",
    "shared_observable": "Shared observables",
    "qproto_proto": "RFF prototype",
    "qproto_cproto": "CProto",
    "qproto_chop": "CHOP",
    "qproto_masked": "QProto-Masked",
    "qproto_masked_hop": "QProto-Masked-HOP",
}


def ci95(xs: list[float]) -> float:
    if len(xs) <= 1:
        return 0.0
    return T_CRIT_95.get(len(xs) - 1, 1.96) * st.stdev(xs) / math.sqrt(len(xs))


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def infer_group(run: str) -> str | None:
    for pattern, group in GROUPS:
        if re.match(pattern, run):
            return group
    return None


def main() -> None:
    ap = argparse.ArgumentParser("Summarize IF-style heterogeneous fusion controls")
    ap.add_argument("--summary", type=str, default="runs/summary.csv")
    ap.add_argument("--out", type=str, default="runs/if_fusion_controls_report.csv")
    ap.add_argument("--md", type=str, default="runs/if_fusion_controls_report.md")
    ap.add_argument("--tex", type=str, default="latex_qproto_hop/tables/table_if_fusion_controls.tex")
    args = ap.parse_args()

    groups: dict[tuple[str, str], list[dict[str, str]]] = {}
    for row in read_rows(Path(args.summary)):
        group = infer_group(str(row["run"]))
        method = str(row["method"])
        if group is None or method not in METHOD_ORDER:
            continue
        groups.setdefault((group, method), []).append(row)

    out_rows = []
    for (group, method), vals in groups.items():
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

    out_rows.sort(key=lambda r: (str(r["group"]), METHOD_ORDER.get(str(r["method"]), 99)))
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    fields = ["group", "method", "n", "acc_mean", "acc_ci95", "balanced_acc_mean", "bytes_mean"]
    with out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(out_rows)

    lines = ["# IF-Style Heterogeneous Fusion Control Report", ""]
    for group in sorted({str(r["group"]) for r in out_rows}):
        lines.extend([f"## {group}", "", "| Method | n | Acc. | 95% CI | Bal. acc. | Bytes |", "|---|---:|---:|---:|---:|---:|"])
        for r in [x for x in out_rows if x["group"] == group]:
            lines.append(
                f"| {METHOD_LABELS.get(str(r['method']), str(r['method']))} | {r['n']} | "
                f"{float(r['acc_mean']):.4f} | {float(r['acc_ci95']):.4f} | "
                f"{float(r['balanced_acc_mean']):.4f} | {float(r['bytes_mean']):.0f} |"
            )
        lines.append("")
    Path(args.md).write_text("\n".join(lines), encoding="utf-8")

    tex = [
        "\\begin{table*}[t]",
        "\\centering",
        "\\caption{IF-style heterogeneous fusion controls on full-class datasets. Zero-fill and mask-only are generic missing-observation controls; shared-observable aggregation uses only the intersection observed by every client. Bytes are per client per round.}",
        "\\label{tab:if-fusion-controls}",
        "\\begin{tabular}{llccc}",
        "\\toprule",
        "Dataset & Method & Acc. & 95\\% CI & Bytes \\\\",
        "\\midrule",
    ]
    for gi, group in enumerate(["MNIST-10", "Fashion-10", "CIFAR-10"]):
        rows = [r for r in out_rows if r["group"] == group]
        for r in rows:
            tex.append(
                f"{group} & {METHOD_LABELS.get(str(r['method']), str(r['method']))} & "
                f"{float(r['acc_mean']):.3f} & {float(r['acc_ci95']):.3f} & {float(r['bytes_mean']):.0f} \\\\"
            )
        if gi < 2:
            tex.append("\\midrule")
    tex.extend(["\\bottomrule", "\\end{tabular}", "\\end{table*}", ""])
    tex_path = Path(args.tex)
    tex_path.parent.mkdir(parents=True, exist_ok=True)
    tex_path.write_text("\n".join(tex), encoding="utf-8")
    print(f"Wrote {out}, {args.md}, and {tex_path}")


if __name__ == "__main__":
    main()

