$ErrorActionPreference = "Stop"

$Python = "python"
$env:PYTHONPATH = ".qdeps;."
$env:MPLCONFIGDIR = ".mplcache"

& $Python "scripts\run_nonquantum_if_benchmark.py" `
    "--dataset" "mfeat_interaction" `
    "--seeds" "0,1,2,3,4" `
    "--anchor-size" "700" `
    "--views-per-client" "3" `
    "--common-views" "1" `
    "--chop-keys" "160" `
    "--equal-cproto-keys" "0" `
    "--hop-dim" "128" `
    "--hop-weight" "0.35" `
    "--pca-rank" "24" `
    "--ridge-alpha" "0.1" `
    "--torch-epochs" "25" `
    "--key-policy" "variance" `
    "--out-csv" "runs\if_mfeat_interaction_fusion.csv" `
    "--out-md" "runs\if_mfeat_interaction_fusion_report.md" `
    "--out-tex" "latex_qproto_hop_IF\tables\table_if_mfeat_interaction.tex" `
    "--out-equal-tex" "latex_qproto_hop_IF\tables\table_strict_equal_byte_mfeat_interaction.tex"

if ($LASTEXITCODE -ne 0) {
    throw "MFeat interaction IF benchmark failed with exit code $LASTEXITCODE"
}

