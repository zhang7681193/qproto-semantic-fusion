$ErrorActionPreference = "Stop"

$Python = "python"
$env:PYTHONPATH = ".qdeps;."

& $Python "scripts\prepare_qiskit_aer_readout_npz.py" `
    "--source" "data\mnist.npz" `
    "--out" "data\mnist4_qiskit_aer_readout.npz" `
    "--n-classes" "4" `
    "--n-train" "320" `
    "--n-test" "120" `
    "--n-qubits" "4" `
    "--depth" "1" `
    "--shots" "256" `
    "--depol1" "0.002" `
    "--depol2" "0.01" `
    "--readout-p" "0.02" `
    "--chunk-size" "240" `
    "--seed" "0"

& $Python -m qprotohop `
    "--out" "runs\qiskit_aer_mnist4_seed0" `
    "--dataset" "npz" `
    "--dataset-path" "data\mnist4_qiskit_aer_readout.npz" `
    "--readout-backend" "precomputed" `
    "--n-classes" "4" `
    "--n-train" "320" `
    "--n-test" "120" `
    "--clients" "8" `
    "--rounds" "12" `
    "--eval-every" "12" `
    "--participation" "0.75" `
    "--dirichlet-alpha" "0.5" `
    "--methods" "qproto_hop,qproto_proto,shared_observable,no_schema,wrong_schema,forced_canonical,fedavg_forced" `
    "--observables" "12" `
    "--obs-per-client" "8" `
    "--observable-overlap" "0.5" `
    "--sketch-dim" "32" `
    "--hop-dim" "16" `
    "--bandwidth" "2.0" `
    "--anchor-size" "32" `
    "--shots" "64,128,256,1024" `
    "--eval-shots" "1024" `
    "--seed" "0"

& $Python "scripts\collect_results.py" "--root" "runs" "--out" "runs\summary.csv"

