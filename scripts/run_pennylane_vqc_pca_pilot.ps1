$ErrorActionPreference = "Stop"

$Python = "python"
$env:PYTHONPATH = ".qdeps;."
$env:MPLCONFIGDIR = ".mplcache"

& $Python "scripts\prepare_pennylane_readout_npz.py" `
    "--source" "data\mnist.npz" `
    "--out" "data\mnist4_pennylane_pca_readout.npz" `
    "--n-classes" "4" `
    "--n-train" "1200" `
    "--n-test" "500" `
    "--n-qubits" "6" `
    "--depth" "0" `
    "--observables" "60" `
    "--angle-map" "pca" `
    "--seed" "0"

& $Python -m qprotohop `
    "--out" "runs\pennylane_mnist4_pca_seed0" `
    "--dataset" "npz" `
    "--dataset-path" "data\mnist4_pennylane_pca_readout.npz" `
    "--readout-backend" "precomputed" `
    "--n-classes" "4" `
    "--n-train" "1200" `
    "--n-test" "500" `
    "--clients" "16" `
    "--rounds" "20" `
    "--eval-every" "20" `
    "--participation" "0.75" `
    "--dirichlet-alpha" "0.5" `
    "--methods" "qproto_hop,qproto_proto,no_schema,wrong_schema,forced_canonical,fedavg_forced,fedprox_forced,local_only,classical_kernel" `
    "--observables" "60" `
    "--obs-per-client" "24" `
    "--observable-overlap" "0.5" `
    "--sketch-dim" "96" `
    "--hop-dim" "48" `
    "--classical-sketch-dim" "96" `
    "--bandwidth" "3.0" `
    "--classical-bandwidth" "3.0" `
    "--anchor-size" "96" `
    "--shots" "64,128,256,1024" `
    "--eval-shots" "1024" `
    "--seed" "0"

& $Python "scripts\collect_results.py" "--root" "runs" "--out" "runs\summary.csv"

