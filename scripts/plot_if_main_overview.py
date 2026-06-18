from __future__ import annotations

import csv
import math
import os
from collections import defaultdict
from pathlib import Path

_cache_dir = Path(__file__).resolve().parents[1] / ".mplconfig"
_cache_dir.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(_cache_dir))
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "latex_qproto_hop_IF" / "figures" / "if_main_result_overview.pdf"
OUT_PNG = ROOT / "latex_qproto_hop_IF" / "figures" / "if_main_result_overview.png"

COLORS = {
    "QProto": "#2a6f97",
    "CProto": "#2a9d8f",
    "CHOP": "#b75d69",
    "Zero-fill": "#9c6ade",
    "Shared": "#e09f3e",
    "Strong baseline": "#577590",
    "FedProto": "#8d99ae",
}


def read_summary(path: str) -> list[dict[str, str]]:
    with (ROOT / path).open(newline="") as f:
        return list(csv.DictReader(f))


def mean_ci(values: list[float]) -> tuple[float, float]:
    m = sum(values) / len(values)
    if len(values) < 2:
        return m, 0.0
    sd = math.sqrt(sum((v - m) ** 2 for v in values) / (len(values) - 1))
    return m, 1.96 * sd / math.sqrt(len(values))


def seed_means(path: str) -> dict[str, tuple[float, float]]:
    rows = read_summary(path)
    by_method: dict[str, list[float]] = defaultdict(list)
    for row in rows:
        by_method[row["method"]].append(float(row["final_acc"]))
    return {method: mean_ci(vals) for method, vals in by_method.items()}


def summary_lookup(path: str, group_key: str, method_key: str) -> dict[tuple[str, str], tuple[float, float]]:
    rows = read_summary(path)
    out: dict[tuple[str, str], tuple[float, float]] = {}
    for row in rows:
        group = row[group_key]
        method = row[method_key]
        out[(group, method)] = (float(row["acc_mean"]), float(row.get("acc_ci95", 0.0)))
    return out


def grouped_bars(ax, groups, series, data, title, ylim=None):
    width = min(0.18, 0.72 / max(len(series), 1))
    xs = list(range(len(groups)))
    offsets = [(i - (len(series) - 1) / 2) * width for i in range(len(series))]
    for offset, (label, color) in zip(offsets, series):
        vals = [data[(g, label)][0] for g in groups]
        errs = [data[(g, label)][1] for g in groups]
        ax.bar([x + offset for x in xs], vals, width, label=label, color=color, edgecolor="#263238", linewidth=0.35)
        ax.errorbar([x + offset for x in xs], vals, yerr=errs, fmt="none", ecolor="#263238", elinewidth=0.8, capsize=2)
    ax.set_xticks(xs)
    ax.set_xticklabels(groups)
    ax.set_ylim(*(ylim or (0, 1)))
    ax.set_ylabel("Accuracy")
    ax.set_title(title, loc="left", fontweight="bold")
    ax.grid(axis="y", alpha=0.22, linewidth=0.6)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


def main() -> None:
    plt.rcParams.update(
        {
            "font.size": 8,
            "axes.titlesize": 9,
            "axes.labelsize": 8,
            "legend.fontsize": 7,
            "xtick.labelsize": 7,
            "ytick.labelsize": 7,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
        }
    )

    fig, axes = plt.subplots(2, 2, figsize=(7.3, 4.85))
    fig.subplots_adjust(left=0.075, right=0.99, top=0.94, bottom=0.16, hspace=0.44, wspace=0.28)

    # A: full-class heterogeneous readout controls.
    controls = summary_lookup("runs/if_fusion_controls_report.csv", "group", "method")
    image_groups = ["MNIST-10", "Fashion-10", "CIFAR-10"]
    image_data = {}
    for group in image_groups:
        image_data[(group, "Zero-fill")] = controls[(group, "schema_zero_fill")]
        image_data[(group, "Shared")] = controls[(group, "shared_observable")]
        image_data[(group, "QProto")] = controls[(group, "qproto_masked_hop")]
    grouped_bars(
        axes[0, 0],
        image_groups,
        [("Zero-fill", COLORS["Zero-fill"]), ("Shared", COLORS["Shared"]), ("QProto", COLORS["QProto"])],
        image_data,
        "A. Full-class heterogeneous readout",
        ylim=(0.0, 0.82),
    )

    # B: real IF benchmarks.
    har = seed_means("runs/if_nonquantum_sensor_fusion.csv")
    mfeat = seed_means("runs/if_mfeat_fusion.csv")
    real_groups = ["UCI HAR", "MFeat"]
    real_data = {
        ("UCI HAR", "Zero-fill"): har["zero_fill_rff_equal_bytes"],
        ("UCI HAR", "Shared"): har["shared_view_rff_equal_bytes"],
        ("UCI HAR", "CProto"): har["cproto_equal_bytes"],
        ("UCI HAR", "Strong baseline"): har["hemis_modality_dropout"],
        ("MFeat", "Zero-fill"): mfeat["zero_fill_rff_equal_bytes"],
        ("MFeat", "Shared"): mfeat["shared_view_rff_equal_bytes"],
        ("MFeat", "CProto"): mfeat["group_cproto_equal_bytes"],
        ("MFeat", "Strong baseline"): mfeat["hemis_modality_dropout"],
    }
    grouped_bars(
        axes[0, 1],
        real_groups,
        [
            ("Zero-fill", COLORS["Zero-fill"]),
            ("Shared", COLORS["Shared"]),
            ("CProto", COLORS["CProto"]),
            ("Strong baseline", COLORS["Strong baseline"]),
        ],
        real_data,
        "B. Real missing-view fusion",
        ylim=(0.0, 1.02),
    )

    # C: real and controlled high-order/source-interaction tests.
    mhealth = seed_means("runs/if_mhealth_fusion.csv")
    high = summary_lookup("runs/if_scientific_fusion_report.csv", "method", "method")
    high_data = {
        ("MHEALTH", "Zero-fill"): mhealth["zero_fill_rff_equal_bytes"],
        ("MHEALTH", "Shared"): mhealth["shared_view_rff_equal_bytes"],
        ("MHEALTH", "CProto"): mhealth["cproto_equal_bytes"],
        ("MHEALTH", "CHOP"): mhealth["chop_equal_bytes"],
        ("Covariance", "Zero-fill"): high[("schema_zero_fill", "schema_zero_fill")],
        ("Covariance", "Shared"): high[("shared_observable", "shared_observable")],
        ("Covariance", "CProto"): high[("qproto_cproto", "qproto_cproto")],
        ("Covariance", "CHOP"): high[("qproto_chop", "qproto_chop")],
    }
    grouped_bars(
        axes[1, 0],
        ["MHEALTH", "Covariance"],
        [
            ("Zero-fill", COLORS["Zero-fill"]),
            ("Shared", COLORS["Shared"]),
            ("CProto", COLORS["CProto"]),
            ("CHOP", COLORS["CHOP"]),
        ],
        high_data,
        "C. High-order/source interactions",
        ylim=(0.0, 1.02),
    )

    # D: Qiskit Aer compatibility under simulated backend noise.
    qiskit = summary_lookup("runs/qiskit_noise_sweep_report.csv", "setting", "method")
    q_groups = ["clean", "lowshot", "readout", "depol", "depth"]
    setting_map = {
        "clean": "clean",
        "lowshot": "lowshot",
        "readout": "readout_high",
        "depol": "depol_high",
        "depth": "depth2",
    }
    x = list(range(len(q_groups)))
    for method, label, color, marker in [
        ("qproto_masked_hop", "QProto", COLORS["QProto"], "o"),
        ("shared_observable", "Shared", COLORS["Shared"], "s"),
        ("fedproto_schema", "FedProto", COLORS["FedProto"], "^"),
    ]:
        vals = [qiskit[(setting_map[g], method)][0] for g in q_groups]
        errs = [qiskit[(setting_map[g], method)][1] for g in q_groups]
        axes[1, 1].errorbar(x, vals, yerr=errs, marker=marker, linewidth=1.5, capsize=2.5, label=label, color=color)
    axes[1, 1].set_xticks(x)
    axes[1, 1].set_xticklabels(q_groups)
    axes[1, 1].set_ylim(0.25, 0.66)
    axes[1, 1].set_ylabel("Accuracy")
    axes[1, 1].set_title("D. Circuit-generated readout compatibility", loc="left", fontweight="bold")
    axes[1, 1].grid(axis="y", alpha=0.22, linewidth=0.6)
    axes[1, 1].spines["top"].set_visible(False)
    axes[1, 1].spines["right"].set_visible(False)

    handles, labels = [], []
    for ax in axes.flat:
        h, l = ax.get_legend_handles_labels()
        handles.extend(h)
        labels.extend(l)
    unique = {}
    for h, l in zip(handles, labels):
        unique.setdefault(l, h)
    fig.legend(unique.values(), unique.keys(), loc="lower center", ncol=7, frameon=False, bbox_to_anchor=(0.5, 0.025))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, bbox_inches="tight")
    fig.savefig(OUT_PNG, dpi=220, bbox_inches="tight")
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()

