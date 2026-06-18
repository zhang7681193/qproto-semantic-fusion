$ErrorActionPreference = "Stop"

$Python = "python"
$env:PYTHONPATH = ".qdeps;."
$env:MPLCONFIGDIR = ".mplcache"

$Dataset = "data\mnist2_hardware_protocol_aer_readout.npz"

if (-not (Test-Path $Dataset)) {
    & $Python "scripts\prepare_qiskit_hardware_readout_npz.py" `
        "--source" "data\mnist.npz" `
        "--out" $Dataset `
        "--backend-mode" "aer" `
        "--n-classes" "2" `
        "--n-train" "120" `
        "--n-test" "60" `
        "--n-qubits" "4" `
        "--depth" "1" `
        "--shots" "512" `
        "--depol1" "0.002" `
        "--depol2" "0.01" `
        "--readout-p" "0.02" `
        "--chunk-size" "240" `
        "--seed" "0"
}

& $Python -m qprotohop `
    "--out" "runs\hardware_ready_aer_mnist2_seed0" `
    "--dataset" "npz" `
    "--dataset-path" $Dataset `
    "--readout-backend" "precomputed" `
    "--n-classes" "2" `
    "--n-train" "120" `
    "--n-test" "60" `
    "--clients" "6" `
    "--rounds" "10" `
    "--eval-every" "10" `
    "--participation" "0.75" `
    "--dirichlet-alpha" "0.5" `
    "--methods" "fedadam_schema,fedproto_schema,shared_observable,no_schema,wrong_schema,qproto_cproto,qproto_chop,qproto_masked_hop" `
    "--observables" "12" `
    "--obs-per-client" "8" `
    "--observable-overlap" "0.5" `
    "--compressed-observables" "8" `
    "--sketch-dim" "32" `
    "--hop-dim" "16" `
    "--bandwidth" "2.0" `
    "--anchor-size" "32" `
    "--shots" "128,256,512" `
    "--eval-shots" "1024" `
    "--seed" "0" `
    "--hop-weight" "0.12" `
    "--server-lr" "0.05" `
    "--local-epochs" "8" `
    "--lr" "0.2"

& $Python "scripts\collect_results.py" "--root" "runs" "--out" "runs\summary.csv"

