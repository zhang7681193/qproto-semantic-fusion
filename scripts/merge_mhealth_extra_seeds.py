from __future__ import annotations

import csv
from pathlib import Path

from run_nonquantum_if_benchmark import build_argparser, write_reports


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "runs" / "if_mhealth_fusion.csv"
EXTRA = ROOT / "runs" / "if_mhealth_fusion_seeds5_9.csv"


def read_rows(path: Path) -> list[dict[str, object]]:
    with path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    for row in rows:
        row["seed"] = int(row["seed"])
        row["final_acc"] = float(row["final_acc"])
        row["final_balanced_acc"] = float(row["final_balanced_acc"])
        row["bytes_per_client_round"] = int(float(row["bytes_per_client_round"]))
        row["elapsed_sec"] = float(row["elapsed_sec"])
    return rows


def main() -> None:
    base_rows = [r for r in read_rows(BASE) if int(r["seed"]) <= 4]
    extra_rows = read_rows(EXTRA)
    merged = base_rows + extra_rows
    merged.sort(key=lambda r: (int(r["seed"]), str(r["method"])))
    with BASE.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(merged[0].keys()))
        writer.writeheader()
        writer.writerows(merged)

    args = build_argparser().parse_args(
        [
            "--dataset",
            "mhealth",
            "--out-csv",
            str(BASE),
            "--out-md",
            str(ROOT / "runs" / "if_mhealth_fusion_report.md"),
            "--out-tex",
            str(ROOT / "latex_qproto_hop_IF" / "tables" / "table_if_mhealth_fusion.tex"),
            "--out-equal-tex",
            str(ROOT / "latex_qproto_hop_IF" / "tables" / "table_strict_equal_byte_mhealth.tex"),
        ]
    )
    write_reports(merged, args)


if __name__ == "__main__":
    main()

