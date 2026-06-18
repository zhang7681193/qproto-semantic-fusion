from __future__ import annotations

import argparse
import csv
import math
import re
import statistics as st
from pathlib import Path


T_CRIT_95 = {1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571}

METHOD_ORDER = {
    "schema_mask_only": 0,
    "schema_zero_fill": 1,
    "no_schema": 2,
    "forced_canonical": 3,
    "shared_observable": 4,
    "fedproto_schema": 5,
    "fedadam_schema": 6,
    "qproto_masked": 7,
    "qproto_cproto": 8,
    "qproto_masked_hop": 9,
    "qproto_chop": 10,
}

METHOD_LABELS = {
    "schema_mask_only": "Mask-only metadata",
    "schema_zero_fill": "Schema zero-fill",
    "no_schema": "No schema",
    "forced_canonical": "Forced canonical",
    "shared_observable": "Shared observables",
    "fedproto_schema": "FedProto schema",
    "fedadam_schema": "FedAdam schema",
    "qproto_masked": "QProto-Masked",
    "qproto_cproto": "CProto",
    "qproto_masked_hop": "QProto-Masked-HOP",
    "qproto_chop": "CHOP",
}


def ci95(xs: list[float]) -> float:
    if len(xs) <= 1:
        return 0.0
    return T_CRIT_95.get(len(xs) - 1, 1.96) * st.stdev(xs) / math.sqrt(len(xs))


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main() -> None:
    ap = argparse.ArgumentParser("Summarize IF-style non-image scientific fusion task")
    ap.add_argument("--summary", type=str, default="runs/summary.csv")
    ap.add_argument("--out", type=str, default="runs/if_scientific_fusion_report.csv")
    ap.add_argument("--md", type=str, default="runs/if_scientific_fusion_report.md")
    ap.add_argument("--tex", type=str, default="latex_qproto_hop/tables/table_if_scientific_fusion.tex")
    args = ap.parse_args()

    groups: dict[str, list[dict[str, str]]] = {}
    for row in read_rows(Path(args.summary)):
        if not re.match(r"^if_scientific_fusion_seed\d+$", str(row["run"])):
            continue
        method = str(row["method"])
        if method not in METHOD_ORDER:
            continue
        groups.setdefault(method, []).append(row)

    out_rows = []
    for method, vals in groups.items():
        acc = [float(v["final_acc"]) for v in vals]
        bal = [float(v["final_balanced_acc"]) for v in vals]
        bytes_ = [float(v["bytes_per_client_round"]) for v in vals]
        out_rows.append(
            {
                "method": method,
                "n": len(vals),
                "acc_mean": st.mean(acc),
                "acc_ci95": ci95(acc),
                "balanced_acc_mean": st.mean(bal),
                "bytes_mean": st.mean(bytes_),
            }
        )
    out_rows.sort(key=lambda r: METHOD_ORDER.get(str(r["method"]), 99))

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    fields = ["method", "n", "acc_mean", "acc_ci95", "balanced_acc_mean", "bytes_mean"]
    with out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(out_rows)

    lines = [
        "# IF-Style Scientific Fusion Report",
        "",
        "Synthetic non-image latent covariance-sensing task. Classes have weak mean signal and differ mainly through high-order readout structure; clients observe heterogeneous observable subsets.",
        "",
        "| Method | n | Acc. | 95% CI | Bal. acc. | Bytes |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for r in out_rows:
        lines.append(
            f"| {METHOD_LABELS.get(str(r['method']), str(r['method']))} | {r['n']} | "
            f"{float(r['acc_mean']):.4f} | {float(r['acc_ci95']):.4f} | "
            f"{float(r['balanced_acc_mean']):.4f} | {float(r['bytes_mean']):.0f} |"
        )
    Path(args.md).write_text("\n".join(lines), encoding="utf-8")

    tex = [
        "\\begin{table}[t]",
        "\\centering",
        "\\caption{Non-image scientific-fusion stress test with covariance-dominated quantum readout. Classes differ mainly through high-order readout structure, and clients observe heterogeneous observable subsets.}",
        "\\label{tab:if-scientific-fusion}",
        "\\begin{tabular}{lccc}",
        "\\toprule",
        "Method & Acc. & 95\\% CI & Bytes \\\\",
        "\\midrule",
    ]
    for r in out_rows:
        tex.append(
            f"{METHOD_LABELS.get(str(r['method']), str(r['method']))} & "
            f"{float(r['acc_mean']):.3f} & {float(r['acc_ci95']):.3f} & {float(r['bytes_mean']):.0f} \\\\"
        )
    tex.extend(["\\bottomrule", "\\end{tabular}", "\\end{table}", ""])
    tex_path = Path(args.tex)
    tex_path.parent.mkdir(parents=True, exist_ok=True)
    tex_path.write_text("\n".join(tex), encoding="utf-8")
    print(f"Wrote {out}, {args.md}, and {tex_path}")


if __name__ == "__main__":
    main()

