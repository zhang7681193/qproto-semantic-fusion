$ErrorActionPreference = "Stop"

$Python = "python"
$env:PYTHONPATH = ".qdeps;."
$env:MPLCONFIGDIR = ".mplcache"

function Invoke-SchemaHeadRun {
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
        [double]$ServerLr = 0.08,
        [int]$LocalEpochs = 8,
        [double]$Lr = 0.25
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
        "--readout-backend" $Backend `
        "--n-classes" "$NClasses" `
        "--n-train" "$NTrain" `
        "--n-test" "$NTest" `
        "--clients" "$Clients" `
        "--rounds" "$Rounds" `
        "--eval-every" "$Rounds" `
        "--participation" "$Participation" `
        "--dirichlet-alpha" "$Alpha" `
        "--methods" "fedavg_schema,fedprox_schema,fedadam_schema,fedproto_schema,qproto_cproto,qproto_chop,qproto_masked_hop" `
        "--observables" "$Observables" `
        "--obs-per-client" "$ObsPerClient" `
        "--observable-overlap" "$Overlap" `
        "--compressed-observables" "$CompressedObservables" `
        "--compressed-key-policy" "variance" `
        "--sketch-dim" "$SketchDim" `
        "--hop-dim" "$HopDim" `
        "--bandwidth" "$Bandwidth" `
        "--anchor-size" "$AnchorSize" `
        "--shots" $Shots `
        "--eval-shots" "$EvalShots" `
        "--seed" "$Seed" `
        "--hop-weight" "$HopWeight" `
        "--server-lr" "$ServerLr" `
        "--local-epochs" "$LocalEpochs" `
        "--lr" "$Lr"
}

$FullDatasets = @(
    @{ Name = "mnist10"; Path = "data\mnist.npz"; Train = 8000; Test = 2000 },
    @{ Name = "fashion10"; Path = "data\fashion_mnist.npz"; Train = 8000; Test = 2000 },
    @{ Name = "cifar10"; Path = "data\cifar10_feat_resnet18_sz32_pt.npz"; Train = 12000; Test = 3000 }
)

foreach ($Dataset in $FullDatasets) {
    foreach ($Seed in 0,1,2) {
        Invoke-SchemaHeadRun `
            -Out "runs\schema_head_baseline_$($Dataset.Name)_seed$Seed" `
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
            -HopWeight 0.12 `
            -ServerLr 0.06
    }
}

$QiskitData = @{
    0 = "data\mnist4_qiskit_aer_readout.npz"
    1 = "data\mnist4_qiskit_aer_readout_seed1.npz"
    2 = "data\mnist4_qiskit_aer_readout_seed2.npz"
}

foreach ($Seed in 0,1,2) {
    Invoke-SchemaHeadRun `
        -Out "runs\schema_head_baseline_qiskit_aer_seed$Seed" `
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
        -HopWeight 0.12 `
        -ServerLr 0.05 `
        -LocalEpochs 8 `
        -Lr 0.2
}

foreach ($Seed in 0,1,2) {
    Invoke-SchemaHeadRun `
        -Out "runs\schema_head_baseline_pennylane_highorder_seed$Seed" `
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
        -HopWeight 3.0 `
        -ServerLr 0.06 `
        -LocalEpochs 8 `
        -Lr 0.25
}

& $Python "scripts\collect_results.py" "--root" "runs" "--out" "runs\summary.csv"
& $Python "scripts\report_topjournal_pilots.py" "--summary" "runs\summary.csv" "--out" "runs\topjournal_pilot_tables.csv" "--md" "runs\topjournal_pilot_report.md"

