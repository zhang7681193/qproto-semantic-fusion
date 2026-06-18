$ErrorActionPreference = "Stop"

$Python = "python"
$env:PYTHONPATH = ".qdeps;."
$env:MPLCONFIGDIR = ".mplcache"

function Invoke-FinalFullClassRun {
    param(
        [string]$Name,
        [string]$DatasetPath,
        [int]$NTrain,
        [int]$NTest,
        [int]$Seed
    )

    $Out = "runs\final_fullclass_$($Name)_seed$Seed"
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
        "--methods" "fedavg_forced,fedprox_forced,fedadam_forced,fedavg_schema,fedprox_schema,fedadam_schema,scaffold_schema,feddyn_schema,fedproto_forced,fedproto_schema,shared_observable,no_schema,wrong_schema,qproto_cproto,qproto_chop,qproto_masked,qproto_masked_hop" `
        "--observables" "256" `
        "--obs-per-client" "96" `
        "--observable-overlap" "0.8" `
        "--compressed-observables" "96" `
        "--compressed-key-policy" "variance" `
        "--sketch-dim" "192" `
        "--hop-dim" "96" `
        "--bandwidth" "6.0" `
        "--anchor-size" "192" `
        "--shots" "64,128,256,1024" `
        "--eval-shots" "1024" `
        "--seed" "$Seed" `
        "--hop-weight" "0.12" `
        "--server-lr" "0.06" `
        "--local-epochs" "8" `
        "--lr" "0.25" `
        "--feddyn-alpha" "0.02"
}

$Datasets = @(
    @{ Name = "mnist10"; Path = "data\mnist.npz"; Train = 8000; Test = 2000 },
    @{ Name = "fashion10"; Path = "data\fashion_mnist.npz"; Train = 8000; Test = 2000 },
    @{ Name = "cifar10"; Path = "data\cifar10_feat_resnet18_sz32_pt.npz"; Train = 12000; Test = 3000 }
)

foreach ($Dataset in $Datasets) {
    foreach ($Seed in 0,1,2,3,4) {
        Invoke-FinalFullClassRun `
            -Name $Dataset.Name `
            -DatasetPath $Dataset.Path `
            -NTrain $Dataset.Train `
            -NTest $Dataset.Test `
            -Seed $Seed
    }
}

& $Python "scripts\collect_results.py" "--root" "runs" "--out" "runs\summary.csv"
& $Python "scripts\report_final_fullclass.py" "--summary" "runs\summary.csv" "--out" "runs\final_fullclass_report.csv" "--md" "runs\final_fullclass_report.md"

