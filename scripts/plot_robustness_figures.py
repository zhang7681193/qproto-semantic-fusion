from __future__ import annotations

import argparse
import csv
import re
from dataclasses import dataclass
from pathlib import Path


PALETTE = {
    "qproto_full": "#2f7d5c",
    "qproto_hop": "#3f6fb5",
    "qproto_proto": "#6b5ca5",
    "no_schema": "#c27a2c",
    "forced_canonical": "#a04f7a",
    "wrong_schema": "#b54a43",
    "fedavg_forced": "#666666",
    "fedprox_forced": "#4f4f4f",
}


LABELS = {
    "qproto_full": "QProto-HOP",
    "qproto_hop": "HOP",
    "qproto_proto": "Prototype",
    "no_schema": "No schema",
    "forced_canonical": "Forced canonical",
    "wrong_schema": "Wrong schema",
    "fedavg_forced": "FedAvg forced",
    "fedprox_forced": "FedProx forced",
}


@dataclass(frozen=True)
class Series:
    key: str
    points: list[tuple[float, float]]


def esc(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def line_chart(
    series: list[Series],
    *,
    title: str,
    subtitle: str,
    x_label: str,
    y_label: str,
    out: Path,
    x_tick_labels: dict[float, str] | None = None,
    y_min: float = 0.0,
    y_max: float = 0.8,
) -> None:
    width = 980
    height = 620
    margin_l = 88
    margin_r = 220
    margin_t = 92
    margin_b = 86
    plot_w = width - margin_l - margin_r
    plot_h = height - margin_t - margin_b
    all_x = sorted({x for s in series for x, _ in s.points})
    x_min = min(all_x) if all_x else 0.0
    x_max = max(all_x) if all_x else 1.0
    if x_min == x_max:
        x_max = x_min + 1.0

    def x_pos(v: float) -> float:
        return margin_l + (v - x_min) / (x_max - x_min) * plot_w

    def y_pos(v: float) -> float:
        return margin_t + (1.0 - (v - y_min) / (y_max - y_min)) * plot_h

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        f'<text x="{margin_l}" y="38" font-family="Arial, sans-serif" font-size="24" font-weight="700" fill="#111111">{esc(title)}</text>',
        f'<text x="{margin_l}" y="66" font-family="Arial, sans-serif" font-size="14" fill="#555555">{esc(subtitle)}</text>',
        f'<text x="{margin_l + plot_w / 2}" y="{height - 24}" text-anchor="middle" font-family="Arial, sans-serif" font-size="14" fill="#333333">{esc(x_label)}</text>',
        f'<text x="22" y="{margin_t + plot_h / 2}" transform="rotate(-90 22 {margin_t + plot_h / 2})" font-family="Arial, sans-serif" font-size="14" fill="#333333">{esc(y_label)}</text>',
    ]

    for tick in range(0, 6):
        yv = y_min + (y_max - y_min) * tick / 5
        y = y_pos(yv)
        parts.append(f'<line x1="{margin_l}" y1="{y:.2f}" x2="{margin_l + plot_w}" y2="{y:.2f}" stroke="#e8e8e8" stroke-width="1"/>')
        parts.append(f'<text x="{margin_l - 12}" y="{y + 4:.2f}" text-anchor="end" font-family="Arial, sans-serif" font-size="12" fill="#666666">{yv:.2f}</text>')

    x_tick_labels = x_tick_labels or {x: str(int(x) if float(x).is_integer() else x) for x in all_x}
    for xv in all_x:
        x = x_pos(xv)
        parts.append(f'<line x1="{x:.2f}" y1="{margin_t}" x2="{x:.2f}" y2="{margin_t + plot_h}" stroke="#f1f1f1" stroke-width="1"/>')
        parts.append(f'<text x="{x:.2f}" y="{margin_t + plot_h + 25}" text-anchor="middle" font-family="Arial, sans-serif" font-size="12" fill="#666666">{esc(x_tick_labels.get(xv, str(xv)))}</text>')

    parts.append(f'<line x1="{margin_l}" y1="{margin_t + plot_h}" x2="{margin_l + plot_w}" y2="{margin_t + plot_h}" stroke="#333333" stroke-width="1.2"/>')
    parts.append(f'<line x1="{margin_l}" y1="{margin_t}" x2="{margin_l}" y2="{margin_t + plot_h}" stroke="#333333" stroke-width="1.2"/>')

    legend_x = margin_l + plot_w + 36
    legend_y = margin_t + 6
    for i, s in enumerate(series):
        color = PALETTE.get(s.key, "#4a6d8c")
        pts = " ".join(f"{x_pos(x):.2f},{y_pos(y):.2f}" for x, y in s.points)
        parts.append(f'<polyline points="{pts}" fill="none" stroke="{color}" stroke-width="3"/>')
        for x, y in s.points:
            parts.append(f'<circle cx="{x_pos(x):.2f}" cy="{y_pos(y):.2f}" r="4.5" fill="{color}" stroke="#ffffff" stroke-width="1"/>')
        ly = legend_y + i * 28
        parts.append(f'<line x1="{legend_x}" y1="{ly}" x2="{legend_x + 24}" y2="{ly}" stroke="{color}" stroke-width="3"/>')
        parts.append(f'<circle cx="{legend_x + 12}" cy="{ly}" r="4" fill="{color}"/>')
        parts.append(f'<text x="{legend_x + 34}" y="{ly + 4}" font-family="Arial, sans-serif" font-size="13" fill="#222222">{esc(LABELS.get(s.key, s.key))}</text>')

    parts.append("</svg>")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(parts), encoding="utf-8")


def from_table(rows: list[dict[str, str]], x_field: str, methods: list[str], label_map: dict[str, float] | None = None) -> list[Series]:
    out = []
    for method in methods:
        pts = []
        for r in rows:
            if r.get("method") != method:
                continue
            x_raw = r[x_field]
            x = label_map[x_raw] if label_map else float(x_raw)
            pts.append((x, float(r["acc_mean"])))
        if pts:
            out.append(Series(method, sorted(pts)))
    return out


def main() -> None:
    ap = argparse.ArgumentParser("Generate robustness SVG figures")
    ap.add_argument("--runs-dir", type=str, default="runs")
    ap.add_argument("--out-dir", type=str, default="figures")
    args = ap.parse_args()

    runs_dir = Path(args.runs_dir)
    out_dir = Path(args.out_dir)

    mismatch_path = runs_dir / "mismatch_by_shift.csv"
    if mismatch_path.exists():
        rows = read_csv(mismatch_path)
        line_chart(
            from_table(rows, "wrong_shift", ["qproto_full", "forced_canonical", "no_schema", "wrong_schema"]),
            title="Schema mismatch severity",
            subtitle="Correct protocol remains stable while corrupted schema aggregation degrades.",
            x_label="Wrong-schema shift",
            y_label="Final accuracy",
            out=out_dir / "schema_mismatch_sweep.svg",
            y_max=0.72,
        )

    noise_path = runs_dir / "noise_by_level.csv"
    if noise_path.exists():
        rows = read_csv(noise_path)
        noise_map = {"low": 0.0, "mid": 1.0, "high": 2.0}
        line_chart(
            from_table(rows, "noise", ["qproto_full", "qproto_proto", "no_schema", "wrong_schema", "fedavg_forced"], noise_map),
            title="Readout and hardware-noise robustness",
            subtitle="QProto-HOP degrades under stronger noise but keeps a margin over schema-incorrect controls.",
            x_label="Noise level",
            y_label="Final accuracy",
            out=out_dir / "noise_robustness_sweep.svg",
            x_tick_labels={0.0: "low", 1.0: "mid", 2.0: "high"},
            y_max=0.72,
        )

    anchor_rows = []
    summary_path = runs_dir / "summary.csv"
    if summary_path.exists():
        for r in read_csv(summary_path):
            if re.match(r"anchor\d+_seed\d+$", r["run"]):
                anchor_rows.append(r)
    if anchor_rows:
        grouped: dict[tuple[str, str], list[float]] = {}
        for r in anchor_rows:
            anchor = r["run"].split("_seed")[0].replace("anchor", "")
            grouped.setdefault((anchor, r["method"]), []).append(float(r["final_acc"]))
        rows = [
            {"anchor": a, "method": m, "acc_mean": str(sum(v) / len(v))}
            for (a, m), v in grouped.items()
        ]
        line_chart(
            from_table(rows, "anchor", ["qproto_full", "qproto_hop", "qproto_proto", "no_schema", "wrong_schema"]),
            title="Public-anchor normalization sensitivity",
            subtitle="Naive anchor center/scale normalization can weaken correct-schema aggregation.",
            x_label="Anchor size",
            y_label="Final accuracy",
            out=out_dir / "anchor_sensitivity_sweep.svg",
            y_max=0.72,
        )

    print(f"Wrote robustness figures to {out_dir}")


if __name__ == "__main__":
    main()

