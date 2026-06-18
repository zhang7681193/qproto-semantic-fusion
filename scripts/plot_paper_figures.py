from __future__ import annotations

import argparse
import csv
import math
import re
import statistics as st
from dataclasses import dataclass
from pathlib import Path


PALETTE = {
    "qproto_full": "#2f7d5c",
    "qproto_hop": "#3f6fb5",
    "qproto_proto": "#6b5ca5",
    "proto_low": "#6b5ca5",
    "hop_low": "#3f6fb5",
    "proto_high": "#8a6f2a",
    "hop_high": "#2f7d5c",
    "no_schema": "#c27a2c",
    "forced_canonical": "#a04f7a",
    "wrong_schema": "#b54a43",
    "fedavg_forced": "#666666",
    "fedprox_forced": "#4f4f4f",
    "local_only": "#2b2b2b",
    "classical_kernel": "#3b8c8c",
    "centralized_kernel": "#8a8a8a",
    "centralized_qproto": "#5c8a72",
}


@dataclass(frozen=True)
class BarItem:
    key: str
    label: str
    mean: float
    std: float
    aux: float | None = None


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def mean(xs: list[float]) -> float:
    return st.mean(xs) if xs else 0.0


def std(xs: list[float]) -> float:
    return st.stdev(xs) if len(xs) > 1 else 0.0


def summarize(
    rows: list[dict[str, str]],
    *,
    predicate,
    order: list[str],
    labels: dict[str, str] | None = None,
) -> list[BarItem]:
    labels = labels or {}
    rr = [r for r in rows if predicate(r)]
    out: list[BarItem] = []
    for key in order:
        xs = [float(r["final_acc"]) for r in rr if r["method"] == key]
        if not xs:
            continue
        ds = [float(r.get("distortion_proxy") or 0.0) for r in rr if r["method"] == key]
        out.append(BarItem(key=key, label=labels.get(key, key), mean=mean(xs), std=std(xs), aux=mean(ds)))
    return out


def iso_items(rows: list[dict[str, str]]) -> list[BarItem]:
    def variant(run: str) -> str | None:
        m = re.match(r"iso_(proto_low|hop_low|proto_high|hop_high)_seed\d+$", run)
        return m.group(1) if m else None

    labels = {
        "proto_low": "Proto low",
        "hop_low": "HOP low",
        "proto_high": "Proto high",
        "hop_high": "HOP high",
    }
    out: list[BarItem] = []
    for key in ["proto_low", "hop_low", "proto_high", "hop_high"]:
        rr = [r for r in rows if variant(r["run"]) == key]
        xs = [float(r["final_acc"]) for r in rr]
        bytes_ = [float(r["bytes_per_client_round"]) for r in rr]
        if xs:
            out.append(BarItem(key=key, label=labels[key], mean=mean(xs), std=std(xs), aux=mean(bytes_)))
    return out


def esc(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def svg_bar_chart(
    items: list[BarItem],
    *,
    title: str,
    subtitle: str,
    y_label: str,
    out: Path,
    y_max: float | None = None,
    aux_label: str | None = None,
) -> None:
    width = 980
    height = 620
    margin_l = 88
    margin_r = 36
    margin_t = 92
    margin_b = 118
    plot_w = width - margin_l - margin_r
    plot_h = height - margin_t - margin_b
    y_max = y_max or min(1.0, max(0.1, max((x.mean + x.std for x in items), default=0.8) * 1.18))

    def x_center(i: int) -> float:
        return margin_l + (i + 0.5) * plot_w / len(items)

    def y_pos(v: float) -> float:
        return margin_t + plot_h * (1.0 - v / y_max)

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        f'<text x="{margin_l}" y="38" font-family="Arial, sans-serif" font-size="24" font-weight="700" fill="#111111">{esc(title)}</text>',
        f'<text x="{margin_l}" y="66" font-family="Arial, sans-serif" font-size="14" fill="#555555">{esc(subtitle)}</text>',
        f'<text x="22" y="{margin_t + plot_h / 2}" transform="rotate(-90 22 {margin_t + plot_h / 2})" font-family="Arial, sans-serif" font-size="14" fill="#333333">{esc(y_label)}</text>',
    ]

    for tick in range(0, 6):
        v = y_max * tick / 5
        y = y_pos(v)
        parts.append(f'<line x1="{margin_l}" y1="{y:.2f}" x2="{width - margin_r}" y2="{y:.2f}" stroke="#e8e8e8" stroke-width="1"/>')
        parts.append(f'<text x="{margin_l - 12}" y="{y + 4:.2f}" text-anchor="end" font-family="Arial, sans-serif" font-size="12" fill="#666666">{v:.2f}</text>')

    parts.append(f'<line x1="{margin_l}" y1="{margin_t + plot_h}" x2="{width - margin_r}" y2="{margin_t + plot_h}" stroke="#333333" stroke-width="1.2"/>')
    parts.append(f'<line x1="{margin_l}" y1="{margin_t}" x2="{margin_l}" y2="{margin_t + plot_h}" stroke="#333333" stroke-width="1.2"/>')

    bar_w = min(86, plot_w / len(items) * 0.58)
    for i, item in enumerate(items):
        cx = x_center(i)
        top = y_pos(item.mean)
        bottom = margin_t + plot_h
        color = PALETTE.get(item.key, "#4a6d8c")
        parts.append(f'<rect x="{cx - bar_w / 2:.2f}" y="{top:.2f}" width="{bar_w:.2f}" height="{bottom - top:.2f}" rx="3" fill="{color}"/>')
        err_top = y_pos(min(y_max, item.mean + item.std))
        err_bot = y_pos(max(0.0, item.mean - item.std))
        parts.append(f'<line x1="{cx:.2f}" y1="{err_top:.2f}" x2="{cx:.2f}" y2="{err_bot:.2f}" stroke="#222222" stroke-width="1.6"/>')
        parts.append(f'<line x1="{cx - 12:.2f}" y1="{err_top:.2f}" x2="{cx + 12:.2f}" y2="{err_top:.2f}" stroke="#222222" stroke-width="1.6"/>')
        parts.append(f'<line x1="{cx - 12:.2f}" y1="{err_bot:.2f}" x2="{cx + 12:.2f}" y2="{err_bot:.2f}" stroke="#222222" stroke-width="1.6"/>')
        parts.append(f'<text x="{cx:.2f}" y="{top - 10:.2f}" text-anchor="middle" font-family="Arial, sans-serif" font-size="13" font-weight="700" fill="#222222">{item.mean:.3f}</text>')
        label_y = bottom + 28
        parts.append(f'<text x="{cx:.2f}" y="{label_y:.2f}" text-anchor="middle" font-family="Arial, sans-serif" font-size="13" fill="#222222">{esc(item.label)}</text>')
        if aux_label and item.aux is not None:
            aux_text = f"{aux_label}: {item.aux:.3f}" if item.aux < 10 else f"{aux_label}: {item.aux:.0f}"
            parts.append(f'<text x="{cx:.2f}" y="{label_y + 22:.2f}" text-anchor="middle" font-family="Arial, sans-serif" font-size="11" fill="#666666">{esc(aux_text)}</text>')

    parts.append("</svg>")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(parts), encoding="utf-8")


def markdown_table(items: list[BarItem], *, aux_label: str | None = None) -> str:
    header = "| Variant | Accuracy mean | Accuracy std |"
    sep = "|---|---:|---:|"
    if aux_label:
        header += f" {aux_label} |"
        sep += "---:|"
    lines = [header, sep]
    for item in items:
        line = f"| {item.label} | {item.mean:.4f} | {item.std:.4f} |"
        if aux_label:
            aux = item.aux if item.aux is not None and math.isfinite(item.aux) else 0.0
            line = f"| {item.label} | {item.mean:.4f} | {item.std:.4f} | {aux:.4f} |"
        lines.append(line)
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser("Generate paper-style SVG figures for QProto-HOP")
    ap.add_argument("--summary", type=str, default="runs/summary.csv")
    ap.add_argument("--out-dir", type=str, default="figures")
    args = ap.parse_args()

    rows = read_rows(Path(args.summary))
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    schema = summarize(
        rows,
        predicate=lambda r: r["run"].startswith("schema_triptych"),
        order=["qproto_full", "no_schema", "forced_canonical", "wrong_schema"],
        labels={
            "qproto_full": "QProto-HOP",
            "no_schema": "No schema",
            "forced_canonical": "Forced canonical",
            "wrong_schema": "Wrong schema",
        },
    )
    hop = summarize(
        rows,
        predicate=lambda r: re.match(r"hop_cov_seed\d+$", r["run"]) is not None,
        order=["qproto_full", "qproto_hop", "qproto_proto", "wrong_schema", "no_schema"],
        labels={
            "qproto_full": "Full",
            "qproto_hop": "HOP",
            "qproto_proto": "Prototype",
            "wrong_schema": "Wrong schema",
            "no_schema": "No schema",
        },
    )
    iso = iso_items(rows)
    baseline = summarize(
        rows,
        predicate=lambda r: re.match(r"baseline_suite_seed\d+$", r["run"]) is not None,
        order=[
            "centralized_kernel",
            "classical_kernel",
            "centralized_qproto",
            "local_only",
            "qproto_full",
            "qproto_proto",
            "no_schema",
            "forced_canonical",
            "fedavg_forced",
            "fedprox_forced",
            "wrong_schema",
        ],
        labels={
            "centralized_kernel": "Centralized",
            "classical_kernel": "Classical kernel",
            "centralized_qproto": "Centralized Q",
            "local_only": "Local only",
            "qproto_full": "QProto-HOP",
            "qproto_proto": "Prototype",
            "no_schema": "No schema",
            "forced_canonical": "Forced canonical",
            "fedavg_forced": "FedAvg forced",
            "fedprox_forced": "FedProx forced",
            "wrong_schema": "Wrong schema",
        },
    )

    svg_bar_chart(
        schema,
        title="Schema comparability under heterogeneous readout",
        subtitle="Correct protocol vs no/wrong/forced schema controls; 3 seeds.",
        y_label="Final accuracy",
        out=out_dir / "schema_triptych_accuracy.svg",
        y_max=0.8,
        aux_label="dist",
    )
    svg_bar_chart(
        hop,
        title="High-order outer-product prototypes",
        subtitle="Covariance-structured task where first-order prototypes are weak; 3 seeds.",
        y_label="Final accuracy",
        out=out_dir / "hop_ablation_accuracy.svg",
        y_max=0.9,
        aux_label="dist",
    )
    svg_bar_chart(
        baseline,
        title="Expanded baseline suite",
        subtitle="Classical input-space references and heterogeneous-readout baselines; 3 seeds.",
        y_label="Final accuracy",
        out=out_dir / "baseline_suite_accuracy.svg",
        y_max=1.05,
        aux_label="dist",
    )
    svg_bar_chart(
        iso,
        title="Iso-communication prototype vs HOP",
        subtitle="Low and high communication budgets matched in bytes/client/round; 3 seeds.",
        y_label="Final accuracy",
        out=out_dir / "iso_communication_accuracy.svg",
        y_max=0.9,
        aux_label="bytes",
    )

    summary = [
        "# QProto-HOP Figure Summary",
        "",
        "## Schema Triptych",
        "",
        markdown_table(schema, aux_label="Distortion"),
        "",
        "## HOP Ablation",
        "",
        markdown_table(hop, aux_label="Distortion"),
        "",
        "## Expanded Baseline Suite",
        "",
        markdown_table(baseline, aux_label="Distortion"),
        "",
        "## Iso-Communication",
        "",
        markdown_table(iso, aux_label="Bytes"),
        "",
        "Generated SVG files:",
        "",
        "- `schema_triptych_accuracy.svg`",
        "- `baseline_suite_accuracy.svg`",
        "- `hop_ablation_accuracy.svg`",
        "- `iso_communication_accuracy.svg`",
    ]
    (out_dir / "figure_summary.md").write_text("\n".join(summary) + "\n", encoding="utf-8")
    print(f"Wrote figures to {out_dir}")


if __name__ == "__main__":
    main()

