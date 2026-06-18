$ErrorActionPreference = "Stop"

$Python = "python"
$Dataset = "data\cifar10_feat_resnet18_sz32_pt.npz"

$Common = @(
    "-m", "qprotohop",
    "--dataset", "npz",
    "--dataset-path", $Dataset,
    "--n-classes", "4",
    "--n-train", "5000",
    "--n-test", "1000",
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
    "--methods", "qproto_full,qproto_proto,no_schema,wrong_schema,fedavg_forced"
)

foreach ($Shot in 32,64,128,256,1024) {
    foreach ($Seed in 0,1,2,3,4) {
        $Out = "runs/real_cifar4_shot${Shot}_seed$Seed"
        & $Python @Common "--shots" "$Shot" "--eval-shots" "$Shot" "--seed" "$Seed" "--out" $Out
    }
}

& $Python "scripts/collect_results.py" "--root" "runs" "--out" "runs/summary.csv"

