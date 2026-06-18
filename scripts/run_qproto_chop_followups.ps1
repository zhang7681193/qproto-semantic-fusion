$ErrorActionPreference = "Stop"

$Python = "python"
$env:PYTHONPATH = ".qdeps;."
$env:MPLCONFIGDIR = ".mplcache"

function Invoke-ChopRun {
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
        [int]$CompressedObservables,
        [int]$SketchDim,
        [int]$HopDim,
        [double]$Bandwidth,
        [int]$AnchorSize,
        [string]$Shots,
        [int]$EvalShots,
        [int]$Seed,
        [double]$HopWeight,
        [string]$Methods = "qproto_cproto,qproto_chop",
        [string]$CommonPolicy = "random"
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
        "--readout-backend" $Backend `
        "--n-classes" "$NClasses" `
        "--n-train" "$NTrain" `
        "--n-test" "$NTest" `
        "--clients" "$Clients" `
        "--rounds" "$Rounds" `
        "--eval-every" "$Rounds" `
        "--participation" "$Participation" `
        "--dirichlet-alpha" "$Alpha" `
        "--methods" $Methods `
        "--observables" "$Observables" `
        "--obs-per-client" "$ObsPerClient" `
        "--observable-overlap" "$Overlap" `
        "--compressed-observables" "$CompressedObservables" `
        "--compressed-key-policy" "variance" `
        "--common-policy" $CommonPolicy `
        "--sketch-dim" "$SketchDim" `
        "--hop-dim" "$HopDim" `
        "--bandwidth" "$Bandwidth" `
        "--anchor-size" "$AnchorSize" `
        "--shots" $Shots `
        "--eval-shots" "$EvalShots" `
        "--seed" "$Seed" `
        "--hop-weight" "$HopWeight"
}

$FullDatasets = @(
    @{ Name = "mnist10"; Path = "data\mnist.npz"; Train = 8000; Test = 2000 },
    @{ Name = "fashion10"; Path = "data\fashion_mnist.npz"; Train = 8000; Test = 2000 },
    @{ Name = "cifar10"; Path = "data\cifar10_feat_resnet18_sz32_pt.npz"; Train = 12000; Test = 3000 }
)

foreach ($Dataset in $FullDatasets) {
    foreach ($Seed in 0,1,2) {
        Invoke-ChopRun `
            -Out "runs\chop_$($Dataset.Name)_k96_seed$Seed" `
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
            -CompressedObservables 96 `
            -SketchDim 192 `
            -HopDim 96 `
            -Bandwidth 6.0 `
            -AnchorSize 192 `
            -Shots "64,128,256,1024" `
            -EvalShots 1024 `
            -Seed $Seed `
            -HopWeight 0.12
    }
}

$QiskitData = @{
    0 = "data\mnist4_qiskit_aer_readout.npz"
    1 = "data\mnist4_qiskit_aer_readout_seed1.npz"
    2 = "data\mnist4_qiskit_aer_readout_seed2.npz"
}

foreach ($Seed in 0,1,2) {
    Invoke-ChopRun `
        -Out "runs\chop_qiskit_aer_k8_seed$Seed" `
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
        -CompressedObservables 8 `
        -SketchDim 32 `
        -HopDim 16 `
        -Bandwidth 2.0 `
        -AnchorSize 32 `
        -Shots "64,128,256,1024" `
        -EvalShots 1024 `
        -Seed $Seed `
        -HopWeight 0.12
}

foreach ($Seed in 0,1,2) {
    Invoke-ChopRun `
        -Out "runs\chop_pennylane_highorder_k24_seed$Seed" `
        -DatasetPath "data\pennylane_highorder_readout.npz" `
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
        -Overlap 0.35 `
        -CompressedObservables 24 `
        -SketchDim 96 `
        -HopDim 96 `
        -Bandwidth 3.0 `
        -AnchorSize 96 `
        -Shots "64,128,256,1024" `
        -EvalShots 1024 `
        -Seed $Seed `
        -HopWeight 3.0
}

& $Python "scripts\collect_results.py" "--root" "runs" "--out" "runs\summary.csv"

