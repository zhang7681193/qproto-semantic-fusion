$ErrorActionPreference = "Stop"

$Python = "python"
$env:PYTHONPATH = ".qdeps;."
$env:MPLCONFIGDIR = ".mplcache"

& $Python "scripts\run_nonquantum_if_benchmark.py" `
    "--dataset" "hydraulic" `
    "--hydraulic-target" "cooler" `
    "--seeds" "0,1,2,3,4" `
    "--n-train" "0" `
    "--n-test" "0" `
    "--anchor-size" "900" `
    "--views-per-client" "9" `
    "--common-views" "2" `
    "--chop-keys" "96" `
    "--equal-cproto-keys" "0" `
    "--hop-dim" "96" `
    "--hop-weight" "0.3" `
    "--pca-rank" "24" `
    "--ridge-alpha" "0.1" `
    "--torch-epochs" "20" `
    "--key-policy" "anchor_covariance" `
    "--out-csv" "runs\if_hydraulic_cooler_fusion.csv" `
    "--out-md" "runs\if_hydraulic_cooler_fusion_report.md" `
    "--out-tex" "latex_qproto_hop_IF\tables\table_if_hydraulic_cooler_fusion.tex" `
    "--out-equal-tex" "latex_qproto_hop_IF\tables\table_strict_equal_byte_hydraulic_cooler.tex"

if ($LASTEXITCODE -ne 0) {
    throw "Hydraulic IF benchmark failed with exit code $LASTEXITCODE"
}

