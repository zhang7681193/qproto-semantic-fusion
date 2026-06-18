from __future__ import annotations

import argparse
import csv
import math
import re
import statistics as st
from pathlib import Path


T_CRIT_95 = {1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571}
ORDER = {"clean": 0, "lowshot": 1, "readout_high": 2, "depol_high": 3, "depth2": 4}
METHOD_ORDER = {
    "qproto_masked_hop": 0,
    "qproto_chop": 1,
    "qproto_masked": 2,
    "qproto_cproto": 3,
    "fedproto_schema": 4,
    "fedadam_schema": 5,
    "shared_observable": 6,
    "no_schema": 7,
    "wrong_schema": 8,
}


def ci95(xs: list[float]) -> float:
    if len(xs) <= 1:
        return 0.0
    return T_CRIT_95.get(len(xs) - 1, 1.96) * st.stdev(xs) / math.sqrt(len(xs))


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main() -> None:
    ap = argparse.ArgumentParser("Summarize Qiskit Aer noise/depth/shot sweep")
    ap.add_argument("--summary", type=str, default="runs/summary.csv")
    ap.add_argument("--out", type=str, default="runs/qiskit_noise_sweep_report.csv")
    ap.add_argument("--md", type=str, default="runs/qiskit_noise_sweep_report.md")
    args = ap.parse_args()

    groups: dict[tuple[str, str], list[dict[str, str]]] = {}
    for r in read_rows(Path(args.summary)):
        m = re.match(r"qiskit_noise_(clean|lowshot|readout_high|depol_high|depth2)_seed\d+$", r["run"])
        if not m:
            continue
        groups.setdefault((m.group(1), r["method"]), []).append(r)

    out_rows = []
    for (setting, method), vals in groups.items():
        acc = [float(v["final_acc"]) for v in vals]
        bal = [float(v["final_balanced_acc"]) for v in vals]
        bytes_ = [float(v["bytes_per_client_round"]) for v in vals]
        out_rows.append(
            {
                "setting": setting,
                "method": method,
                "n": len(vals),
                "acc_mean": st.mean(acc),
                "acc_ci95": ci95(acc),
                "balanced_acc_mean": st.mean(bal),
                "bytes_mean": st.mean(bytes_),
            }
        )
    out_rows.sort(key=lambda r: (ORDER.get(str(r["setting"]), 99), METHOD_ORDER.get(str(r["method"]), 99)))

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    fields = ["setting", "method", "n", "acc_mean", "acc_ci95", "balanced_acc_mean", "bytes_mean"]
    with out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(out_rows)

    labels = {
        "clean": "Clean, depth 1, 1024 shots",
        "lowshot": "Low shot, 128 shots",
        "readout_high": "High readout error",
        "depol_high": "High depolarizing noise",
        "depth2": "Depth 2",
    }
    lines = ["# Qiskit Aer Noise Sweep Report", ""]
    for setting in sorted({str(r["setting"]) for r in out_rows}, key=lambda x: ORDER.get(x, 99)):
        lines.extend([f"## {labels.get(setting, setting)}", "", "| Method | n | Acc. | 95% CI | Bal. acc. | Bytes |", "|---|---:|---:|---:|---:|---:|"])
        for r in [x for x in out_rows if x["setting"] == setting]:
            lines.append(
                f"| {r['method']} | {r['n']} | {float(r['acc_mean']):.4f} | "
                f"{float(r['acc_ci95']):.4f} | {float(r['balanced_acc_mean']):.4f} | {float(r['bytes_mean']):.0f} |"
            )
        lines.append("")
    Path(args.md).write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {out} and {args.md}")


if __name__ == "__main__":
    main()

