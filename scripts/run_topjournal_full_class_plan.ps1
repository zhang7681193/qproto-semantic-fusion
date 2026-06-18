$ErrorActionPreference = "Stop"

$Python = "python"

$Common = @(
    "-m", "qprotohop",
    "--dataset", "npz",
    "--n-classes", "10",
    "--n-train", "12000",
    "--n-test", "3000",
    "--clients", "20",
    "--rounds", "30",
    "--eval-every", "30",
    "--participation", "0.8",
    "--observables", "384",
    "--obs-per-client", "128",
    "--observable-overlap", "0.6",
    "--sketch-dim", "256",
    "--hop-dim", "128",
    "--classical-sketch-dim", "256",
    "--bandwidth", "6.0",
    "--classical-bandwidth", "8.0",
    "--anchor-size", "256",
    "--shots", "64,128,256,1024",
    "--eval-shots", "1024",
    "--methods", "qproto_hop,qproto_proto,no_schema,wrong_schema,forced_canonical,fedavg_forced,fedprox_forced,local_only,classical_kernel"
)

$Datasets = @(
    @{ Name = "mnist10"; Path = "data\mnist.npz" },
    @{ Name = "fashion10"; Path = "data\fashion_mnist.npz" },
    @{ Name = "cifar10"; Path = "data\cifar10_feat_resnet18_sz32_pt.npz" }
)

$Alphas = @(0.1, 0.3, 0.5, 1.0)

foreach ($Dataset in $Datasets) {
    foreach ($Alpha in $Alphas) {
        foreach ($Seed in 0,1,2,3,4) {
            $Out = "runs/topjournal_$($Dataset.Name)_alpha$Alpha`_seed$Seed"
            & $Python @Common "--dataset-path" $Dataset.Path "--dirichlet-alpha" "$Alpha" "--seed" "$Seed" "--out" $Out
        }
    }
}

& $Python "scripts/collect_results.py" "--root" "runs" "--out" "runs/summary.csv"

