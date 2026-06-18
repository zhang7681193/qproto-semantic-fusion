from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


def load_history(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def first_round_at(history: list[dict], target: float) -> int | None:
    for row in history:
        if float(row.get("acc", 0.0)) >= target:
            return int(row.get("round", 0))
    return None


def main() -> None:
    ap = argparse.ArgumentParser("Report convergence rounds from QProto-HOP history files")
    ap.add_argument("--root", type=str, default="runs")
    ap.add_argument("--prefix", type=str, default="")
    ap.add_argument("--absolute-target", type=float, default=0.6)
    ap.add_argument("--final-fraction", type=float, default=0.95)
    ap.add_argument("--out", type=str, default="")
    args = ap.parse_args()

    rows = []
    root = Path(args.root)
    for run_dir in sorted(p for p in root.iterdir() if p.is_dir()):
        if args.prefix and not run_dir.name.startswith(args.prefix):
            continue
        for hist_path in sorted(run_dir.glob("*/history.jsonl")):
            history = load_history(hist_path)
            if not history:
                continue
            final_acc = float(history[-1].get("acc", 0.0))
            frac_target = args.final_fraction * final_acc
            rows.append(
                {
                    "run": run_dir.name,
                    "method": hist_path.parent.name,
                    "final_acc": final_acc,
                    "round_abs_target": first_round_at(history, args.absolute_target),
                    "absolute_target": args.absolute_target,
                    "round_final_fraction": first_round_at(history, frac_target),
                    "final_fraction": args.final_fraction,
                    "n_evals": len(history),
                }
            )

    fields = [
        "run",
        "method",
        "final_acc",
        "round_abs_target",
        "absolute_target",
        "round_final_fraction",
        "final_fraction",
        "n_evals",
    ]
    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)
        print(f"Wrote {len(rows)} rows to {out}")
    else:
        writer = csv.DictWriter(__import__("sys").stdout, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()

