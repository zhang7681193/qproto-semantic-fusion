$ErrorActionPreference = "Stop"

$Python = "python"
$env:PYTHONPATH = ".qdeps;."

function Invoke-MatchedControl {
    param(
        [string]$Out,
        [string]$DatasetPath,
        [int]$NTrain,
        [int]$NTest,
        [int]$Seed
    )

    $Metrics = Join-Path $Out "metrics.csv"
    if (Test-Path $Metrics) {
        Write-Host "Skipping existing $Out"
        return
    }

    Write-Host "Running $Out"
    & $Python -m qprotohop `
        "--out" $Out `
        "--dataset" "npz" `
        "--dataset-path" $DatasetPath `
        "--n-classes" "10" `
        "--n-train" "$NTrain" `
        "--n-test" "$NTest" `
        "--clients" "20" `
        "--rounds" "15" `
        "--eval-every" "15" `
        "--participation" "0.8" `
        "--dirichlet-alpha" "0.5" `
        "--methods" "qproto_proto,shared_observable" `
        "--observables" "256" `
        "--obs-per-client" "96" `
        "--observable-overlap" "0.8" `
        "--sketch-dim" "512" `
        "--hop-dim" "96" `
        "--bandwidth" "6.0" `
        "--anchor-size" "192" `
        "--shots" "64,128,256,1024" `
        "--eval-shots" "1024" `
        "--seed" "$Seed"
}

$Datasets = @(
    @{ Name = "mnist10"; Path = "data\mnist.npz"; Train = 8000; Test = 2000 },
    @{ Name = "fashion10"; Path = "data\fashion_mnist.npz"; Train = 8000; Test = 2000 },
    @{ Name = "cifar10"; Path = "data\cifar10_feat_resnet18_sz32_pt.npz"; Train = 12000; Test = 3000 }
)

foreach ($Dataset in $Datasets) {
    foreach ($Seed in 0,1,2) {
        Invoke-MatchedControl `
            -Out "runs\matched_budget_$($Dataset.Name)_seed$Seed" `
            -DatasetPath $Dataset.Path `
            -NTrain $Dataset.Train `
            -NTest $Dataset.Test `
            -Seed $Seed
    }
}

& $Python "scripts\collect_results.py" "--root" "runs" "--out" "runs\summary.csv"

