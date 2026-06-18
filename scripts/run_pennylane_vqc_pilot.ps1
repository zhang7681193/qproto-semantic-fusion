$ErrorActionPreference = "Stop"

$Python = "python"
$env:PYTHONPATH = ".qdeps;."
$env:MPLCONFIGDIR = ".mplcache"

& $Python "scripts\prepare_pennylane_readout_npz.py" `
    "--source" "data\mnist.npz" `
    "--out" "data\mnist4_pennylane_vqc_readout.npz" `
    "--n-classes" "4" `
    "--n-train" "800" `
    "--n-test" "300" `
    "--n-qubits" "4" `
    "--depth" "2" `
    "--observables" "30" `
    "--seed" "0"

& $Python -m qprotohop `
    "--out" "runs\pennylane_mnist4_vqc_seed0" `
    "--dataset" "npz" `
    "--dataset-path" "data\mnist4_pennylane_vqc_readout.npz" `
    "--readout-backend" "precomputed" `
    "--n-classes" "4" `
    "--n-train" "800" `
    "--n-test" "300" `
    "--clients" "12" `
    "--rounds" "15" `
    "--eval-every" "15" `
    "--participation" "0.75" `
    "--dirichlet-alpha" "0.5" `
    "--methods" "qproto_hop,qproto_proto,no_schema,wrong_schema,forced_canonical,fedavg_forced,fedprox_forced,local_only" `
    "--observables" "30" `
    "--obs-per-client" "14" `
    "--observable-overlap" "0.5" `
    "--sketch-dim" "64" `
    "--hop-dim" "32" `
    "--bandwidth" "3.0" `
    "--anchor-size" "64" `
    "--shots" "64,128,256,1024" `
    "--eval-shots" "1024" `
    "--seed" "0"

& $Python "scripts\collect_results.py" "--root" "runs" "--out" "runs\summary.csv"

