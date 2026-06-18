from __future__ import annotations

import csv
import math
from pathlib import Path

import numpy as np

from run_nonquantum_if_benchmark import (
    build_argparser,
    bytes_cproto,
    calibration_accuracy_chop,
    calibration_accuracy_coverage,
    fit_chop,
    fit_coverage,
    make_benchmark,
    select_keys_by_anchor_covariance,
    select_keys_by_variance,
    train_calibration_split,
)


ROOT = Path(__file__).resolve().parents[1]
OUT_CSV = ROOT / "runs" / "adaptive_chop_gate_choices.csv"
OUT_TEX = ROOT / "latex_qproto_hop_IF" / "tables" / "table_adaptive_chop_gate_choices.tex"


DATASETS = [
    (
        "UCI HAR",
        [
            "--dataset",
            "uci_har",
            "--seeds",
            "0,1,2,3,4",
            "--n-train",
            "5000",
            "--n-test",
            "1500",
            "--anchor-size",
            "512",
            "--chop-keys",
            "128",
            "--equal-cproto-keys",
            "160",
            "--hop-dim",
            "64",
            "--hop-weight",
            "0.05",
            "--adaptive-calib-frac",
            "0.25",
            "--adaptive-margin",
            "0.0",
            "--key-policy",
            "variance",
            "--hop-pair-policy",
            "cross_group_covariance",
        ],
    ),
    (
        "MFeat",
        [
            "--dataset",
            "mfeat",
            "--seeds",
            "0,1,2,3,4,5,6,7,8,9",
            "--anchor-size",
            "700",
            "--views-per-client",
            "3",
            "--common-views",
            "1",
            "--chop-keys",
            "160",
            "--equal-cproto-keys",
            "0",
            "--hop-dim",
            "96",
            "--hop-weight",
            "0.05",
            "--adaptive-calib-frac",
            "0.25",
            "--adaptive-margin",
            "0.0",
            "--key-policy",
            "variance",
            "--hop-pair-policy",
            "cross_group_covariance",
        ],
    ),
    (
        "PAMAP2",
        [
            "--dataset",
            "pamap2",
            "--pamap2-split",
            "subject",
            "--pamap2-window",
            "128",
            "--pamap2-stride",
            "64",
            "--pamap2-max-windows-per-subject",
            "1200",
            "--pamap2-subjects",
            "all",
            "--seeds",
            "0,1,2,3,4",
            "--n-train",
            "0",
            "--n-test",
            "0",
            "--anchor-size",
            "1000",
            "--views-per-client",
            "6",
            "--common-views",
            "1",
            "--chop-keys",
            "128",
            "--equal-cproto-keys",
            "0",
            "--hop-dim",
            "128",
            "--hop-weight",
            "0.1",
            "--adaptive-calib-frac",
            "0.25",
            "--adaptive-margin",
            "0.0",
            "--key-policy",
            "anchor_covariance",
            "--hop-pair-policy",
            "cross_group_covariance",
        ],
    ),
    (
        "MHEALTH",
        [
            "--dataset",
            "mhealth",
            "--mhealth-split",
            "subject",
            "--mhealth-window",
            "128",
            "--mhealth-stride",
            "64",
            "--mhealth-max-windows-per-subject",
            "900",
            "--seeds",
            "0,1,2,3,4,5,6,7,8,9",
            "--n-train",
            "0",
            "--n-test",
            "0",
            "--anchor-size",
            "900",
            "--views-per-client",
            "5",
            "--common-views",
            "1",
            "--chop-keys",
            "96",
            "--equal-cproto-keys",
            "0",
            "--hop-dim",
            "96",
            "--hop-weight",
            "0.05",
            "--adaptive-calib-frac",
            "0.25",
            "--adaptive-margin",
            "0.0",
            "--key-policy",
            "anchor_covariance",
            "--hop-pair-policy",
            "cross_group_covariance",
        ],
    ),
]


ALPHAS = [0.0, 0.25, 0.5, 0.75, 1.0]


def choose_for_seed(args, seed: int) -> dict[str, object]:
    data = make_benchmark(args, seed)
    d = data.x_train.shape[1]
    key_selector = select_keys_by_anchor_covariance if args.key_policy == "anchor_covariance" else select_keys_by_variance
    chop_keys = key_selector(data, args.chop_keys)
    budget_bytes = bytes_cproto(data.n_classes, args.chop_keys, args.hop_dim)
    if args.equal_cproto_keys <= 0:
        equal_k = int(math.floor(((budget_bytes / 4.0 - 1.0) / data.n_classes - 1.0) / 2.0))
        equal_k = max(1, min(d, equal_k))
    else:
        equal_k = min(d, args.equal_cproto_keys)
    low_keys = key_selector(data, equal_k)
    fit_data, cal_indices = train_calibration_split(data, calib_frac=args.adaptive_calib_frac, seed=seed + 719 + 991)

    low_proto, low_counts = fit_coverage(fit_data, low_keys)
    low_cal = calibration_accuracy_coverage(data, cal_indices, keys=low_keys, proto=low_proto, counts=low_counts)

    proto, counts, hop_proto, hop_counts, pair_a, pair_b = fit_chop(
        fit_data,
        keys=chop_keys,
        hop_dim=args.hop_dim,
        seed=seed + 719 + 997,
        anchor_pairs=True,
        pair_policy=args.hop_pair_policy,
    )
    scores: list[tuple[float, str, float | None]] = [(low_cal, "cproto", None)]
    for alpha in ALPHAS:
        score = calibration_accuracy_chop(
            data,
            cal_indices,
            keys=chop_keys,
            proto=proto,
            counts=counts,
            hop_proto=hop_proto,
            hop_counts=hop_counts,
            pair_a=pair_a,
            pair_b=pair_b,
            hop_weight=args.hop_weight,
            alpha=alpha,
        )
        scores.append((score, "mixture", alpha))
    best_score, best_kind, best_alpha = max(scores, key=lambda x: (x[0], -1.0 if x[1] == "cproto" else float(x[2] or 0.0)))
    if best_kind == "cproto" or best_score - low_cal <= args.adaptive_margin:
        selected = "CProto"
        alpha_value = ""
    else:
        selected = f"alpha={best_alpha:g}"
        alpha_value = f"{best_alpha:g}"
    return {
        "seed": seed,
        "selected": selected,
        "alpha": alpha_value,
        "low_cal": low_cal,
        "best_cal": best_score,
        "best_gain": best_score - low_cal,
    }


def main() -> None:
    rows: list[dict[str, object]] = []
    summaries: list[dict[str, object]] = []
    for dataset, argv in DATASETS:
        args = build_argparser().parse_args(argv)
        seeds = [int(x.strip()) for x in args.seeds.split(",") if x.strip()]
        choices = []
        for seed in seeds:
            choice = choose_for_seed(args, seed)
            choice["dataset"] = dataset
            rows.append(choice)
            choices.append(choice)
        labels = ["CProto"] + [f"alpha={a:g}" for a in ALPHAS]
        counts = {label: sum(1 for c in choices if c["selected"] == label) for label in labels}
        summaries.append(
            {
                "dataset": dataset,
                "n": len(seeds),
                **counts,
                "mean_cal_gain": float(np.mean([float(c["best_gain"]) for c in choices])),
            }
        )

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    tex = [
        "\\begin{table}[t]",
        "\\centering",
        "\\caption{Adaptive CHOP calibration choices. The gate uses training-only calibration and chooses either the equal-byte CProto fallback or a CHOP-key candidate \\(\\alpha d_{\\mathrm{low}}+(1-\\alpha)d_{\\mathrm{hop}}\\). The \\(\\alpha=1\\) column is a CHOP-key low-order branch rather than a high-order branch.}",
        "\\label{tab:adaptive-chop-gate}",
        "\\begin{tabular}{lrrrrrrr}",
        "\\toprule",
        "Dataset & \\(n\\) & CProto & \\(\\alpha=0\\) & .25 & .50 & .75 & 1.0 \\\\",
        "\\midrule",
    ]
    for summary in summaries:
        tex.append(
            f"{summary['dataset']} & {summary['n']} & {summary['CProto']} & "
            f"{summary['alpha=0']} & {summary['alpha=0.25']} & {summary['alpha=0.5']} & "
            f"{summary['alpha=0.75']} & {summary['alpha=1']} \\\\"
        )
    tex.extend(["\\bottomrule", "\\end{tabular}", "\\end{table}", ""])
    OUT_TEX.write_text("\n".join(tex), encoding="utf-8")
    print(f"Wrote {OUT_CSV} and {OUT_TEX}")


if __name__ == "__main__":
    main()

