from __future__ import annotations

import argparse
import csv
from pathlib import Path


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def fmt(x: str | float, nd: int = 3) -> str:
    try:
        return f"{float(x):.{nd}f}"
    except Exception:
        return str(x)


def table_environment(caption: str, label: str, columns: str, header: str, rows: list[str]) -> str:
    body = "\n".join(rows)
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
            body,
            "\\bottomrule",
            "\\end{tabular}",
            "\\end{table}",
            "",
        ]
    )


def baseline_table(rows: list[dict[str, str]]) -> str:
    order = [
        "centralized_kernel",
        "classical_kernel",
        "local_only",
        "qproto_full",
        "centralized_qproto",
        "qproto_hop",
        "qproto_proto",
        "no_schema",
        "forced_canonical",
        "fedavg_forced",
        "fedprox_forced",
        "wrong_schema",
    ]
    names = {
        "centralized_kernel": "Centralized kernel",
        "classical_kernel": "Classical kernel",
        "local_only": "Local only",
        "qproto_full": "QProto-HOP",
        "centralized_qproto": "Centralized QProto",
        "qproto_hop": "QProto-HOP w/o shrink.",
        "qproto_proto": "QProto prototype",
        "no_schema": "No schema",
        "forced_canonical": "Forced canonical",
        "fedavg_forced": "FedAvg forced",
        "fedprox_forced": "FedProx forced",
        "wrong_schema": "Wrong schema",
    }
    by_method = {r["method"]: r for r in rows if r.get("prefix") == "baseline_suite"}
    body = []
    for method in order:
        r = by_method.get(method)
        if not r:
            continue
        ci = fmt(r["acc_ci95"])
        body.append(
            f"{names[method]} & {fmt(r['acc_mean'])} $\\pm$ {ci} & {fmt(r['balanced_acc_mean'])} & {fmt(r['bytes_mean'], 0)} \\\\"
        )
    return table_environment(
        "Expanded baseline suite on the default heterogeneous-readout benchmark.",
        "tab:baseline-suite",
        "lccc",
        "Method & Acc. (95\\% CI) & Bal. acc. & Bytes",
        body,
    )


def simple_csv_table(
    rows: list[dict[str, str]],
    *,
    caption: str,
    label: str,
    x_field: str,
    x_name: str,
    methods: list[str],
    names: dict[str, str],
) -> str:
    x_values = []
    for r in rows:
        if r[x_field] not in x_values:
            x_values.append(r[x_field])
    body = []
    for x in x_values:
        parts = [x]
        for method in methods:
            found = [r for r in rows if r[x_field] == x and r["method"] == method]
            parts.append(fmt(found[0]["acc_mean"]) if found else "--")
        body.append(" & ".join(parts) + " \\\\")
    header = " & ".join([x_name] + [names.get(m, m) for m in methods])
    return table_environment(caption, label, "l" + "c" * len(methods), header, body)


def main() -> None:
    ap = argparse.ArgumentParser("Export LaTeX tables for QProto-HOP results")
    ap.add_argument("--runs-dir", type=str, default="runs")
    ap.add_argument("--out", type=str, default="paper_tables.tex")
    args = ap.parse_args()

    runs_dir = Path(args.runs_dir)
    blocks = []

    baseline_stats = read_csv(runs_dir / "baseline_statistics.csv")
    if baseline_stats:
        blocks.append(baseline_table(baseline_stats))

    mismatch = read_csv(runs_dir / "mismatch_by_shift.csv")
    if mismatch:
        blocks.append(
            simple_csv_table(
                mismatch,
                caption="Schema mismatch severity sweep.",
                label="tab:schema-mismatch",
                x_field="wrong_shift",
                x_name="Shift",
                methods=["qproto_full", "forced_canonical", "no_schema", "wrong_schema"],
                names={
                    "qproto_full": "QProto-HOP",
                    "forced_canonical": "Forced",
                    "no_schema": "No schema",
                    "wrong_schema": "Wrong",
                },
            )
        )

    noise = read_csv(runs_dir / "noise_by_level.csv")
    if noise:
        blocks.append(
            simple_csv_table(
                noise,
                caption="Readout and hardware-noise robustness sweep.",
                label="tab:noise-robustness",
                x_field="noise",
                x_name="Noise",
                methods=["qproto_full", "qproto_proto", "no_schema", "wrong_schema", "fedavg_forced"],
                names={
                    "qproto_full": "QProto-HOP",
                    "qproto_proto": "Proto",
                    "no_schema": "No schema",
                    "wrong_schema": "Wrong",
                    "fedavg_forced": "FedAvg",
                },
            )
        )

    noniid = read_csv(runs_dir / "noniid_sensitivity.csv")
    if noniid:
        blocks.append(
            simple_csv_table(
                noniid,
                caption="Dirichlet label-skew sensitivity.",
                label="tab:noniid-sensitivity",
                x_field="alpha",
                x_name="Alpha",
                methods=["qproto_full", "qproto_proto", "no_schema", "wrong_schema", "fedavg_forced"],
                names={
                    "qproto_full": "QProto-HOP",
                    "qproto_proto": "Proto",
                    "no_schema": "No schema",
                    "wrong_schema": "Wrong",
                    "fedavg_forced": "FedAvg",
                },
            )
        )

    comm = read_csv(runs_dir / "comm_budget_curve.csv")
    if comm:
        # Pivot rows by matched bytes so the table reads as a communication curve.
        by_bytes: dict[str, dict[str, str]] = {}
        for r in comm:
            by_bytes.setdefault(r["bytes_mean"], {})[r["variant"]] = r["acc_mean"]
        body = []
        for b in sorted(by_bytes, key=lambda x: float(x)):
            body.append(f"{fmt(b, 0)} & {fmt(by_bytes[b].get('proto', '--'))} & {fmt(by_bytes[b].get('hop', '--'))} \\\\")
        blocks.append(
            table_environment(
                "Matched communication-budget curve on the high-order benchmark.",
                "tab:comm-budget",
                "lcc",
                "Bytes & Prototype & HOP",
                body,
            )
        )

    out = Path(args.out)
    out.write_text("\n".join(blocks), encoding="utf-8")
    print(f"Wrote LaTeX tables to {out}")


if __name__ == "__main__":
    main()

