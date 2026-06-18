$ErrorActionPreference = "Stop"

$Python = "python"

$Common = @(
    "-m", "qprotohop",
    "--dataset", "npz",
    "--n-classes", "10",
    "--n-train", "8000",
    "--n-test", "2000",
    "--clients", "20",
    "--rounds", "15",
    "--eval-every", "15",
    "--participation", "0.8",
    "--dirichlet-alpha", "0.5",
    "--observables", "256",
    "--obs-per-client", "96",
    "--observable-overlap", "0.8",
    "--sketch-dim", "192",
    "--hop-dim", "96",
    "--classical-sketch-dim", "192",
    "--bandwidth", "6.0",
    "--classical-bandwidth", "8.0",
    "--anchor-size", "192",
    "--shots", "64,128,256,1024",
    "--eval-shots", "1024",
    "--methods", "qproto_hop,qproto_proto,shared_observable,no_schema,wrong_schema,forced_canonical,fedavg_forced,fedprox_forced,local_only,classical_kernel"
)

$Datasets = @(
    @{ Name = "mnist10"; Path = "data\mnist.npz"; Train = "8000"; Test = "2000" },
    @{ Name = "fashion10"; Path = "data\fashion_mnist.npz"; Train = "8000"; Test = "2000" },
    @{ Name = "cifar10"; Path = "data\cifar10_feat_resnet18_sz32_pt.npz"; Train = "12000"; Test = "3000" }
)

foreach ($Dataset in $Datasets) {
    foreach ($Seed in 1,2) {
        $Out = "runs/topjournal_$($Dataset.Name)_pilot_seed$Seed"
        & $Python @Common `
            "--dataset-path" $Dataset.Path `
            "--n-train" $Dataset.Train `
            "--n-test" $Dataset.Test `
            "--seed" "$Seed" `
            "--out" $Out
    }
}

& $Python "scripts/collect_results.py" "--root" "runs" "--out" "runs\summary.csv"

