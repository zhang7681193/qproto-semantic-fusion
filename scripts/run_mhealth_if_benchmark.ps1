$ErrorActionPreference = "Stop"

$Python = "python"
$env:PYTHONPATH = "."
$env:MPLCONFIGDIR = ".mplcache"

& $Python "scripts\run_nonquantum_if_benchmark.py" `
    "--dataset" "mhealth" `
    "--mhealth-split" "subject" `
    "--mhealth-window" "128" `
    "--mhealth-stride" "64" `
    "--mhealth-max-windows-per-subject" "900" `
    "--seeds" "0,1,2,3,4,5,6,7,8,9" `
    "--n-train" "0" `
    "--n-test" "0" `
    "--anchor-size" "900" `
    "--views-per-client" "5" `
    "--common-views" "1" `
    "--chop-keys" "96" `
    "--equal-cproto-keys" "0" `
    "--hop-dim" "96" `
    "--hop-weight" "0.05" `
    "--include-adaptive-chop" `
    "--adaptive-calib-frac" "0.25" `
    "--adaptive-margin" "0.0" `
    "--pca-rank" "24" `
    "--ridge-alpha" "0.1" `
    "--torch-epochs" "20" `
    "--key-policy" "anchor_covariance" `
    "--hop-pair-policy" "cross_group_covariance" `
    "--adaptive-alpha-grid" "0,0.25,0.5,0.75,1" `
    "--out-csv" "runs\if_mhealth_fusion.csv" `
    "--out-md" "runs\if_mhealth_fusion_report.md" `
    "--out-tex" "latex_qproto_hop_IF\tables\table_if_mhealth_fusion.tex" `
    "--out-equal-tex" "latex_qproto_hop_IF\tables\table_strict_equal_byte_mhealth.tex"

if ($LASTEXITCODE -ne 0) {
    throw "MHEALTH IF benchmark failed with exit code $LASTEXITCODE"
}

