$ErrorActionPreference = "Stop"

$Python = "python"
$env:PYTHONPATH = ".qdeps;."
$env:MPLCONFIGDIR = ".mplcache"

function Invoke-QProtoSweepRun {
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
        [string]$Methods,
        [double]$ServerLr = 0.06,
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
        "--methods" $Methods `
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

$MainMethods = "fedavg_schema,fedadam_schema,fedproto_schema,shared_observable,no_schema,wrong_schema,qproto_cproto,qproto_chop,qproto_masked_hop"
$HopMethods = "fedadam_schema,fedproto_schema,shared_observable,no_schema,wrong_schema,qproto_cproto,qproto_chop,qproto_masked_hop"

foreach ($Clients in 10,20,50,100) {
    foreach ($Seed in 0,1,2) {
        Invoke-QProtoSweepRun `
            -Out "runs\scale_mnist10_c$($Clients)_seed$Seed" `
            -DatasetPath "data\mnist.npz" `
            -Backend "synthetic" `
            -NClasses 10 `
            -NTrain 8000 `
            -NTest 2000 `
            -Clients $Clients `
            -Rounds 12 `
            -Participation 0.5 `
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
            -Methods $MainMethods
    }
}

foreach ($Overlap in "0.20","0.40","0.60","0.80","1.00") {
    $Tag = $Overlap.Replace(".","p")
    foreach ($Seed in 0,1,2) {
        Invoke-QProtoSweepRun `
            -Out "runs\overlap_mnist10_o$($Tag)_seed$Seed" `
            -DatasetPath "data\mnist.npz" `
            -Backend "synthetic" `
            -NClasses 10 `
            -NTrain 8000 `
            -NTest 2000 `
            -Clients 20 `
            -Rounds 12 `
            -Participation 0.5 `
            -Alpha 0.5 `
            -Observables 256 `
            -ObsPerClient 96 `
            -Overlap $Overlap `
            -CompressedObservables 96 `
            -SketchDim 192 `
            -HopDim 96 `
            -Bandwidth 6.0 `
            -AnchorSize 192 `
            -Shots "64,128,256,1024" `
            -EvalShots 1024 `
            -Seed $Seed `
            -HopWeight 0.12 `
            -Methods $MainMethods
    }
}

foreach ($Overlap in "0.20","0.35","0.50","0.80") {
    $Tag = $Overlap.Replace(".","p")
    foreach ($Seed in 0,1,2) {
        Invoke-QProtoSweepRun `
            -Out "runs\overlap_pennylane_highorder_o$($Tag)_seed$Seed" `
            -DatasetPath "data\pennylane_highorder_readout.npz" `
            -Backend "precomputed" `
            -NClasses 4 `
            -NTrain 1200 `
            -NTest 500 `
            -Clients 16 `
            -Rounds 16 `
            -Participation 0.75 `
            -Alpha 0.5 `
            -Observables 60 `
            -ObsPerClient 24 `
            -Overlap $Overlap `
            -CompressedObservables 24 `
            -SketchDim 96 `
            -HopDim 96 `
            -Bandwidth 3.0 `
            -AnchorSize 96 `
            -Shots "64,128,256,1024" `
            -EvalShots 1024 `
            -Seed $Seed `
            -HopWeight 3.0 `
            -Methods $HopMethods `
            -ServerLr 0.06 `
            -LocalEpochs 8 `
            -Lr 0.25
    }
}

& $Python "scripts\collect_results.py" "--root" "runs" "--out" "runs\summary.csv"
& $Python "scripts\report_scale_overlap.py" "--summary" "runs\summary.csv" "--out" "runs\scale_overlap_report.csv" "--md" "runs\scale_overlap_report.md"

