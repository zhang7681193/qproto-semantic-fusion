$ErrorActionPreference = "Stop"

$Python = "python"
$env:PYTHONPATH = ".qdeps;."
$env:MPLCONFIGDIR = ".mplcache"

function Invoke-MaskedRun {
    param(
        [string]$Out,
        [string]$DatasetPath,
        [string]$Backend,
        [int]$NClasses,
        [int]$NTrain,
        [int]$NTest,
        [int]$Clients,
        [int]$Rounds,
        [double]$Participation,
        [double]$Alpha,
        [int]$Observables,
        [int]$ObsPerClient,
        [double]$Overlap,
        [int]$SketchDim,
        [int]$HopDim,
        [double]$Bandwidth,
        [int]$AnchorSize,
        [string]$Shots,
        [int]$EvalShots,
        [int]$Seed,
        [string]$CommonPolicy = "random"
    )

    $Metrics = Join-Path $Out "metrics.csv"
    if (Test-Path $Metrics) {
        Write-Host "Skipping existing $Out"
        return
    }

    Write-Host "Running $Out"
    $RunArgs = @(
        "-m", "qprotohop",
        "--out", $Out,
        "--dataset", "npz",
        "--dataset-path", $DatasetPath,
        "--readout-backend", $Backend,
        "--n-classes", "$NClasses",
        "--n-train", "$NTrain",
        "--n-test", "$NTest",
        "--clients", "$Clients",
        "--rounds", "$Rounds",
        "--eval-every", "$Rounds",
        "--participation", "$Participation",
        "--dirichlet-alpha", "$Alpha",
        "--methods", "qproto_masked",
        "--observables", "$Observables",
        "--obs-per-client", "$ObsPerClient",
        "--observable-overlap", "$Overlap",
        "--common-policy", $CommonPolicy,
        "--sketch-dim", "$SketchDim",
        "--hop-dim", "$HopDim",
        "--bandwidth", "$Bandwidth",
        "--anchor-size", "$AnchorSize",
        "--shots", $Shots,
        "--eval-shots", "$EvalShots",
        "--seed", "$Seed"
    )
    & $Python @RunArgs
}

$FullDatasets = @(
    @{ Name = "mnist10"; Path = "data\mnist.npz"; Train = 8000; Test = 2000 },
    @{ Name = "fashion10"; Path = "data\fashion_mnist.npz"; Train = 8000; Test = 2000 },
    @{ Name = "cifar10"; Path = "data\cifar10_feat_resnet18_sz32_pt.npz"; Train = 12000; Test = 3000 }
)

foreach ($Dataset in $FullDatasets) {
    foreach ($Seed in 0,1,2) {
        Invoke-MaskedRun `
            -Out "runs\masked_$($Dataset.Name)_seed$Seed" `
            -DatasetPath $Dataset.Path `
            -Backend "synthetic" `
            -NClasses 10 `
            -NTrain $Dataset.Train `
            -NTest $Dataset.Test `
            -Clients 20 `
            -Rounds 15 `
            -Participation 0.8 `
            -Alpha 0.5 `
            -Observables 256 `
            -ObsPerClient 96 `
            -Overlap 0.8 `
            -SketchDim 192 `
            -HopDim 96 `
            -Bandwidth 6.0 `
            -AnchorSize 192 `
            -Shots "64,128,256,1024" `
            -EvalShots 1024 `
            -Seed $Seed
    }
}

$QiskitData = @{
    0 = "data\mnist4_qiskit_aer_readout.npz"
    1 = "data\mnist4_qiskit_aer_readout_seed1.npz"
    2 = "data\mnist4_qiskit_aer_readout_seed2.npz"
}

foreach ($Seed in 0,1,2) {
    Invoke-MaskedRun `
        -Out "runs\masked_qiskit_aer_seed$Seed" `
        -DatasetPath $QiskitData[$Seed] `
        -Backend "precomputed" `
        -NClasses 4 `
        -NTrain 320 `
        -NTest 120 `
        -Clients 8 `
        -Rounds 12 `
        -Participation 0.75 `
        -Alpha 0.5 `
        -Observables 12 `
        -ObsPerClient 8 `
        -Overlap 0.5 `
        -SketchDim 32 `
        -HopDim 16 `
        -Bandwidth 2.0 `
        -AnchorSize 32 `
        -Shots "64,128,256,1024" `
        -EvalShots 1024 `
        -Seed $Seed
}

foreach ($Seed in 0,1,2) {
    Invoke-MaskedRun `
        -Out "runs\masked_pennylane_mnist4_pca_seed$Seed" `
        -DatasetPath "data\mnist4_pennylane_pca_readout.npz" `
        -Backend "precomputed" `
        -NClasses 4 `
        -NTrain 1200 `
        -NTest 500 `
        -Clients 16 `
        -Rounds 20 `
        -Participation 0.75 `
        -Alpha 0.5 `
        -Observables 60 `
        -ObsPerClient 24 `
        -Overlap 0.5 `
        -SketchDim 96 `
        -HopDim 48 `
        -Bandwidth 3.0 `
        -AnchorSize 96 `
        -Shots "64,128,256,1024" `
        -EvalShots 1024 `
        -Seed $Seed
}

foreach ($Seed in 0,1,2) {
    Invoke-MaskedRun `
        -Out "runs\masked_pennylane_private_signal_seed$Seed" `
        -DatasetPath "data\mnist4_pennylane_private_signal.npz" `
        -Backend "precomputed" `
        -NClasses 4 `
        -NTrain 1200 `
        -NTest 500 `
        -Clients 16 `
        -Rounds 20 `
        -Participation 0.75 `
        -Alpha 0.5 `
        -Observables 60 `
        -ObsPerClient 24 `
        -Overlap 0.25 `
        -SketchDim 96 `
        -HopDim 48 `
        -Bandwidth 3.0 `
        -AnchorSize 96 `
        -Shots "64,128,256,1024" `
        -EvalShots 1024 `
        -Seed $Seed `
        -CommonPolicy "prefix"
}

& $Python "scripts\collect_results.py" "--root" "runs" "--out" "runs\summary.csv"
& $Python "scripts\report_topjournal_pilots.py" "--summary" "runs\summary.csv" "--out" "runs\topjournal_pilot_tables.csv" "--md" "runs\topjournal_pilot_report.md"

