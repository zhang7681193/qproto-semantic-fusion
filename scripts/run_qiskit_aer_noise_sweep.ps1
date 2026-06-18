$ErrorActionPreference = "Stop"

$Python = "python"
$env:PYTHONPATH = ".qdeps;."
$env:MPLCONFIGDIR = ".mplcache"

function Invoke-QiskitNoiseRun {
    param(
        [string]$Tag,
        [int]$Seed,
        [int]$Depth,
        [int]$BackendShots,
        [double]$Depol1,
        [double]$Depol2,
        [double]$ReadoutP
    )

    $Dataset = "data\mnist4_qiskit_noise_$($Tag)_seed$Seed.npz"
    if (-not (Test-Path $Dataset)) {
        & $Python "scripts\prepare_qiskit_aer_readout_npz.py" `
            "--source" "data\mnist.npz" `
            "--out" $Dataset `
            "--n-classes" "4" `
            "--n-train" "240" `
            "--n-test" "100" `
            "--n-qubits" "4" `
            "--depth" "$Depth" `
            "--shots" "$BackendShots" `
            "--depol1" "$Depol1" `
            "--depol2" "$Depol2" `
            "--readout-p" "$ReadoutP" `
            "--chunk-size" "240" `
            "--seed" "$Seed"
    }

    $Out = "runs\qiskit_noise_$($Tag)_seed$Seed"
    $Metrics = Join-Path $Out "metrics.json"
    if (Test-Path $Metrics) {
        Write-Host "Skipping existing $Out"
        return
    }

    & $Python -m qprotohop `
        "--out" $Out `
        "--dataset" "npz" `
        "--dataset-path" $Dataset `
        "--readout-backend" "precomputed" `
        "--n-classes" "4" `
        "--n-train" "240" `
        "--n-test" "100" `
        "--clients" "8" `
        "--rounds" "12" `
        "--eval-every" "12" `
        "--participation" "0.75" `
        "--dirichlet-alpha" "0.5" `
        "--methods" "fedadam_schema,fedproto_schema,shared_observable,no_schema,wrong_schema,qproto_masked,qproto_cproto,qproto_chop,qproto_masked_hop" `
        "--observables" "12" `
        "--obs-per-client" "8" `
        "--observable-overlap" "0.5" `
        "--compressed-observables" "8" `
        "--sketch-dim" "32" `
        "--hop-dim" "16" `
        "--bandwidth" "2.0" `
        "--anchor-size" "32" `
        "--shots" "$BackendShots" `
        "--eval-shots" "$BackendShots" `
        "--shot-noise-scale" "0.0" `
        "--readout-p" "0.0" `
        "--readout-std" "0.0" `
        "--depol-p" "0.0" `
        "--depol-std" "0.0" `
        "--seed" "$Seed" `
        "--hop-weight" "0.12" `
        "--server-lr" "0.05" `
        "--local-epochs" "8" `
        "--lr" "0.2"
}

$Settings = @(
    @{ Tag = "clean"; Depth = 1; Shots = 1024; Depol1 = 0.000; Depol2 = 0.000; Readout = 0.00 },
    @{ Tag = "lowshot"; Depth = 1; Shots = 128; Depol1 = 0.002; Depol2 = 0.010; Readout = 0.02 },
    @{ Tag = "readout_high"; Depth = 1; Shots = 512; Depol1 = 0.002; Depol2 = 0.010; Readout = 0.08 },
    @{ Tag = "depol_high"; Depth = 1; Shots = 512; Depol1 = 0.010; Depol2 = 0.040; Readout = 0.02 },
    @{ Tag = "depth2"; Depth = 2; Shots = 512; Depol1 = 0.002; Depol2 = 0.010; Readout = 0.02 }
)

foreach ($Setting in $Settings) {
    foreach ($Seed in 0,1,2,3,4) {
        Invoke-QiskitNoiseRun `
            -Tag $Setting.Tag `
            -Seed $Seed `
            -Depth $Setting.Depth `
            -BackendShots $Setting.Shots `
            -Depol1 $Setting.Depol1 `
            -Depol2 $Setting.Depol2 `
            -ReadoutP $Setting.Readout
    }
}

& $Python "scripts\collect_results.py" "--root" "runs" "--out" "runs\summary.csv"
& $Python "scripts\report_qiskit_noise_sweep.py" "--summary" "runs\summary.csv" "--out" "runs\qiskit_noise_sweep_report.csv" "--md" "runs\qiskit_noise_sweep_report.md"

