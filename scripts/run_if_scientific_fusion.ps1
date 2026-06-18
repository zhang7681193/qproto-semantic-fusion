$ErrorActionPreference = "Stop"

$Python = "python"
$env:PYTHONPATH = ".qdeps;."
$env:MPLCONFIGDIR = ".mplcache"

foreach ($Seed in 0,1,2,3,4) {
    $Out = "runs\if_scientific_fusion_seed$Seed"
    $Metrics = Join-Path $Out "metrics.json"
    if (Test-Path $Metrics) {
        Write-Host "Skipping existing $Out"
        continue
    }

    Write-Host "Running $Out"
    & $Python -m qprotohop `
        "--out" $Out `
        "--dataset" "synthetic" `
        "--data-structure" "covariance" `
        "--class-sep" "0.0" `
        "--cov-boost" "6.0" `
        "--n-classes" "5" `
        "--input-dim" "16" `
        "--n-train" "2500" `
        "--n-test" "1000" `
        "--clients" "20" `
        "--rounds" "20" `
        "--eval-every" "20" `
        "--participation" "0.8" `
        "--dirichlet-alpha" "0.8" `
        "--methods" "schema_zero_fill,schema_mask_only,no_schema,forced_canonical,shared_observable,qproto_masked,qproto_masked_hop,qproto_cproto,qproto_chop,fedproto_schema,fedadam_schema" `
        "--observables" "96" `
        "--obs-per-client" "48" `
        "--observable-overlap" "0.45" `
        "--compressed-observables" "48" `
        "--compressed-key-policy" "variance" `
        "--sketch-dim" "96" `
        "--hop-dim" "96" `
        "--bandwidth" "3.0" `
        "--anchor-size" "128" `
        "--probe-size" "0" `
        "--shots" "128,256,512,1024" `
        "--eval-shots" "1024" `
        "--seed" "$Seed" `
        "--hop-weight" "8.0" `
        "--server-lr" "0.08" `
        "--local-epochs" "6" `
        "--lr" "0.25"
    if ($LASTEXITCODE -ne 0) {
        throw "qprotohop failed for $Out with exit code $LASTEXITCODE"
    }
}

& $Python "scripts\collect_results.py" "--root" "runs" "--out" "runs\summary.csv"
if ($LASTEXITCODE -ne 0) { throw "collect_results.py failed with exit code $LASTEXITCODE" }
& $Python "scripts\report_if_scientific_fusion.py" "--summary" "runs\summary.csv" "--out" "runs\if_scientific_fusion_report.csv" "--md" "runs\if_scientific_fusion_report.md" "--tex" "latex_qproto_hop\tables\table_if_scientific_fusion.tex"
if ($LASTEXITCODE -ne 0) { throw "report_if_scientific_fusion.py failed with exit code $LASTEXITCODE" }

