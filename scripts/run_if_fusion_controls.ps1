$ErrorActionPreference = "Stop"

$Python = "python"
$env:PYTHONPATH = ".qdeps;."
$env:MPLCONFIGDIR = ".mplcache"

function Invoke-IFFusionRun {
    param(
        [string]$Name,
        [string]$DatasetPath,
        [int]$NTrain,
        [int]$NTest,
        [int]$Seed
    )

    $Out = "runs\if_fusion_fullclass_$($Name)_seed$Seed"
    $Metrics = Join-Path $Out "metrics.json"
    if (Test-Path $Metrics) {
        Write-Host "Skipping existing $Out"
        return
    }

    Write-Host "Running $Out"
    & $Python -m qprotohop `
        "--out" $Out `
        "--dataset" "npz" `
        "--dataset-path" $DatasetPath `
        "--readout-backend" "synthetic" `
        "--n-classes" "10" `
        "--n-train" "$NTrain" `
        "--n-test" "$NTest" `
        "--clients" "20" `
        "--rounds" "15" `
        "--eval-every" "15" `
        "--participation" "0.8" `
        "--dirichlet-alpha" "0.5" `
        "--methods" "schema_zero_fill,schema_mask_only,no_schema,forced_canonical,shared_observable,qproto_proto,qproto_cproto,qproto_chop,qproto_masked,qproto_masked_hop" `
        "--observables" "256" `
        "--obs-per-client" "96" `
        "--observable-overlap" "0.8" `
        "--compressed-observables" "96" `
        "--compressed-key-policy" "variance" `
        "--sketch-dim" "192" `
        "--hop-dim" "96" `
        "--bandwidth" "6.0" `
        "--anchor-size" "192" `
        "--probe-size" "0" `
        "--shots" "64,128,256,1024" `
        "--eval-shots" "1024" `
        "--seed" "$Seed" `
        "--hop-weight" "0.12"
    if ($LASTEXITCODE -ne 0) {
        throw "qprotohop failed for $Out with exit code $LASTEXITCODE"
    }
}

$Datasets = @(
    @{ Name = "mnist10"; Path = "data\mnist.npz"; Train = 8000; Test = 2000 },
    @{ Name = "fashion10"; Path = "data\fashion_mnist.npz"; Train = 8000; Test = 2000 },
    @{ Name = "cifar10"; Path = "data\cifar10_feat_resnet18_sz32_pt.npz"; Train = 12000; Test = 3000 }
)

foreach ($Dataset in $Datasets) {
    foreach ($Seed in 0,1,2,3,4) {
        Invoke-IFFusionRun `
            -Name $Dataset.Name `
            -DatasetPath $Dataset.Path `
            -NTrain $Dataset.Train `
            -NTest $Dataset.Test `
            -Seed $Seed
    }
}

& $Python "scripts\collect_results.py" "--root" "runs" "--out" "runs\summary.csv"
if ($LASTEXITCODE -ne 0) { throw "collect_results.py failed with exit code $LASTEXITCODE" }
& $Python "scripts\report_if_fusion_controls.py" "--summary" "runs\summary.csv" "--out" "runs\if_fusion_controls_report.csv" "--md" "runs\if_fusion_controls_report.md" "--tex" "latex_qproto_hop\tables\table_if_fusion_controls.tex"
if ($LASTEXITCODE -ne 0) { throw "report_if_fusion_controls.py failed with exit code $LASTEXITCODE" }

