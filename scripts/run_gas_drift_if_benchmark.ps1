$ErrorActionPreference = "Stop"

$Python = "python"
$env:PYTHONPATH = "."
$env:MPLCONFIGDIR = ".mplcache"

& $Python "scripts\run_nonquantum_if_benchmark.py" `
    "--dataset" "gas_drift" `
    "--gas-split" "random" `
    "--seeds" "0,1,2,3,4" `
    "--n-train" "0" `
    "--n-test" "0" `
    "--anchor-size" "900" `
    "--views-per-client" "8" `
    "--common-views" "2" `
    "--chop-keys" "96" `
    "--equal-cproto-keys" "0" `
    "--hop-dim" "96" `
    "--hop-weight" "0.1" `
    "--pca-rank" "24" `
    "--ridge-alpha" "0.1" `
    "--torch-epochs" "20" `
    "--key-policy" "variance" `
    "--hop-pair-policy" "cross_group_covariance" `
    "--include-adaptive-chop" `
    "--adaptive-calib-frac" "0.25" `
    "--adaptive-margin" "0.0" `
    "--out-csv" "runs\if_gas_drift_fusion.csv" `
    "--out-md" "runs\if_gas_drift_fusion_report.md" `
    "--out-tex" "latex_qproto_hop_IF\tables\table_if_gas_drift_fusion.tex" `
    "--out-equal-tex" "latex_qproto_hop_IF\tables\table_strict_equal_byte_gas_drift.tex"

if ($LASTEXITCODE -ne 0) {
    throw "Gas Drift IF benchmark failed with exit code $LASTEXITCODE"
}

