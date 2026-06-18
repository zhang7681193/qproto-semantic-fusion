from __future__ import annotations

import csv
from pathlib import Path

from run_nonquantum_if_benchmark import (
    build_argparser,
    bytes_proto,
    eval_hemis_modality_dropout,
    make_benchmark,
    write_reports,
)


def read_existing(path: Path) -> list[dict[str, object]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main() -> None:
    args = build_argparser().parse_args()
    seeds = [int(x.strip()) for x in args.seeds.split(",") if x.strip()]
    seed_set = {str(s) for s in seeds}
    rows = [
        r
        for r in read_existing(Path(args.out_csv))
        if not (r.get("method") == "hemis_modality_dropout" and str(r.get("seed")) in seed_set)
    ]
    for seed in seeds:
        print(f"Adding HeMIS modality-dropout baseline seed {seed}", flush=True)
        data = make_benchmark(args, seed)
        acc, elapsed = eval_hemis_modality_dropout(data, args, seed + 821)
        d = data.x_train.shape[1]
        rows.append(
            {
                "run": f"if_nonquantum_sensor_seed{seed}",
                "seed": seed,
                "method": "hemis_modality_dropout",
                "family": "deep-missing-view",
                "final_acc": acc,
                "final_balanced_acc": acc,
                "bytes_per_client_round": bytes_proto(data.n_classes, 2 * d),
                "elapsed_sec": elapsed,
            }
        )
    write_reports(rows, args)


if __name__ == "__main__":
    main()

