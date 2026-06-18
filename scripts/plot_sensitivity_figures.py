from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path


PALETTE = {
    "qproto_full": "#2f7d5c",
    "qproto_hop": "#3f6fb5",
    "qproto_proto": "#6b5ca5",
    "no_schema": "#c27a2c",
    "wrong_schema": "#b54a43",
    "fedavg_forced": "#666666",
    "fedprox_forced": "#4f4f4f",
    "proto": "#6b5ca5",
    "hop": "#3f6fb5",
}

LABELS = {
    "qproto_full": "QProto-HOP",
    "qproto_hop": "HOP",
    "qproto_proto": "Prototype",
    "no_schema": "No schema",
    "wrong_schema": "Wrong schema",
    "fedavg_forced": "FedAvg",
    "fedprox_forced": "FedProx",
    "proto": "Prototype",
    "hop": "HOP",
}


@dataclass(frozen=True)
class Series:
    key: str
    points: list[tuple[float, float]]


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def esc(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def chart(series: list[Series], *, title: str, subtitle: str, x_label: str, out: Path, y_max: float = 0.9) -> None:
    width, height = 980, 620
    ml, mr, mt, mb = 88, 220, 92, 86
    pw, ph = width - ml - mr, height - mt - mb
    xs = sorted({x for s in series for x, _ in s.points})
    if not xs:
        return
    xmin, xmax = min(xs), max(xs)
    if xmin == xmax:
        xmax = xmin + 1

    def xp(x: float) -> float:
        return ml + (x - xmin) / (xmax - xmin) * pw

    def yp(y: float) -> float:
        return mt + (1 - y / y_max) * ph

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#fff"/>',
        f'<text x="{ml}" y="38" font-family="Arial, sans-serif" font-size="24" font-weight="700">{esc(title)}</text>',
        f'<text x="{ml}" y="66" font-family="Arial, sans-serif" font-size="14" fill="#555">{esc(subtitle)}</text>',
        f'<text x="{ml + pw / 2}" y="{height - 24}" text-anchor="middle" font-family="Arial, sans-serif" font-size="14">{esc(x_label)}</text>',
        f'<text x="22" y="{mt + ph / 2}" transform="rotate(-90 22 {mt + ph / 2})" font-family="Arial, sans-serif" font-size="14">Final accuracy</text>',
    ]
    for i in range(6):
        yv = y_max * i / 5
        y = yp(yv)
        parts.append(f'<line x1="{ml}" y1="{y:.2f}" x2="{ml+pw}" y2="{y:.2f}" stroke="#e8e8e8"/>')
        parts.append(f'<text x="{ml-12}" y="{y+4:.2f}" text-anchor="end" font-family="Arial, sans-serif" font-size="12" fill="#666">{yv:.2f}</text>')
    for x in xs:
        parts.append(f'<text x="{xp(x):.2f}" y="{mt+ph+25}" text-anchor="middle" font-family="Arial, sans-serif" font-size="12" fill="#666">{x:g}</text>')
    parts.append(f'<line x1="{ml}" y1="{mt+ph}" x2="{ml+pw}" y2="{mt+ph}" stroke="#333"/>')
    parts.append(f'<line x1="{ml}" y1="{mt}" x2="{ml}" y2="{mt+ph}" stroke="#333"/>')
    lx, ly0 = ml + pw + 36, mt + 6
    for i, s in enumerate(series):
        color = PALETTE.get(s.key, "#4a6d8c")
        pts = " ".join(f"{xp(x):.2f},{yp(y):.2f}" for x, y in s.points)
        parts.append(f'<polyline points="{pts}" fill="none" stroke="{color}" stroke-width="3"/>')
        for x, y in s.points:
            parts.append(f'<circle cx="{xp(x):.2f}" cy="{yp(y):.2f}" r="4.5" fill="{color}" stroke="#fff"/>')
        ly = ly0 + i * 28
        parts.append(f'<line x1="{lx}" y1="{ly}" x2="{lx+24}" y2="{ly}" stroke="{color}" stroke-width="3"/>')
        parts.append(f'<text x="{lx+34}" y="{ly+4}" font-family="Arial, sans-serif" font-size="13">{esc(LABELS.get(s.key, s.key))}</text>')
    parts.append("</svg>")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(parts), encoding="utf-8")


def series_from_rows(rows: list[dict[str, str]], x_field: str, methods: list[str], key_field: str = "method") -> list[Series]:
    out = []
    for m in methods:
        pts = []
        for r in rows:
            if r.get(key_field) == m:
                pts.append((float(r[x_field]), float(r["acc_mean"])))
        if pts:
            out.append(Series(m, sorted(pts)))
    return out


def main() -> None:
    ap = argparse.ArgumentParser("Plot sensitivity figures")
    ap.add_argument("--runs-dir", type=str, default="runs")
    ap.add_argument("--out-dir", type=str, default="figures")
    args = ap.parse_args()
    runs = Path(args.runs_dir)
    out = Path(args.out_dir)

    dim = read_csv(runs / "dimension_sensitivity.csv")
    if dim:
        sketch_rows = [r for r in dim if r["sweep"] == "sketch_dim"]
        chart(
            series_from_rows(sketch_rows, "x_value", ["qproto_full", "qproto_proto", "no_schema", "wrong_schema"]),
            title="Sketch dimension sensitivity",
            subtitle="Default heterogeneous-readout task.",
            x_label="RFF sketch dimension",
            out=out / "sketch_dimension_sensitivity.svg",
            y_max=0.8,
        )
        hop_rows = [r for r in dim if r["sweep"] == "hop_dim"]
        chart(
            series_from_rows(hop_rows, "x_value", ["qproto_full", "qproto_hop", "qproto_proto"]),
            title="HOP dimension sensitivity",
            subtitle="Covariance/high-order task.",
            x_label="HOP sketch dimension",
            out=out / "hop_dimension_sensitivity.svg",
            y_max=0.9,
        )

    noniid = read_csv(runs / "noniid_sensitivity.csv")
    if noniid:
        chart(
            series_from_rows(noniid, "alpha", ["qproto_full", "qproto_proto", "no_schema", "wrong_schema", "fedavg_forced"]),
            title="Client label-skew sensitivity",
            subtitle="Dirichlet alpha controls non-IID severity; smaller is more heterogeneous.",
            x_label="Dirichlet alpha",
            out=out / "noniid_sensitivity.svg",
            y_max=0.8,
        )

    comm = read_csv(runs / "comm_budget_curve.csv")
    if comm:
        chart(
            series_from_rows(comm, "bytes_mean", ["proto", "hop"], key_field="variant"),
            title="Communication budget curve",
            subtitle="Prototype and HOP variants matched by transmitted scalars.",
            x_label="Bytes per client per round",
            out=out / "communication_budget_curve.svg",
            y_max=0.9,
        )
    print(f"Wrote sensitivity figures to {out}")


if __name__ == "__main__":
    main()

