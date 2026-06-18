from __future__ import annotations

import argparse
import csv
import math
import re
from dataclasses import dataclass
from pathlib import Path


T_CRIT_95 = {1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571, 6: 2.447, 7: 2.365, 8: 2.306, 9: 2.262, 10: 2.228}


def mean(xs: list[float]) -> float:
    return float(sum(float(x) for x in xs) / len(xs))


def stdev(xs: list[float]) -> float:
    if len(xs) <= 1:
        return 0.0
    m = mean(xs)
    return float(math.sqrt(sum((float(x) - m) ** 2 for x in xs) / (len(xs) - 1)))


@dataclass(frozen=True)
class ComparisonSpec:
    family: str
    setting: str
    pattern: str
    method_a: str
    method_b: str
    label: str


@dataclass(frozen=True)
class CsvComparisonSpec:
    family: str
    setting: str
    path: str
    method_a: str
    method_b: str
    label: str


COMPARISONS = [
    # IF-style missing-observation/fusion controls.
    ComparisonSpec("IF fusion", "MNIST-10", r"^if_fusion_fullclass_mnist10_seed\d+$", "qproto_masked_hop", "schema_zero_fill", "Masked-HOP - zero-fill"),
    ComparisonSpec("IF fusion", "MNIST-10", r"^if_fusion_fullclass_mnist10_seed\d+$", "qproto_masked_hop", "shared_observable", "Masked-HOP - shared-observable"),
    ComparisonSpec("IF fusion", "MNIST-10", r"^if_fusion_fullclass_mnist10_seed\d+$", "qproto_masked_hop", "qproto_cproto", "Masked-HOP - CProto"),
    ComparisonSpec("IF fusion", "MNIST-10", r"^if_fusion_fullclass_mnist10_seed\d+$", "qproto_chop", "schema_zero_fill", "CHOP - zero-fill"),
    ComparisonSpec("IF fusion", "Fashion-10", r"^if_fusion_fullclass_fashion10_seed\d+$", "qproto_masked_hop", "schema_zero_fill", "Masked-HOP - zero-fill"),
    ComparisonSpec("IF fusion", "Fashion-10", r"^if_fusion_fullclass_fashion10_seed\d+$", "qproto_masked_hop", "shared_observable", "Masked-HOP - shared-observable"),
    ComparisonSpec("IF fusion", "Fashion-10", r"^if_fusion_fullclass_fashion10_seed\d+$", "qproto_masked_hop", "qproto_cproto", "Masked-HOP - CProto"),
    ComparisonSpec("IF fusion", "Fashion-10", r"^if_fusion_fullclass_fashion10_seed\d+$", "qproto_chop", "schema_zero_fill", "CHOP - zero-fill"),
    ComparisonSpec("IF fusion", "CIFAR-10", r"^if_fusion_fullclass_cifar10_seed\d+$", "qproto_masked_hop", "schema_zero_fill", "Masked-HOP - zero-fill"),
    ComparisonSpec("IF fusion", "CIFAR-10", r"^if_fusion_fullclass_cifar10_seed\d+$", "qproto_masked_hop", "shared_observable", "Masked-HOP - shared-observable"),
    ComparisonSpec("IF fusion", "CIFAR-10", r"^if_fusion_fullclass_cifar10_seed\d+$", "qproto_masked_hop", "qproto_cproto", "Masked-HOP - CProto"),
    ComparisonSpec("IF fusion", "CIFAR-10", r"^if_fusion_fullclass_cifar10_seed\d+$", "qproto_chop", "schema_zero_fill", "CHOP - zero-fill"),
    ComparisonSpec("IF scientific", "Covariance sensing", r"^if_scientific_fusion_seed\d+$", "qproto_chop", "schema_zero_fill", "CHOP - zero-fill"),
    ComparisonSpec("IF scientific", "Covariance sensing", r"^if_scientific_fusion_seed\d+$", "qproto_chop", "shared_observable", "CHOP - shared-observable"),
    ComparisonSpec("IF scientific", "Covariance sensing", r"^if_scientific_fusion_seed\d+$", "qproto_chop", "qproto_cproto", "CHOP - CProto"),
    ComparisonSpec("IF scientific", "Covariance sensing", r"^if_scientific_fusion_seed\d+$", "qproto_masked_hop", "qproto_masked", "Masked-HOP - Masked"),
    # Standard FL/QFL baselines on final full-class runs.
    ComparisonSpec("FL baselines", "MNIST-10", r"^final_fullclass_mnist10_seed\d+$", "qproto_masked_hop", "fedproto_schema", "Masked-HOP - schema-FedProto"),
    ComparisonSpec("FL baselines", "MNIST-10", r"^final_fullclass_mnist10_seed\d+$", "qproto_masked_hop", "fedadam_schema", "Masked-HOP - schema-FedAdam"),
    ComparisonSpec("FL baselines", "MNIST-10", r"^final_fullclass_mnist10_seed\d+$", "qproto_masked_hop", "no_schema", "Masked-HOP - no-schema"),
    ComparisonSpec("FL baselines", "Fashion-10", r"^final_fullclass_fashion10_seed\d+$", "qproto_masked_hop", "fedproto_schema", "Masked-HOP - schema-FedProto"),
    ComparisonSpec("FL baselines", "Fashion-10", r"^final_fullclass_fashion10_seed\d+$", "qproto_masked_hop", "fedadam_schema", "Masked-HOP - schema-FedAdam"),
    ComparisonSpec("FL baselines", "Fashion-10", r"^final_fullclass_fashion10_seed\d+$", "qproto_masked_hop", "no_schema", "Masked-HOP - no-schema"),
    ComparisonSpec("FL baselines", "CIFAR-10", r"^final_fullclass_cifar10_seed\d+$", "qproto_masked_hop", "fedproto_schema", "Masked-HOP - schema-FedProto"),
    ComparisonSpec("FL baselines", "CIFAR-10", r"^final_fullclass_cifar10_seed\d+$", "qproto_masked_hop", "fedadam_schema", "Masked-HOP - schema-FedAdam"),
    ComparisonSpec("FL baselines", "CIFAR-10", r"^final_fullclass_cifar10_seed\d+$", "qproto_masked_hop", "no_schema", "Masked-HOP - no-schema"),
    # High-order and quantum-backend claims.
    ComparisonSpec("High-order", "PennyLane high-order", r"^drift_baseline_pennylane_highorder_seed\d+$", "qproto_chop", "qproto_cproto", "CHOP - CProto"),
    ComparisonSpec("High-order", "PennyLane high-order", r"^drift_baseline_pennylane_highorder_seed\d+$", "qproto_chop", "fedproto_schema", "CHOP - schema-FedProto"),
    ComparisonSpec("Quantum backend", "Qiskit Aer", r"^drift_baseline_qiskit_aer_seed\d+$", "qproto_masked_hop", "fedproto_schema", "Masked-HOP - schema-FedProto"),
    ComparisonSpec("Quantum backend", "Qiskit Aer", r"^drift_baseline_qiskit_aer_seed\d+$", "qproto_masked_hop", "feddyn_schema", "Masked-HOP - FedDyn"),
]


CSV_COMPARISONS = [
    CsvComparisonSpec("Real missing-view", "UCI HAR", "runs/if_nonquantum_sensor_fusion.csv", "cproto_equal_bytes", "zero_fill_rff_equal_bytes", "CProto eq. - zero-fill RFF eq."),
    CsvComparisonSpec("Real missing-view", "UCI HAR", "runs/if_nonquantum_sensor_fusion.csv", "cproto_equal_bytes", "shared_view_rff_equal_bytes", "CProto eq. - shared-view RFF eq."),
    CsvComparisonSpec("Real missing-view", "UCI HAR", "runs/if_nonquantum_sensor_fusion.csv", "coverage_proto_all", "anchor_ae_impute", "Coverage all - anchor AE"),
    CsvComparisonSpec("Real missing-view", "MFeat", "runs/if_mfeat_fusion.csv", "group_cproto_equal_bytes", "zero_fill_rff_equal_bytes", "Group-CProto eq. - zero-fill RFF eq."),
    CsvComparisonSpec("Real missing-view", "MFeat", "runs/if_mfeat_fusion.csv", "group_cproto_equal_bytes", "shared_view_rff_equal_bytes", "Group-CProto eq. - shared-view RFF eq."),
    CsvComparisonSpec("Real missing-view", "MFeat", "runs/if_mfeat_fusion.csv", "group_cproto_all", "mask_aware_mlp_pooled", "Group-CProto all - mask-aware MLP"),
    CsvComparisonSpec("Real high-order", "MHEALTH", "runs/if_mhealth_fusion.csv", "chop_equal_bytes", "cproto_equal_bytes", "CHOP eq. - CProto eq."),
    CsvComparisonSpec("Real high-order", "MHEALTH", "runs/if_mhealth_fusion.csv", "chop_equal_bytes", "zero_fill_rff_equal_bytes", "CHOP eq. - zero-fill RFF eq."),
    CsvComparisonSpec("Real high-order", "MHEALTH", "runs/if_mhealth_fusion.csv", "chop_equal_bytes", "shared_view_rff_equal_bytes", "CHOP eq. - shared-view RFF eq."),
    CsvComparisonSpec("Real high-order", "MHEALTH", "runs/if_mhealth_fusion.csv", "chop_equal_bytes", "mask_aware_mlp_pooled", "CHOP eq. - mask-aware MLP"),
    CsvComparisonSpec("Real high-order", "MHEALTH", "runs/if_mhealth_fusion.csv", "adaptive_chop_equal_bytes", "cproto_equal_bytes", "Adaptive CHOP - CProto eq."),
    CsvComparisonSpec("Real high-order", "MHEALTH", "runs/if_mhealth_fusion.csv", "random_key_hop_equal_bytes", "random_key_cproto_equal_bytes", "Random HOP - random CProto eq."),
    CsvComparisonSpec("Adaptive gate", "UCI HAR", "runs/if_nonquantum_sensor_fusion.csv", "adaptive_chop_equal_bytes", "chop_equal_bytes", "Adaptive CHOP - CHOP eq."),
    CsvComparisonSpec("Adaptive gate", "MFeat", "runs/if_mfeat_fusion.csv", "adaptive_chop_equal_bytes", "chop_equal_bytes", "Adaptive CHOP - CHOP eq."),
    CsvComparisonSpec("Adaptive gate", "PAMAP2", "runs/if_pamap2_fusion.csv", "adaptive_chop_equal_bytes", "chop_equal_bytes", "Adaptive CHOP - CHOP eq."),
    CsvComparisonSpec("Adaptive gate", "PAMAP2", "runs/if_pamap2_fusion.csv", "adaptive_chop_equal_bytes", "zero_fill_rff_equal_bytes", "Adaptive CHOP - zero-fill RFF eq."),
    CsvComparisonSpec("Adaptive gate", "PAMAP2", "runs/if_pamap2_fusion.csv", "adaptive_chop_equal_bytes", "shared_view_rff_equal_bytes", "Adaptive CHOP - shared-view RFF eq."),
]


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def seed_from_run(run: str) -> int | None:
    m = re.search(r"_seed(\d+)$", run)
    return int(m.group(1)) if m else None


def ci95(xs: list[float]) -> float:
    if len(xs) <= 1:
        return 0.0
    return T_CRIT_95.get(len(xs) - 1, 1.96) * stdev(xs) / math.sqrt(len(xs))


def _student_t_sf(t: float, df: int) -> float:
    """Survival function for Student's t distribution without requiring SciPy."""
    if df <= 0 or math.isnan(t):
        return 1.0
    if t < 0:
        return 1.0 - _student_t_sf(-t, df)
    if abs(t) <= 1e-12:
        return 0.5
    try:
        import mpmath as mp

        x = df / (df + t * t)
        return float(0.5 * mp.betainc(df / 2.0, 0.5, 0, x, regularized=True))
    except Exception:
        # Pure-Python fallback using Simpson integration of the Student-t PDF.
        # This avoids the anti-conservative normal-tail approximation for small
        # n paired tests when neither SciPy nor mpmath is available.
        coef = math.gamma((df + 1.0) / 2.0) / (math.sqrt(df * math.pi) * math.gamma(df / 2.0))

        def pdf(x: float) -> float:
            return coef * (1.0 + (x * x) / df) ** (-(df + 1.0) / 2.0)

        n = max(1000, min(100000, int(math.ceil(t * 1200.0))))
        if n % 2 == 1:
            n += 1
        h = t / n
        total = pdf(0.0) + pdf(t)
        odd = 0.0
        even = 0.0
        for i in range(1, n):
            val = pdf(i * h)
            if i % 2:
                odd += val
            else:
                even += val
        cdf_gap = h * (total + 4.0 * odd + 2.0 * even) / 3.0
        return max(0.0, min(1.0, 0.5 - cdf_gap))


def paired_t_pvalues(deltas: list[float]) -> tuple[float, float]:
    if len(deltas) <= 1:
        return 1.0, 1.0
    delta_mean = mean(deltas)
    sd = stdev(deltas)
    if sd <= 1e-12:
        if delta_mean > 0:
            return 0.0, 0.0
        if delta_mean == 0:
            return 0.5, 1.0
        return 1.0, 0.0
    try:
        from scipy import stats

        res_one = stats.ttest_1samp(deltas, popmean=0.0, alternative="greater")
        res_two = stats.ttest_1samp(deltas, popmean=0.0, alternative="two-sided")
        p_one = float(res_one.pvalue)
        p_two = float(res_two.pvalue)
        return (1.0 if math.isnan(p_one) else p_one, 1.0 if math.isnan(p_two) else p_two)
    except Exception:
        t_stat = delta_mean / (sd / math.sqrt(len(deltas)))
        p_one = _student_t_sf(t_stat, len(deltas) - 1)
        p_two = min(1.0, 2.0 * _student_t_sf(abs(t_stat), len(deltas) - 1))
        return p_one, p_two


def cohen_dz(deltas: list[float]) -> float:
    if len(deltas) <= 1:
        return 0.0
    sd = stdev(deltas)
    if sd <= 1e-12:
        return math.inf if mean(deltas) > 0 else 0.0
    return mean(deltas) / sd


def holm_adjust(pvals: list[float]) -> list[float]:
    n = len(pvals)
    order = sorted(range(n), key=lambda i: pvals[i])
    adjusted = [1.0] * n
    running = 0.0
    for rank, idx in enumerate(order):
        val = min(1.0, (n - rank) * pvals[idx])
        running = max(running, val)
        adjusted[idx] = running
    return adjusted


def collect_comparison(rows: list[dict[str, str]], spec: ComparisonSpec) -> dict[str, object] | None:
    by_run_method = {(str(r["run"]), str(r["method"])): r for r in rows}
    deltas = []
    seeds = []
    for row in rows:
        run = str(row["run"])
        if str(row["method"]) != spec.method_a or not re.match(spec.pattern, run):
            continue
        other = by_run_method.get((run, spec.method_b))
        seed = seed_from_run(run)
        if other is None or seed is None:
            continue
        deltas.append(float(row["final_acc"]) - float(other["final_acc"]))
        seeds.append(seed)
    if not deltas:
        return None
    p_one, p_two = paired_t_pvalues(deltas)
    return {
        "family": spec.family,
        "setting": spec.setting,
        "comparison": spec.label,
        "method_a": spec.method_a,
        "method_b": spec.method_b,
        "n": len(deltas),
        "seeds": ",".join(str(s) for s in sorted(seeds)),
        "delta_acc_mean": mean(deltas),
        "delta_acc_ci95": ci95(deltas),
        "wins": sum(1 for d in deltas if d > 0),
        "cohen_dz": cohen_dz(deltas),
        "p_one_sided": p_one,
        "p_two_sided": p_two,
    }


def collect_csv_comparison(spec: CsvComparisonSpec) -> dict[str, object] | None:
    path = Path(spec.path)
    if not path.exists():
        return None
    rows = read_rows(path)
    by_seed_method = {(int(r["seed"]), str(r["method"])): r for r in rows}
    seeds = sorted({int(r["seed"]) for r in rows if str(r["method"]) == spec.method_a})
    deltas = []
    kept_seeds = []
    for seed in seeds:
        a = by_seed_method.get((seed, spec.method_a))
        b = by_seed_method.get((seed, spec.method_b))
        if a is None or b is None:
            continue
        deltas.append(float(a["final_acc"]) - float(b["final_acc"]))
        kept_seeds.append(seed)
    if not deltas:
        return None
    p_one, p_two = paired_t_pvalues(deltas)
    return {
        "family": spec.family,
        "setting": spec.setting,
        "comparison": spec.label,
        "method_a": spec.method_a,
        "method_b": spec.method_b,
        "n": len(deltas),
        "seeds": ",".join(str(s) for s in kept_seeds),
        "deltas": ";".join(f"{d:.8f}" for d in deltas),
        "delta_acc_mean": mean(deltas),
        "delta_acc_ci95": ci95(deltas),
        "wins": sum(1 for d in deltas if d > 0),
        "cohen_dz": cohen_dz(deltas),
        "p_one_sided": p_one,
        "p_two_sided": p_two,
    }


def fmt_p(p: float, tex: bool = False) -> str:
    if p < 1e-4:
        return "\\(<0.0001\\)" if tex else "<0.0001"
    return f"{p:.4f}"


def main() -> None:
    ap = argparse.ArgumentParser("Report paired significance/effect sizes for IF-style QProto experiments")
    ap.add_argument("--summary", type=str, default="runs/summary.csv")
    ap.add_argument("--out", type=str, default="runs/if_significance_report.csv")
    ap.add_argument("--md", type=str, default="runs/if_significance_report.md")
    ap.add_argument("--tex", type=str, default="latex_qproto_hop/tables/table_if_significance.tex")
    ap.add_argument("--tex-full", type=str, default=None)
    args = ap.parse_args()

    rows = read_rows(Path(args.summary))
    out_rows = [r for r in (collect_comparison(rows, spec) for spec in COMPARISONS) if r is not None]
    out_rows.extend(r for r in (collect_comparison(rows, spec) for spec in CSV_COMPARISONS if isinstance(spec, ComparisonSpec)) if r is not None)
    out_rows.extend(r for r in (collect_csv_comparison(spec) for spec in CSV_COMPARISONS if isinstance(spec, CsvComparisonSpec)) if r is not None)
    adjusted_one = holm_adjust([float(r["p_one_sided"]) for r in out_rows])
    adjusted_two = holm_adjust([float(r["p_two_sided"]) for r in out_rows])
    for row, p_one_adj, p_two_adj in zip(out_rows, adjusted_one, adjusted_two):
        row["p_holm"] = p_one_adj
        row["p_two_sided_holm"] = p_two_adj
        row["significant_005"] = bool(p_one_adj < 0.05)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "family",
        "setting",
        "comparison",
        "method_a",
        "method_b",
        "n",
        "seeds",
        "deltas",
        "delta_acc_mean",
        "delta_acc_ci95",
        "wins",
        "cohen_dz",
        "p_one_sided",
        "p_holm",
        "p_two_sided",
        "p_two_sided_holm",
        "significant_005",
    ]
    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(out_rows)

    lines = [
        "# IF-Style Paired Significance Report",
        "",
        "One-sided paired t-tests are used for the directional claim that the QProto variant improves over the named control. Two-sided p-values are reported as a robustness check. Holm correction is applied across all reported comparisons.",
        "",
    ]
    for family in ["IF fusion", "IF scientific", "Real missing-view", "Real high-order", "Adaptive gate", "FL baselines", "High-order", "Quantum backend"]:
        group_rows = [r for r in out_rows if r["family"] == family]
        if not group_rows:
            continue
        lines.extend([
            f"## {family}",
            "",
            "| Setting | Comparison | n | Delta acc. | 95% CI | Wins | Cohen dz | one-sided Holm p | two-sided Holm p |",
            "|---|---|---:|---:|---:|---:|---:|---:|---:|",
        ])
        for r in group_rows:
            lines.append(
                f"| {r['setting']} | {r['comparison']} | {r['n']} | "
                f"{float(r['delta_acc_mean']):.4f} | {float(r['delta_acc_ci95']):.4f} | "
                f"{r['wins']}/{r['n']} | {float(r['cohen_dz']):.2f} | {fmt_p(float(r['p_holm']))} | "
                f"{fmt_p(float(r['p_two_sided_holm']))} |"
            )
        lines.append("")
    Path(args.md).write_text("\n".join(lines), encoding="utf-8")

    # Compact LaTeX table for the paper: focus on IF-fusion controls plus one representative
    # FL/QFL and high-order line per setting family.
    tex_rows = [
        r
        for r in out_rows
        if (
            r["family"] in {"IF fusion", "IF scientific"}
            and r["comparison"] in {"Masked-HOP - zero-fill", "Masked-HOP - shared-observable"}
        )
        or (
            r["family"] == "IF scientific"
            and r["comparison"] in {"CHOP - zero-fill", "CHOP - shared-observable", "CHOP - CProto"}
        )
        or (
            r["family"] == "FL baselines"
            and r["comparison"] in {"Masked-HOP - schema-FedProto", "Masked-HOP - schema-FedAdam"}
        )
        or (
            r["family"] == "Real missing-view"
            and r["comparison"] in {"CProto eq. - zero-fill RFF eq.", "CProto eq. - shared-view RFF eq.", "Group-CProto eq. - zero-fill RFF eq.", "Group-CProto eq. - shared-view RFF eq."}
        )
        or (
            r["family"] == "Real high-order"
            and r["comparison"] in {"CHOP eq. - CProto eq.", "CHOP eq. - zero-fill RFF eq.", "CHOP eq. - mask-aware MLP"}
        )
        or (
            r["family"] == "Adaptive gate"
            and r["comparison"] in {"Adaptive CHOP - CHOP eq."}
        )
        or r["family"] in {"High-order", "Quantum backend"}
    ]
    tex = [
        "\\begin{table*}[t]",
        "\\centering",
        "\\caption{Paired significance tests for the main experimental claims. Reported values are mean paired accuracy deltas over matched seeds. One-sided paired \\(t\\)-tests use Holm correction across all tested comparisons; the supplementary table also reports two-sided Holm values.}",
        "\\label{tab:if-significance}",
        "\\scriptsize",
        "\\setlength{\\tabcolsep}{3pt}",
        "\\renewcommand{\\arraystretch}{0.9}",
        "\\resizebox{\\textwidth}{!}{%",
        "\\begin{tabular}{llrrrr}",
        "\\toprule",
        "Setting & Comparison & \\(n\\) & \\(\\Delta\\) acc. & \\(d_z\\) & Holm \\(p_{1s}\\) \\\\",
        "\\midrule",
    ]
    for r in tex_rows:
        tex.append(
            f"{r['setting']} & {r['comparison']} & {r['n']} & "
            f"{float(r['delta_acc_mean']):.3f} & {float(r['cohen_dz']):.2f} & {fmt_p(float(r['p_holm']), tex=True)} \\\\"
        )
    tex.extend(["\\bottomrule", "\\end{tabular}%", "}", "\\end{table*}", ""])
    tex_path = Path(args.tex)
    tex_path.parent.mkdir(parents=True, exist_ok=True)
    tex_path.write_text("\n".join(tex), encoding="utf-8")

    if args.tex_full:
        full_tex = [
            "\\begin{table*}[t]",
            "\\centering",
            "\\caption{Full paired significance tests for the main experimental claims. Reported values are mean paired accuracy deltas over matched seeds. One-sided paired \\(t\\)-tests test the directional claim; two-sided values are provided as a robustness check. Holm correction is applied across all reported comparisons.}",
            "\\label{tab:if-significance-full}",
            "\\scriptsize",
            "\\setlength{\\tabcolsep}{2.5pt}",
            "\\renewcommand{\\arraystretch}{0.78}",
            "\\resizebox{\\textwidth}{!}{%",
            "\\begin{tabular}{llrrrrr}",
            "\\toprule",
            "Setting & Comparison & \\(n\\) & \\(\\Delta\\) acc. & \\(d_z\\) & Holm \\(p_{1s}\\) & Holm \\(p_{2s}\\) \\\\",
            "\\midrule",
        ]
        for r in out_rows:
            full_tex.append(
                f"{r['setting']} & {r['comparison']} & {r['n']} & "
                f"{float(r['delta_acc_mean']):.3f} & {float(r['cohen_dz']):.2f} & "
                f"{fmt_p(float(r['p_holm']), tex=True)} & {fmt_p(float(r['p_two_sided_holm']), tex=True)} \\\\"
            )
        full_tex.extend(["\\bottomrule", "\\end{tabular}%", "}", "\\end{table*}", ""])
        full_tex_path = Path(args.tex_full)
        full_tex_path.parent.mkdir(parents=True, exist_ok=True)
        full_tex_path.write_text("\n".join(full_tex), encoding="utf-8")
        print(f"Wrote {out_path}, {args.md}, {tex_path}, and {full_tex_path}")
    else:
        print(f"Wrote {out_path}, {args.md}, and {tex_path}")


if __name__ == "__main__":
    main()

