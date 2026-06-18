from __future__ import annotations

import csv
import math
from pathlib import Path

import numpy as np

from run_nonquantum_if_benchmark import (
    build_argparser,
    bytes_cproto,
    eval_chop_method,
    eval_coverage_method,
    make_benchmark,
    select_keys_by_anchor_covariance,
    select_keys_by_variance,
)


def make_args(split: str):
    return build_argparser().parse_args(
        [
            "--dataset",
            "gas_drift",
            "--gas-split",
            split,
            "--n-train",
            "0",
            "--n-test",
            "0",
            "--anchor-size",
            "900",
            "--views-per-client",
            "8",
            "--common-views",
            "2",
            "--chop-keys",
            "96",
            "--equal-cproto-keys",
            "0",
            "--hop-dim",
            "96",
            "--pca-rank",
            "24",
            "--ridge-alpha",
            "0.1",
            "--key-policy",
            "variance",
        ]
    )


def main() -> None:
    seeds = [0, 1, 2, 3, 4]
    weights = [0.02, 0.05, 0.1, 0.2, 0.5]
    pair_policies = ["anchor_covariance", "cross_group_covariance"]
    rows: list[dict[str, object]] = []
    for split in ["random", "temporal"]:
        args = make_args(split)
        for seed in seeds:
            data = make_benchmark(args, seed)
            d = data.x_train.shape[1]
            key_selector = select_keys_by_anchor_covariance if args.key_policy == "anchor_covariance" else select_keys_by_variance
            chop_keys = key_selector(data, args.chop_keys)
            budget_bytes = bytes_cproto(data.n_classes, args.chop_keys, args.hop_dim)
            equal_k = int(math.floor(((budget_bytes / 4.0 - 1.0) / data.n_classes - 1.0) / 2.0))
            equal_k = max(1, min(d, equal_k))
            equal_keys = key_selector(data, equal_k)
            cproto_acc, _ = eval_coverage_method(data, keys=equal_keys, bytes_per_round=budget_bytes)
            for pair_policy in pair_policies:
                for weight in weights:
                    chop_acc, _ = eval_chop_method(
                        data,
                        keys=chop_keys,
                        hop_dim=args.hop_dim,
                        hop_weight=weight,
                        seed=seed + 709,
                        bytes_per_round=budget_bytes,
                        anchor_pairs=True,
                        pair_policy=pair_policy,
                    )
                    rows.append(
                        {
                            "split": split,
                            "seed": seed,
                            "pair_policy": pair_policy,
                            "hop_weight": weight,
                            "cproto_acc": cproto_acc,
                            "chop_acc": chop_acc,
                            "delta": chop_acc - cproto_acc,
                        }
                    )

    out_path = Path("runs/gas_chop_config_screen.csv")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {out_path}")
    print("split,pair_policy,hop_weight,mean_delta,mean_chop,mean_cproto,wins")
    for split in ["random", "temporal"]:
        for pair_policy in pair_policies:
            for weight in weights:
                vals = [r for r in rows if r["split"] == split and r["pair_policy"] == pair_policy and r["hop_weight"] == weight]
                delta = np.array([float(r["delta"]) for r in vals], dtype=np.float64)
                chop = np.array([float(r["chop_acc"]) for r in vals], dtype=np.float64)
                cproto = np.array([float(r["cproto_acc"]) for r in vals], dtype=np.float64)
                print(
                    f"{split},{pair_policy},{weight:.2f},"
                    f"{delta.mean():.4f},{chop.mean():.4f},{cproto.mean():.4f},{int((delta > 0).sum())}/{len(delta)}"
                )


if __name__ == "__main__":
    main()

