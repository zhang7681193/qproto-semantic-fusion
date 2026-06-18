$ErrorActionPreference = "Stop"

$Python = "python"
$env:PYTHONPATH = ".qdeps;."
$env:MPLCONFIGDIR = ".mplcache"

& $Python "scripts\run_nonquantum_if_benchmark.py" `
    "--dataset" "wdbc" `
    "--seeds" "0,1,2,3,4,5,6,7,8,9" `
    "--anchor-size" "256" `
    "--views-per-client" "5" `
    "--common-views" "1" `
    "--chop-keys" "18" `
    "--equal-cproto-keys" "30" `
    "--hop-dim" "12" `
    "--hop-weight" "0.1" `
    "--torch-epochs" "25" `
    "--key-policy" "variance" `
    "--out-csv" "runs\if_wdbc_fusion.csv" `
    "--out-md" "runs\if_wdbc_fusion_report.md" `
    "--out-tex" "latex_qproto_hop_IF\tables\table_if_wdbc_fusion.tex" `
    "--out-equal-tex" "latex_qproto_hop_IF\tables\table_strict_equal_byte_wdbc.tex"

if ($LASTEXITCODE -ne 0) {
    throw "WDBC IF benchmark failed with exit code $LASTEXITCODE"
}

