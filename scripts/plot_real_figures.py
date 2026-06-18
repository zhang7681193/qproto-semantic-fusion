from __future__ import annotations

import argparse
import csv
from pathlib import Path


PALETTE = {
    "qproto_hop": "#2f7d5c",
    "qproto_full": "#3f6fb5",
    "qproto_proto": "#6b5ca5",
    "no_schema": "#c27a2c",
    "forced_canonical": "#a04f7a",
    "wrong_schema": "#b54a43",
    "fedavg_forced": "#666666",
    "proto": "#6b5ca5",
    "hop": "#2f7d5c",
}


LABELS = {
    "qproto_hop": "QProto-HOP",
    "qproto_full": "Full + shrink.",
    "qproto_proto": "Prototype",
    "no_schema": "No schema",
    "forced_canonical": "Forced",
    "wrong_schema": "Wrong",
    "fedavg_forced": "FedAvg",
    "mnist4": "MNIST-4",
    "fashion4": "Fashion-4",
    "cifar4": "CIFAR-4",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def esc(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def write_grouped_bars(rows: list[dict[str, str]], out: Path) -> None:
    datasets = ["mnist4", "fashion4", "cifar4"]
    methods = ["qproto_hop", "qproto_proto", "no_schema", "forced_canonical", "wrong_schema", "fedavg_forced"]
    lookup = {(r["dataset"], r["method"]): float(r["acc_mean"]) for r in rows}
    ci = {(r["dataset"], r["method"]): float(r["acc_ci95"]) for r in rows}

    width, height = 1040, 620
    ml, mr, mt, mb = 82, 36, 88, 118
    pw, ph = width - ml - mr, height - mt - mb
    y_max = 0.85

    def y(v: float) -> float:
        return mt + ph * (1 - v / y_max)

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        f'<text x="{ml}" y="38" font-family="Arial" font-size="24" font-weight="700">Real image datasets</text>',
        f'<text x="{ml}" y="64" font-family="Arial" font-size="14" fill="#555">5 seeds; heterogeneous quantum readout; first four classes.</text>',
    ]
    for t in range(6):
        v = y_max * t / 5
        yy = y(v)
        parts.append(f'<line x1="{ml}" y1="{yy:.2f}" x2="{width-mr}" y2="{yy:.2f}" stroke="#e8e8e8"/>')
        parts.append(f'<text x="{ml-10}" y="{yy+4:.2f}" text-anchor="end" font-family="Arial" font-size="12" fill="#666">{v:.2f}</text>')
    parts.append(f'<line x1="{ml}" y1="{mt+ph}" x2="{width-mr}" y2="{mt+ph}" stroke="#333"/>')
    parts.append(f'<line x1="{ml}" y1="{mt}" x2="{ml}" y2="{mt+ph}" stroke="#333"/>')

    group_w = pw / len(datasets)
    bar_w = min(22, group_w / (len(methods) + 2))
    for gi, dataset in enumerate(datasets):
        center = ml + group_w * (gi + 0.5)
        start = center - bar_w * len(methods) / 2
        for mi, method in enumerate(methods):
            val = lookup.get((dataset, method), 0.0)
            err = ci.get((dataset, method), 0.0)
            x = start + mi * bar_w
            yy = y(val)
            parts.append(f'<rect x="{x:.2f}" y="{yy:.2f}" width="{bar_w-2:.2f}" height="{mt+ph-yy:.2f}" rx="2" fill="{PALETTE[method]}"/>')
            parts.append(f'<line x1="{x+(bar_w-2)/2:.2f}" y1="{y(min(y_max,val+err)):.2f}" x2="{x+(bar_w-2)/2:.2f}" y2="{y(max(0,val-err)):.2f}" stroke="#222" stroke-width="1"/>')
        parts.append(f'<text x="{center:.2f}" y="{mt+ph+32}" text-anchor="middle" font-family="Arial" font-size="14" font-weight="700">{LABELS[dataset]}</text>')

    lx, ly = ml, height - 54
    for i, method in enumerate(methods):
        x = lx + i * 150
        parts.append(f'<rect x="{x}" y="{ly}" width="12" height="12" fill="{PALETTE[method]}"/>')
        parts.append(f'<text x="{x+18}" y="{ly+11}" font-family="Arial" font-size="12" fill="#333">{esc(LABELS[method])}</text>')
    parts.append("</svg>")
    out.write_text("\n".join(parts), encoding="utf-8")


def write_line_chart(rows: list[dict[str, str]], out: Path, *, title: str, x_field: str, series_field: str, x_label: str) -> None:
    width, height = 940, 560
    ml, mr, mt, mb = 80, 36, 82, 82
    pw, ph = width - ml - mr, height - mt - mb
    series = sorted({r[series_field] for r in rows})
    xs = sorted({float(r[x_field]) for r in rows})
    y_max = min(0.85, max(float(r["acc_mean"]) + float(r.get("acc_ci95", 0) or 0) for r in rows) * 1.18)
    y_max = max(0.4, y_max)

    def x_pos(v: float) -> float:
        if len(xs) == 1:
            return ml + pw / 2
        return ml + (v - min(xs)) / (max(xs) - min(xs)) * pw

    def y_pos(v: float) -> float:
        return mt + ph * (1 - v / y_max)

    lookup = {(r[series_field], float(r[x_field])): float(r["acc_mean"]) for r in rows}
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        f'<text x="{ml}" y="36" font-family="Arial" font-size="23" font-weight="700">{esc(title)}</text>',
        f'<text x="{ml}" y="{height-24}" font-family="Arial" font-size="13" fill="#333">{esc(x_label)}</text>',
    ]
    for t in range(6):
        v = y_max * t / 5
        yy = y_pos(v)
        parts.append(f'<line x1="{ml}" y1="{yy:.2f}" x2="{width-mr}" y2="{yy:.2f}" stroke="#e8e8e8"/>')
        parts.append(f'<text x="{ml-10}" y="{yy+4:.2f}" text-anchor="end" font-family="Arial" font-size="12" fill="#666">{v:.2f}</text>')
    parts.append(f'<line x1="{ml}" y1="{mt+ph}" x2="{width-mr}" y2="{mt+ph}" stroke="#333"/>')
    parts.append(f'<line x1="{ml}" y1="{mt}" x2="{ml}" y2="{mt+ph}" stroke="#333"/>')
    for xv in xs:
        xp = x_pos(xv)
        parts.append(f'<text x="{xp:.2f}" y="{mt+ph+24}" text-anchor="middle" font-family="Arial" font-size="12">{xv:.0f}</text>')
    for si, s in enumerate(series):
        pts = [(x_pos(xv), y_pos(lookup[(s, xv)])) for xv in xs if (s, xv) in lookup]
        color = PALETTE.get(s, PALETTE.get(str(s).split("_")[0], "#4a6d8c"))
        if len(pts) > 1:
            parts.append('<polyline fill="none" stroke="{}" stroke-width="2.5" points="{}"/>'.format(color, " ".join(f"{x:.2f},{y:.2f}" for x, y in pts)))
        for x, y in pts:
            parts.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="4" fill="{color}"/>')
        lx, ly = ml + si * 150, 58
        label = LABELS.get(s, s)
        parts.append(f'<rect x="{lx}" y="{ly}" width="12" height="12" fill="{color}"/>')
        parts.append(f'<text x="{lx+18}" y="{ly+11}" font-family="Arial" font-size="12">{esc(label)}</text>')
    parts.append("</svg>")
    out.write_text("\n".join(parts), encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser("Plot real-data SVG figures")
    ap.add_argument("--runs-dir", type=str, default="runs")
    ap.add_argument("--out-dir", type=str, default="figures")
    args = ap.parse_args()
    runs = Path(args.runs_dir)
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)

    image_rows = read_csv(runs / "real_image_dataset_tables.csv")
    write_grouped_bars(image_rows, out / "real_image_dataset_accuracy.svg")

    shot_rows = read_csv(runs / "real_cifar4_shot_sweep.csv")
    write_line_chart(
        shot_rows,
        out / "real_cifar4_shot_sweep.svg",
        title="CIFAR-4 shot-noise sweep",
        x_field="shots",
        series_field="method",
        x_label="Measurement shots",
    )

    comm_rows = read_csv(runs / "real_cifar4_comm_budget.csv")
    write_line_chart(
        comm_rows,
        out / "real_cifar4_comm_budget.svg",
        title="CIFAR-4 matched communication budget",
        x_field="bytes_mean",
        series_field="family",
        x_label="Bytes per client per round",
    )
    print(f"Wrote real figures to {out}")


if __name__ == "__main__":
    main()

