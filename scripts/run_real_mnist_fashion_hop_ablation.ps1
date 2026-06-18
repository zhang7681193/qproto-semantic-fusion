$ErrorActionPreference = "Stop"

$Python = "python"

$Common = @(
    "-m", "qprotohop",
    "--dataset", "npz",
    "--n-classes", "4",
    "--n-train", "6000",
    "--n-test", "1200",
    "--clients", "20",
    "--rounds", "20",
    "--eval-every", "20",
    "--participation", "0.8",
    "--dirichlet-alpha", "0.5",
    "--observables", "256",
    "--obs-per-client", "96",
    "--observable-overlap", "0.8",
    "--sketch-dim", "192",
    "--hop-dim", "96",
    "--bandwidth", "6.0",
    "--anchor-size", "192",
    "--shots", "64,128,256,1024",
    "--eval-shots", "1024",
    "--methods", "qproto_hop"
)

$Datasets = @(
    @{ Name = "mnist4"; Path = "data\mnist.npz" },
    @{ Name = "fashion4"; Path = "data\fashion_mnist.npz" }
)

foreach ($Dataset in $Datasets) {
    foreach ($Seed in 0,1,2,3,4) {
        $Out = "runs/real_$($Dataset.Name)_hop_seed$Seed"
        & $Python @Common "--dataset-path" $Dataset.Path "--seed" "$Seed" "--out" $Out
    }
}

& $Python "scripts/collect_results.py" "--root" "runs" "--out" "runs/summary.csv"

