$ErrorActionPreference = "Stop"

$Python = "python"
$env:PYTHONPATH = ".qdeps;."
$env:MPLCONFIGDIR = ".mplcache"

& $Python "scripts\run_quantum_param_vqc_baseline.py" `
    "--source" "data\mnist.npz" `
    "--out" "runs\quantum_param_vqc_baseline" `
    "--seeds" "0,1,2,3,4" `
    "--n-classes" "4" `
    "--n-train" "300" `
    "--n-test" "200" `
    "--n-qubits" "4" `
    "--layers" "1" `
    "--clients" "12" `
    "--dirichlet-alpha" "0.5" `
    "--participation" "0.75" `
    "--rounds" "6" `
    "--local-steps" "4" `
    "--batch-size" "16" `
    "--lr" "0.10" `
    "--fedprox-mu" "0.02" `
    "--methods" "vqc_init,vqc_fedavg,vqc_fedprox,vqc_centralized" `
    "--reuse-existing"

