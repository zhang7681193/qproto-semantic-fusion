from __future__ import annotations

import csv
import math
import re
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
T_CRIT_95 = {1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571}


def mean(xs: list[float]) -> float:
    return float(sum(float(x) for x in xs) / len(xs))


def stdev(xs: list[float]) -> float:
    if len(xs) <= 1:
        return 0.0
    m = mean(xs)
    return float(math.sqrt(sum((float(x) - m) ** 2 for x in xs) / (len(xs) - 1)))


def read_csv(path: str) -> list[dict[str, str]]:
    with (ROOT / path).open("r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def ci95(xs: list[float]) -> float:
    if len(xs) <= 1:
        return 0.0
    return T_CRIT_95.get(len(xs) - 1, 1.96) * stdev(xs) / math.sqrt(len(xs))


def clean_tex(s: str) -> str:
    s = s.strip()
    s = re.sub(r"\\textbf\{([^{}]+)\}", r"\1", s)
    s = s.replace(r"\method{}", "QProto")
    s = s.replace(r"\%", "%")
    s = s.replace(r"\(", "").replace(r"\)", "")
    s = s.replace(r"\midrule", "").replace(r"\bottomrule", "").strip()
    s = re.sub(r"\s+", " ", s)
    return s


def parse_float(s: str) -> float:
    return float(clean_tex(s))


def parse_table(path: str) -> list[list[str]]:
    rows: list[list[str]] = []
    text = (ROOT / path).read_text(encoding="utf-8")
    for raw in text.splitlines():
        line = raw.strip()
        if "&" not in line or line.startswith("%"):
            continue
        if "toprule" in line or "midrule" in line or "bottomrule" in line:
            continue
        line = line.split(r"\\")[0]
        parts = [clean_tex(p) for p in line.split("&")]
        if parts and parts[0] not in {"Dataset", "Method", "Setting"}:
            rows.append(parts)
    return rows


def summarize_seed_csv(path: str) -> dict[str, dict[str, float]]:
    rows = read_csv(path)
    if rows and "acc_mean" in rows[0]:
        return {
            r["method"]: {
                "acc": float(r["acc_mean"]),
                "ci": float(r["acc_ci95"]),
                "bytes": float(r["bytes_mean"]),
                "runtime": 0.0,
                "n": float(r["n"]),
            }
            for r in rows
        }
    grouped: dict[str, list[dict[str, str]]] = {}
    for r in rows:
        grouped.setdefault(r["method"], []).append(r)
    out: dict[str, dict[str, float]] = {}
    for method, items in grouped.items():
        accs = [float(r["final_acc"]) for r in items]
        bytes_vals = [float(r["bytes_per_client_round"]) for r in items]
        elapsed = [float(r["elapsed_sec"]) for r in items]
        out[method] = {
            "acc": mean(accs),
            "ci": ci95(accs),
            "bytes": mean(bytes_vals),
            "runtime": mean(elapsed),
            "n": len(accs),
        }
    return out


def summarize_group_csv(path: str, group_col: str) -> dict[tuple[str, str], dict[str, float]]:
    rows = read_csv(path)
    out: dict[tuple[str, str], dict[str, float]] = {}
    for r in rows:
        key = (r[group_col], r["method"])
        out[key] = {
            "acc": float(r["acc_mean"]),
            "ci": float(r["acc_ci95"]),
            "bytes": float(r["bytes_mean"]),
            "n": float(r["n"]),
        }
    return out


@dataclass(frozen=True)
class TableCheck:
    name: str
    table: str
    source: str
    method_map: dict[str, str]
    dataset_map: dict[str, str] | None = None
    group_col: str | None = None
    has_runtime: bool = False


COMMON_METHODS = {
    "Mask-only metadata": "mask_only_metadata",
    "Zero-fill prototype": "zero_fill_proto",
    "Mean-impute prototype": "mean_impute_proto",
    "Value+mask prototype": "value_mask_proto",
    "Anchor PCA imputation": "anchor_pca_impute",
    "Learned ridge imputation": "anchor_ridge_impute",
    "Anchor autoencoder imputation": "anchor_ae_impute",
    "Mask-aware pooled MLP": "mask_aware_mlp_pooled",
    "HeMIS modality-dropout fusion": "hemis_modality_dropout",
    "View-wise late fusion": "late_fusion_proto",
    "Shared-view prototype": "shared_view_proto",
    "Shared-view RFF equal bytes": "shared_view_rff_equal_bytes",
    "Zero-fill RFF equal bytes": "zero_fill_rff_equal_bytes",
    "Coverage prototype all": "coverage_proto_all",
    "Group-balanced CProto all": "group_cproto_all",
    "CProto equal bytes": "cproto_equal_bytes",
    "Group-balanced CProto equal bytes": "group_cproto_equal_bytes",
    "Random-key CProto equal bytes": "random_key_cproto_equal_bytes",
    "Random-key HOP equal bytes": "random_key_hop_equal_bytes",
    "CHOP equal bytes": "chop_equal_bytes",
    "Adaptive CHOP equal bytes": "adaptive_chop_equal_bytes",
}


CHECKS = [
    TableCheck(
        "full-class",
        "latex_qproto_hop_IF/tables/table_masked_fullclass.tex",
        "runs/final_fullclass_report.csv",
        {
            "QProto-Masked-HOP": "qproto_masked_hop",
            "QProto-Masked": "qproto_masked",
            "CHOP, K=96": "qproto_chop",
            "CProto, K=96": "qproto_cproto",
            "shared-observable": "shared_observable",
            "FedAdam schema": "fedadam_schema",
            "FedProto schema": "fedproto_schema",
            "SCAFFOLD schema": "scaffold_schema",
            "no-schema": "no_schema",
        },
        group_col="dataset",
    ),
    TableCheck(
        "IF full-class controls",
        "latex_qproto_hop_IF/tables/table_if_fusion_controls.tex",
        "runs/if_fusion_controls_report.csv",
        {
            "Mask-only metadata": "schema_mask_only",
            "Schema zero-fill": "schema_zero_fill",
            "No schema": "no_schema",
            "Forced canonical": "forced_canonical",
            "Shared observables": "shared_observable",
            "RFF prototype": "qproto_proto",
            "CProto": "qproto_cproto",
            "CHOP": "qproto_chop",
            "QProto-Masked": "qproto_masked",
            "QProto-Masked-HOP": "qproto_masked_hop",
        },
        group_col="group",
    ),
    TableCheck(
        "UCI HAR",
        "latex_qproto_hop_IF/tables/table_if_nonquantum_fusion.tex",
        "runs/if_nonquantum_sensor_fusion.csv",
        COMMON_METHODS,
        has_runtime=True,
    ),
    TableCheck(
        "UCI Multiple Features",
        "latex_qproto_hop_IF/tables/table_if_mfeat_fusion.tex",
        "runs/if_mfeat_fusion.csv",
        COMMON_METHODS,
        has_runtime=True,
    ),
    TableCheck(
        "UCI MHEALTH",
        "latex_qproto_hop_IF/tables/table_if_mhealth_fusion.tex",
        "runs/if_mhealth_fusion.csv",
        COMMON_METHODS,
        has_runtime=True,
    ),
    TableCheck(
        "UCI PAMAP2",
        "latex_qproto_hop_IF/tables/table_if_pamap2_fusion.tex",
        "runs/if_pamap2_fusion.csv",
        COMMON_METHODS,
        has_runtime=True,
    ),
    TableCheck(
        "UCI Hydraulic Systems",
        "latex_qproto_hop_IF/tables/table_if_hydraulic_cooler_fusion.tex",
        "runs/if_hydraulic_cooler_fusion.csv",
        COMMON_METHODS,
        has_runtime=True,
    ),
    TableCheck(
        "WDBC supplement",
        "latex_qproto_hop_IF/tables/table_if_wdbc_fusion.tex",
        "runs/if_wdbc_fusion.csv",
        COMMON_METHODS,
        has_runtime=True,
    ),
    TableCheck(
        "covariance sensing",
        "latex_qproto_hop_IF/tables/table_if_scientific_fusion.tex",
        "runs/if_scientific_fusion_report.csv",
        {
            "Mask-only metadata": "schema_mask_only",
            "Schema zero-fill": "schema_zero_fill",
            "No schema": "no_schema",
            "Forced canonical": "forced_canonical",
            "Shared observables": "shared_observable",
            "FedProto schema": "fedproto_schema",
            "FedAdam schema": "fedadam_schema",
            "QProto-Masked": "qproto_masked",
            "CProto": "qproto_cproto",
            "QProto-Masked-HOP": "qproto_masked_hop",
            "CHOP": "qproto_chop",
        },
    ),
]


STRICT_CHECKS = [
    ("strict HAR", "latex_qproto_hop_IF/tables/table_strict_equal_byte_controls.tex", "runs/if_nonquantum_sensor_fusion.csv"),
    ("strict MFeat", "latex_qproto_hop_IF/tables/table_strict_equal_byte_mfeat.tex", "runs/if_mfeat_fusion.csv"),
    ("strict MHEALTH", "latex_qproto_hop_IF/tables/table_strict_equal_byte_mhealth.tex", "runs/if_mhealth_fusion.csv"),
    ("strict PAMAP2", "latex_qproto_hop_IF/tables/table_strict_equal_byte_pamap2.tex", "runs/if_pamap2_fusion.csv"),
    ("strict Hydraulic", "latex_qproto_hop_IF/tables/table_strict_equal_byte_hydraulic_cooler.tex", "runs/if_hydraulic_cooler_fusion.csv"),
    ("strict WDBC", "latex_qproto_hop_IF/tables/table_strict_equal_byte_wdbc.tex", "runs/if_wdbc_fusion.csv"),
]


def nearly_equal(reported: float, expected: float, decimals: int = 3) -> bool:
    return abs(reported - round(expected, decimals)) <= 0.5 * 10 ** (-decimals) + 1e-12


def check_table(check: TableCheck) -> list[str]:
    issues: list[str] = []
    rows = parse_table(check.table)
    if check.group_col:
        source = summarize_group_csv(check.source, check.group_col)
    else:
        source = summarize_seed_csv(check.source)
    for row in rows:
        if check.group_col:
            if len(row) < 5:
                continue
            dataset, label, acc, ci, bytes_val = row[:5]
            method = check.method_map.get(label)
            if method is None:
                issues.append(f"{check.name}: unmapped method label {label!r}")
                continue
            key = (dataset, method)
            expected = source.get(key)  # type: ignore[arg-type]
        else:
            if len(row) < 4:
                continue
            label, acc, ci, bytes_val = row[:4]
            method = check.method_map.get(label)
            if method is None:
                issues.append(f"{check.name}: unmapped method label {label!r}")
                continue
            expected = source.get(method)  # type: ignore[assignment]
        if expected is None:
            issues.append(f"{check.name}: missing source row for {row}")
            continue
        if not nearly_equal(parse_float(acc), float(expected["acc"])):
            issues.append(f"{check.name}: acc mismatch for {row[:2]} table={acc}, expected={float(expected['acc']):.6f}")
        if not nearly_equal(parse_float(ci), float(expected["ci"])):
            issues.append(f"{check.name}: CI mismatch for {row[:2]} table={ci}, expected={float(expected['ci']):.6f}")
        if abs(float(bytes_val) - round(float(expected["bytes"]))) > 0.5:
            issues.append(f"{check.name}: bytes mismatch for {row[:2]} table={bytes_val}, expected={float(expected['bytes']):.1f}")
        if check.has_runtime:
            runtime = row[4] if check.group_col is None else row[4]
            if len(row) >= 5 and not nearly_equal(parse_float(runtime), float(expected["runtime"])):
                # Runtime is diagnostic only; retain it as a warning-level issue.
                issues.append(f"{check.name}: runtime mismatch for {row[:2]} table={runtime}, expected={float(expected['runtime']):.6f}")
    return issues


def check_equal_bytes() -> list[str]:
    specs = [
        ("HAR", "runs/if_nonquantum_sensor_fusion.csv", ["shared_view_rff_equal_bytes", "zero_fill_rff_equal_bytes", "cproto_equal_bytes", "group_cproto_equal_bytes", "random_key_hop_equal_bytes", "chop_equal_bytes", "adaptive_chop_equal_bytes"]),
        ("MFeat", "runs/if_mfeat_fusion.csv", ["shared_view_rff_equal_bytes", "zero_fill_rff_equal_bytes", "cproto_equal_bytes", "group_cproto_equal_bytes", "random_key_cproto_equal_bytes", "random_key_hop_equal_bytes", "chop_equal_bytes", "adaptive_chop_equal_bytes"]),
        ("MHEALTH", "runs/if_mhealth_fusion.csv", ["shared_view_rff_equal_bytes", "zero_fill_rff_equal_bytes", "cproto_equal_bytes", "group_cproto_equal_bytes", "random_key_cproto_equal_bytes", "random_key_hop_equal_bytes", "chop_equal_bytes", "adaptive_chop_equal_bytes"]),
        ("PAMAP2", "runs/if_pamap2_fusion.csv", ["shared_view_rff_equal_bytes", "zero_fill_rff_equal_bytes", "cproto_equal_bytes", "group_cproto_equal_bytes", "random_key_cproto_equal_bytes", "random_key_hop_equal_bytes", "chop_equal_bytes", "adaptive_chop_equal_bytes"]),
        ("Hydraulic", "runs/if_hydraulic_cooler_fusion.csv", ["shared_view_rff_equal_bytes", "zero_fill_rff_equal_bytes", "cproto_equal_bytes", "group_cproto_equal_bytes", "random_key_cproto_equal_bytes", "random_key_hop_equal_bytes", "chop_equal_bytes"]),
        ("WDBC", "runs/if_wdbc_fusion.csv", ["shared_view_rff_equal_bytes", "zero_fill_rff_equal_bytes", "cproto_equal_bytes", "group_cproto_equal_bytes", "random_key_cproto_equal_bytes", "random_key_hop_equal_bytes", "chop_equal_bytes"]),
    ]
    issues: list[str] = []
    for name, path, methods in specs:
        rows = read_csv(path)
        vals = sorted({int(round(float(r["bytes_per_client_round"]))) for r in rows if r["method"] in methods})
        if len(vals) != 1:
            issues.append(f"{name}: strict equal-byte methods have multiple payloads: {vals}")
    return issues


def check_strict_tables() -> list[str]:
    issues: list[str] = []
    for name, table, source_path in STRICT_CHECKS:
        source = summarize_seed_csv(source_path)
        rows = parse_table(table)
        for row in rows:
            if len(row) < 3:
                continue
            label, acc, bytes_val = row[:3]
            method = COMMON_METHODS.get(label)
            if method is None:
                issues.append(f"{name}: unmapped method label {label!r}")
                continue
            expected = source.get(method)
            if expected is None:
                issues.append(f"{name}: missing source row for {label!r}")
                continue
            if not nearly_equal(parse_float(acc), float(expected["acc"])):
                issues.append(f"{name}: acc mismatch for {label!r} table={acc}, expected={float(expected['acc']):.6f}")
            if abs(float(bytes_val) - round(float(expected["bytes"]))) > 0.5:
                issues.append(f"{name}: bytes mismatch for {label!r} table={bytes_val}, expected={float(expected['bytes']):.1f}")
    return issues


def check_significance() -> list[str]:
    rows = read_csv("runs/if_significance_report.csv")
    issues: list[str] = []
    by_key = {(r["setting"], r["comparison"]): r for r in rows}
    for key in [
        ("MHEALTH", "CHOP eq. - CProto eq."),
        ("MHEALTH", "CHOP eq. - zero-fill RFF eq."),
        ("MHEALTH", "CHOP eq. - shared-view RFF eq."),
        ("UCI HAR", "Adaptive CHOP - CHOP eq."),
        ("PAMAP2", "Adaptive CHOP - CHOP eq."),
    ]:
        r = by_key.get(key)
        if not r:
            issues.append(f"significance: missing {key}")
            continue
        if float(r["p_holm"]) < 1e-4:
            issues.append(f"significance: suspiciously tiny MHEALTH Holm p for {key}: {r['p_holm']}")
        if not r.get("p_two_sided_holm"):
            issues.append(f"significance: missing two-sided Holm p for {key}")
    return issues


def main() -> None:
    all_issues: list[str] = []
    sections: list[str] = ["# IF Result Audit", ""]
    for check in CHECKS:
        issues = check_table(check)
        all_issues.extend(issues)
        sections.append(f"- {check.name}: {'PASS' if not issues else 'FAIL'}")
        for issue in issues[:8]:
            sections.append(f"  - {issue}")
        if len(issues) > 8:
            sections.append(f"  - ... {len(issues) - 8} more")
    eq_issues = check_equal_bytes()
    strict_table_issues = check_strict_tables()
    sig_issues = check_significance()
    all_issues.extend(eq_issues)
    all_issues.extend(strict_table_issues)
    all_issues.extend(sig_issues)
    sections.append(f"- strict equal-byte payloads: {'PASS' if not eq_issues else 'FAIL'}")
    for issue in eq_issues:
        sections.append(f"  - {issue}")
    sections.append(f"- strict equal-byte table values: {'PASS' if not strict_table_issues else 'FAIL'}")
    for issue in strict_table_issues:
        sections.append(f"  - {issue}")
    sections.append(f"- significance sanity checks: {'PASS' if not sig_issues else 'FAIL'}")
    for issue in sig_issues:
        sections.append(f"  - {issue}")
    sections.extend(["", f"Total issues: {len(all_issues)}"])
    out = ROOT / "runs" / "if_result_audit.md"
    out.write_text("\n".join(sections), encoding="utf-8")
    print(out)
    if all_issues:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

