from __future__ import annotations

import argparse
import csv
from pathlib import Path


METHOD_NAMES = {
    "centralized_qproto": "Centralized QProto",
    "qproto_full": "Full + shrinkage",
    "qproto_hop": "QProto-HOP",
    "qproto_proto": "QProto prototype",
    "no_schema": "No schema",
    "forced_canonical": "Forced canonical",
    "wrong_schema": "Wrong schema",
    "fedavg_forced": "FedAvg forced",
    "fedprox_forced": "FedProx forced",
    "local_only": "Local only",
    "classical_kernel": "Classical kernel",
    "centralized_kernel": "Centralized kernel",
}

DATASET_NAMES = {
    "mnist4": "MNIST-4",
    "fashion4": "Fashion-4",
    "cifar4": "CIFAR-4",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def fmt(x: str | float, nd: int = 3) -> str:
    return f"{float(x):.{nd}f}"


def table(caption: str, label: str, columns: str, header: str, rows: list[str]) -> str:
    return "\n".join(
        [
            "\\begin{table}[t]",
            "\\centering",
            f"\\caption{{{caption}}}",
            f"\\label{{{label}}}",
            f"\\begin{{tabular}}{{{columns}}}",
            "\\toprule",
            header + " \\\\",
            "\\midrule",
            "\n".join(rows),
            "\\bottomrule",
            "\\end{tabular}",
            "\\end{table}",
            "",
        ]
    )


def real_image_table(rows: list[dict[str, str]]) -> str:
    methods = ["qproto_hop", "qproto_proto", "no_schema", "forced_canonical", "wrong_schema", "fedavg_forced", "fedprox_forced", "classical_kernel"]
    body = []
    for dataset in ["mnist4", "fashion4", "cifar4"]:
        body.append(f"\\multicolumn{{4}}{{l}}{{\\textit{{{DATASET_NAMES[dataset]}}}}} \\\\")
        for method in methods:
            found = [r for r in rows if r["dataset"] == dataset and r["method"] == method]
            if not found:
                continue
            r = found[0]
            body.append(
                f"{METHOD_NAMES[method]} & {fmt(r['acc_mean'])} $\\pm$ {fmt(r['acc_ci95'])} & "
                f"{fmt(r['balanced_acc_mean'])} & {fmt(r['bytes_mean'], 0)} \\\\"
            )
    return table(
        "Real image datasets under heterogeneous quantum readout.",
        "tab:real-image-main",
        "lccc",
        "Method & Acc. (95\\% CI) & Bal. acc. & Bytes",
        body,
    )


def shot_table(rows: list[dict[str, str]]) -> str:
    methods = ["qproto_full", "qproto_proto", "no_schema", "wrong_schema", "fedavg_forced"]
    body = []
    for shot in ["32", "64", "128", "256", "1024"]:
        vals = [shot]
        for method in methods:
            found = [r for r in rows if r["shots"] == shot and r["method"] == method]
            vals.append(fmt(found[0]["acc_mean"]) if found else "--")
        body.append(" & ".join(vals) + " \\\\")
    return table(
        "CIFAR-4 shot-noise sweep.",
        "tab:real-cifar-shot",
        "l" + "c" * len(methods),
        "Shots & Full & Proto & No schema & Wrong & FedAvg",
        body,
    )


def comm_table(rows: list[dict[str, str]]) -> str:
    by_bytes: dict[str, dict[str, str]] = {}
    for r in rows:
        by_bytes.setdefault(r["bytes_mean"], {})[r["family"]] = r["acc_mean"]
    body = []
    for b in sorted(by_bytes, key=lambda x: float(x)):
        body.append(f"{fmt(b, 0)} & {fmt(by_bytes[b].get('proto', 0.0))} & {fmt(by_bytes[b].get('hop', 0.0))} \\\\")
    return table(
        "CIFAR-4 matched communication-budget curve.",
        "tab:real-cifar-comm",
        "lcc",
        "Bytes & Prototype & HOP",
        body,
    )


def main() -> None:
    ap = argparse.ArgumentParser("Export real-data LaTeX tables")
    ap.add_argument("--runs-dir", type=str, default="runs")
    ap.add_argument("--out", type=str, default="paper_tables_real.tex")
    args = ap.parse_args()

    runs = Path(args.runs_dir)
    blocks = [
        real_image_table(read_csv(runs / "real_image_dataset_tables.csv")),
        shot_table(read_csv(runs / "real_cifar4_shot_sweep.csv")),
        comm_table(read_csv(runs / "real_cifar4_comm_budget.csv")),
    ]
    Path(args.out).write_text("\n".join(blocks), encoding="utf-8")
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()

