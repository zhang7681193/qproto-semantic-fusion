from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path


CORE_GROUPS = [
    ("Final MNIST-10 full-class", r"^final_fullclass_mnist10_seed(\d+)$"),
    ("Final Fashion-10 full-class", r"^final_fullclass_fashion10_seed(\d+)$"),
    ("Final CIFAR-10 full-class", r"^final_fullclass_cifar10_seed(\d+)$"),
    ("IF fusion MNIST-10", r"^if_fusion_fullclass_mnist10_seed(\d+)$"),
    ("IF fusion Fashion-10", r"^if_fusion_fullclass_fashion10_seed(\d+)$"),
    ("IF fusion CIFAR-10", r"^if_fusion_fullclass_cifar10_seed(\d+)$"),
    ("IF scientific fusion", r"^if_scientific_fusion_seed(\d+)$"),
    ("MNIST-10 full-class", r"^(masked|masked_hop|chop)_mnist10.*_seed(\d+)$|^matched_budget_mnist10_seed(\d+)$|^strong_baseline_mnist10_seed(\d+)$|^schema_head_baseline_mnist10_seed(\d+)$"),
    ("Fashion-10 full-class", r"^(masked|masked_hop|chop)_fashion10.*_seed(\d+)$|^matched_budget_fashion10_seed(\d+)$|^strong_baseline_fashion10_seed(\d+)$|^schema_head_baseline_fashion10_seed(\d+)$"),
    ("CIFAR-10 full-class", r"^(masked|masked_hop|chop)_cifar10.*_seed(\d+)$|^matched_budget_cifar10_seed(\d+)$|^strong_baseline_cifar10_seed(\d+)$|^schema_head_baseline_cifar10_seed(\d+)$"),
    ("Qiskit Aer noise", r"^qiskit_noise_(clean|lowshot|readout_high|depol_high|depth2)_seed(\d+)$"),
    ("Qiskit Aer drift", r"^drift_baseline_qiskit_aer_seed(\d+)$"),
    ("PennyLane high-order drift", r"^drift_baseline_pennylane_highorder_seed(\d+)$"),
    ("MNIST-10 scale/overlap", r"^(scale_mnist10_c\d+|overlap_mnist10_o[0-9p]+)_seed(\d+)$"),
    ("Fashion-10 scale/overlap", r"^(scale_fashion10_c\d+|overlap_fashion10_o[0-9p]+)_seed(\d+)$"),
    ("CIFAR-10 scale/overlap", r"^(scale_cifar10_c\d+|overlap_cifar10_o[0-9p]+)_seed(\d+)$"),
    ("PennyLane high-order overlap", r"^overlap_pennylane_highorder_o[0-9p]+_seed(\d+)$"),
]


TABLE_INPUT_RE = re.compile(r"\\input\{([^}]+)\}")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def config_of(run_dir: Path) -> dict:
    path = run_dir / "config.json"
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def seeds_for(pattern: str, runs: list[str]) -> set[int]:
    seeds: set[int] = set()
    regex = re.compile(pattern)
    for run in runs:
        m = regex.match(run)
        if not m:
            continue
        for g in m.groups()[1:] if len(m.groups()) > 1 else m.groups():
            if g is not None and str(g).isdigit():
                seeds.add(int(g))
    return seeds


def qiskit_noise_double_count_checks(root: Path) -> list[str]:
    issues = []
    for run_dir in root.glob("qiskit_noise_*_seed*"):
        cfg = config_of(run_dir)
        if not cfg:
            continue
        vals = {
            "shot_noise_scale": float(cfg.get("shot_noise_scale", 0.0)),
            "readout_p": float(cfg.get("readout_p", 0.0)),
            "readout_std": float(cfg.get("readout_std", 0.0)),
            "depol_p": float(cfg.get("depol_p", 0.0)),
            "depol_std": float(cfg.get("depol_std", 0.0)),
        }
        bad = {k: v for k, v in vals.items() if abs(v) > 1e-12}
        if bad:
            issues.append(f"{run_dir.name}: extra downstream noise is nonzero: {bad}")
    return issues


def table_input_checks(latex_dir: Path) -> list[str]:
    issues = []
    for tex in [latex_dir / "main.tex", *list((latex_dir / "sections").glob("*.tex"))]:
        if not tex.exists():
            continue
        text = tex.read_text(encoding="utf-8")
        for m in TABLE_INPUT_RE.finditer(text):
            rel = m.group(1)
            candidate = latex_dir / f"{rel}.tex"
            if not candidate.exists():
                issues.append(f"Missing LaTeX input: {rel}.tex referenced by {tex.name}")
    return issues


def method_count_checks(rows: list[dict[str, str]]) -> list[str]:
    issues = []
    by_run: dict[str, list[str]] = {}
    for row in rows:
        by_run.setdefault(str(row["run"]), []).append(str(row["method"]))
    required = {
        "strong_baseline": {"fedadam_forced", "fedproto_schema", "qproto_cproto", "qproto_chop", "qproto_masked_hop"},
        "drift_baseline": {"fedadam_schema", "fedproto_schema", "scaffold_schema", "feddyn_schema", "qproto_cproto", "qproto_chop"},
        "qiskit_noise": {"fedadam_schema", "fedproto_schema", "shared_observable", "no_schema", "wrong_schema", "qproto_cproto", "qproto_chop", "qproto_masked_hop"},
        "if_fusion_fullclass": {"schema_zero_fill", "schema_mask_only", "no_schema", "forced_canonical", "shared_observable", "qproto_cproto", "qproto_chop", "qproto_masked_hop"},
        "if_scientific_fusion": {"schema_zero_fill", "schema_mask_only", "shared_observable", "qproto_cproto", "qproto_chop", "qproto_masked_hop", "fedproto_schema", "fedadam_schema"},
    }
    for run, methods in by_run.items():
        if "smoke" in run:
            continue
        method_set = set(methods)
        for prefix, need in required.items():
            if run.startswith(prefix):
                missing = sorted(need - method_set)
                if missing:
                    issues.append(f"{run}: missing methods {missing}")
    return issues


def byte_checks(rows: list[dict[str, str]]) -> list[str]:
    issues = []
    by_run: dict[str, dict[str, float]] = {}
    for row in rows:
        try:
            by_run.setdefault(str(row["run"]), {})[str(row["method"])] = float(row["bytes_per_client_round"])
        except Exception:
            continue
    for run, vals in by_run.items():
        if "qproto_chop" in vals and "fedproto_schema" in vals:
            # CHOP is intentionally compared both matched-ish and compressed; flag only extreme accidental mismatches.
            ratio = vals["qproto_chop"] / max(vals["fedproto_schema"], 1.0)
            if ratio > 2.5:
                issues.append(f"{run}: CHOP/FedProto byte ratio unusually high ({ratio:.2f})")
        if "scaffold_schema" in vals and "fedadam_schema" in vals:
            ratio = vals["scaffold_schema"] / max(vals["fedadam_schema"], 1.0)
            if not (1.8 <= ratio <= 2.2):
                issues.append(f"{run}: SCAFFOLD byte ratio should be about 2x FedAdam, got {ratio:.2f}")
    return issues


def main() -> None:
    ap = argparse.ArgumentParser("Audit experiment fairness and reproducibility metadata")
    ap.add_argument("--runs-dir", type=str, default="runs")
    ap.add_argument("--summary", type=str, default="runs/summary.csv")
    ap.add_argument("--latex-dir", type=str, default="latex_qproto_hop")
    ap.add_argument("--out", type=str, default="runs/fairness_audit.md")
    args = ap.parse_args()

    root = Path(args.runs_dir)
    rows = read_csv(Path(args.summary)) if Path(args.summary).exists() else []
    runs = sorted({r["run"] for r in rows})
    lines = ["# Experiment Fairness Audit", ""]
    lines.append("## Seed Coverage")
    lines.append("")
    lines.append("| Group | Seeds found | Count |")
    lines.append("|---|---:|---:|")
    for name, pattern in CORE_GROUPS:
        seeds = sorted(seeds_for(pattern, runs))
        seed_text = ",".join(str(s) for s in seeds) if seeds else "-"
        lines.append(f"| {name} | {seed_text} | {len(seeds)} |")
    lines.append("")

    issues = []
    issues.extend(qiskit_noise_double_count_checks(root))
    issues.extend(table_input_checks(Path(args.latex_dir)))
    issues.extend(method_count_checks(rows))
    issues.extend(byte_checks(rows))

    notes = []
    suspicious = [r for r in runs if r == "topjournal_mnist10_shared_seed0"]
    if suspicious:
        notes.append(
            "topjournal_mnist10_shared_seed0 is an auxiliary legacy run and is excluded from formal full-class tables."
        )

    lines.append("## Automated Checks")
    lines.append("")
    if issues:
        lines.append("Status: REVIEW NEEDED")
        lines.append("")
        for issue in issues:
            lines.append(f"- {issue}")
    else:
        lines.append("Status: PASS")
        lines.append("")
        lines.append("- No missing LaTeX table inputs detected.")
        lines.append("- Qiskit Aer noise-sweep runs do not add downstream synthetic noise.")
        lines.append("- Required methods are present in strong/drift/noise baseline groups.")
        lines.append("- Communication accounting is internally consistent for audited baselines.")
    if notes:
        lines.append("")
        lines.append("Notes:")
        for note in notes:
            lines.append(f"- {note}")
    lines.append("")
    lines.append("## Interpretation")
    lines.append("")
    lines.append(
        "The audit checks mechanical fairness and metadata consistency. It does not prove that every baseline is globally optimally tuned; tuned FedAdam/FedProto/SCAFFOLD/FedDyn audits should be reported as optimizer baselines, while QProto variants should be compared at matched or explicitly stated communication budgets."
    )

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()

