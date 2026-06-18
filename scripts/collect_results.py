from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


def main() -> None:
    ap = argparse.ArgumentParser("Collect QProto-HOP metrics.json files into CSV")
    ap.add_argument("--root", type=str, default="runs")
    ap.add_argument("--out", type=str, default="runs/summary.csv")
    args = ap.parse_args()

    rows = []
    for metrics_path in Path(args.root).glob("*/metrics.json"):
        with metrics_path.open("r", encoding="utf-8") as f:
            obj = json.load(f)
        run_name = metrics_path.parent.name
        config = {}
        config_path = metrics_path.parent / "config.json"
        if config_path.exists():
            with config_path.open("r", encoding="utf-8") as f:
                raw_config = json.load(f)
            keep = [
                "dataset",
                "dataset_path",
                "n_classes",
                "n_train",
                "n_test",
                "data_structure",
                "class_sep",
                "cov_boost",
                "sketch_dim",
                "hop_dim",
                "classical_sketch_dim",
                "anchor_normalize",
                "anchor_size",
                "bandwidth",
                "classical_bandwidth",
                "hop_weight",
                "shots",
                "shot_noise_scale",
                "wrong_shift",
                "readout_p",
                "readout_std",
                "depol_p",
                "depol_std",
                "observables",
                "obs_per_client",
                "observable_overlap",
                "common_policy",
                "dirichlet_alpha",
                "participation",
                "seed",
            ]
            config = {f"config_{k}": raw_config.get(k) for k in keep if k in raw_config}
        for rec in obj.get("summaries", []):
            row = {"run": run_name}
            row.update(config)
            row.update(rec)
            rows.append(row)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        out.write_text("", encoding="utf-8")
        return

    fields = sorted({k for row in rows for k in row.keys()})
    with out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} rows to {out}")


if __name__ == "__main__":
    main()

