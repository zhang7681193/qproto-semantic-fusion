from __future__ import annotations

import argparse
import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


ORDER = ["PennyLane high-order", "Qiskit Aer MNIST-4", "MNIST-10", "Fashion-10", "CIFAR-10"]
METHOD_LABELS = {"qproto_chop": "CHOP", "qproto_cproto": "CProto"}


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main() -> None:
    ap = argparse.ArgumentParser("Plot CHOP sweep curves")
    ap.add_argument("--table", type=str, default="runs/chop_sweep_tables.csv")
    ap.add_argument("--out", type=str, default="latex_qproto_hop/figures/chop_sweep_accuracy.pdf")
    ap.add_argument("--png", type=str, default="runs/chop_sweep_accuracy.png")
    args = ap.parse_args()

    rows = read_rows(Path(args.table))
    groups = [g for g in ORDER if any(r["group"] == g for r in rows)]
    fig, axes = plt.subplots(2, 3, figsize=(11.0, 6.2), sharey=False)
    axes_flat = axes.reshape(-1)

    for ax, group in zip(axes_flat, groups):
        sub = [r for r in rows if r["group"] == group]
        for method in ["qproto_cproto", "qproto_chop"]:
            vals = sorted([r for r in sub if r["method"] == method], key=lambda r: int(r["k"]))
            if not vals:
                continue
            xs = [int(r["k"]) for r in vals]
            ys = [float(r["acc_mean"]) for r in vals]
            yerr = [float(r["acc_ci95"]) for r in vals]
            ax.errorbar(xs, ys, yerr=yerr, marker="o", linewidth=1.8, capsize=3, label=METHOD_LABELS[method])
        ax.set_title(group)
        ax.set_xlabel("selected observables K")
        ax.set_ylabel("accuracy")
        ax.grid(True, alpha=0.25)
        ax.legend(frameon=False, fontsize=8)

    for ax in axes_flat[len(groups) :]:
        ax.axis("off")

    fig.tight_layout()
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, bbox_inches="tight")
    png = Path(args.png)
    png.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(png, dpi=180, bbox_inches="tight")
    print(f"Wrote {out} and {png}")


if __name__ == "__main__":
    main()

