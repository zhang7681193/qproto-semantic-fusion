$ErrorActionPreference = "Stop"

$Python = "python"
$env:PYTHONPATH = "."
$env:MPLCONFIGDIR = ".mplcache"

& $Python "scripts\run_nonquantum_if_benchmark.py" `
    "--dataset" "pamap2" `
    "--pamap2-split" "subject" `
    "--pamap2-window" "128" `
    "--pamap2-stride" "64" `
    "--pamap2-max-windows-per-subject" "1200" `
    "--pamap2-subjects" "all" `
    "--seeds" "0,1,2,3,4" `
    "--n-train" "0" `
    "--n-test" "0" `
    "--anchor-size" "1000" `
    "--views-per-client" "6" `
    "--common-views" "1" `
    "--chop-keys" "128" `
    "--equal-cproto-keys" "0" `
    "--hop-dim" "128" `
    "--hop-weight" "0.1" `
    "--include-adaptive-chop" `
    "--adaptive-calib-frac" "0.25" `
    "--adaptive-margin" "0.0" `
    "--pca-rank" "32" `
    "--ridge-alpha" "0.1" `
    "--torch-epochs" "20" `
    "--key-policy" "anchor_covariance" `
    "--hop-pair-policy" "cross_group_covariance" `
    "--adaptive-alpha-grid" "0,0.25,0.5,0.75,1" `
    "--out-csv" "runs\if_pamap2_fusion.csv" `
    "--out-md" "runs\if_pamap2_fusion_report.md" `
    "--out-tex" "latex_qproto_hop_IF\tables\table_if_pamap2_fusion.tex" `
    "--out-equal-tex" "latex_qproto_hop_IF\tables\table_strict_equal_byte_pamap2.tex"

if ($LASTEXITCODE -ne 0) {
    throw "PAMAP2 IF benchmark failed with exit code $LASTEXITCODE"
}

