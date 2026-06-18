$ErrorActionPreference = "Stop"

$Python = "python"
$env:PYTHONPATH = "."
$env:MPLCONFIGDIR = ".mplcache"

& $Python "scripts\run_nonquantum_if_benchmark.py" `
    "--dataset" "uci_har" `
    "--seeds" "0,1,2,3,4" `
    "--n-train" "5000" `
    "--n-test" "1500" `
    "--anchor-size" "512" `
    "--chop-keys" "128" `
    "--equal-cproto-keys" "160" `
    "--hop-dim" "64" `
    "--hop-weight" "0.05" `
    "--include-adaptive-chop" `
    "--adaptive-calib-frac" "0.25" `
    "--adaptive-margin" "0.0" `
    "--torch-epochs" "25" `
    "--key-policy" "variance" `
    "--hop-pair-policy" "cross_group_covariance" `
    "--adaptive-alpha-grid" "0,0.25,0.5,0.75,1"

if ($LASTEXITCODE -ne 0) {
    throw "UCI HAR IF benchmark failed with exit code $LASTEXITCODE"
}

