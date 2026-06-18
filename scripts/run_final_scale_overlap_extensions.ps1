$ErrorActionPreference = "Stop"

$Python = "python"
$env:PYTHONPATH = ".qdeps;."
$env:MPLCONFIGDIR = ".mplcache"

function Invoke-ScaleOverlapExtension {
    param(
        [string]$Out,
        [string]$DatasetPath,
        [int]$NTrain,
        [int]$NTest,
        [int]$Clients,
        [double]$Overlap,
        [int]$Seed
    )

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
        "--clients" "$Clients" `
        "--rounds" "12" `
        "--eval-every" "12" `
        "--participation" "0.5" `
        "--dirichlet-alpha" "0.5" `
        "--methods" "fedadam_schema,fedproto_schema,shared_observable,no_schema,wrong_schema,qproto_cproto,qproto_chop,qproto_masked_hop" `
        "--observables" "256" `
        "--obs-per-client" "96" `
        "--observable-overlap" "$Overlap" `
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
        "--lr" "0.25"
}

$Datasets = @(
    @{ Name = "fashion10"; Path = "data\fashion_mnist.npz"; Train = 8000; Test = 2000 },
    @{ Name = "cifar10"; Path = "data\cifar10_feat_resnet18_sz32_pt.npz"; Train = 12000; Test = 3000 }
)

foreach ($Dataset in $Datasets) {
    foreach ($Clients in 50,100) {
        foreach ($Seed in 0,1,2) {
            Invoke-ScaleOverlapExtension `
                -Out "runs\scale_$($Dataset.Name)_c$($Clients)_seed$Seed" `
                -DatasetPath $Dataset.Path `
                -NTrain $Dataset.Train `
                -NTest $Dataset.Test `
                -Clients $Clients `
                -Overlap 0.8 `
                -Seed $Seed
        }
    }
    foreach ($Overlap in "0.20","0.60","1.00") {
        $Tag = $Overlap.Replace(".","p")
        foreach ($Seed in 0,1,2) {
            Invoke-ScaleOverlapExtension `
                -Out "runs\overlap_$($Dataset.Name)_o$($Tag)_seed$Seed" `
                -DatasetPath $Dataset.Path `
                -NTrain $Dataset.Train `
                -NTest $Dataset.Test `
                -Clients 20 `
                -Overlap $Overlap `
                -Seed $Seed
        }
    }
}

& $Python "scripts\collect_results.py" "--root" "runs" "--out" "runs\summary.csv"
& $Python "scripts\report_scale_overlap.py" "--summary" "runs\summary.csv" "--out" "runs\scale_overlap_report.csv" "--md" "runs\scale_overlap_report.md"

