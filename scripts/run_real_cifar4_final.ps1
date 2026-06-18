$ErrorActionPreference = "Stop"

$Python = "python"
$Dataset = "data\cifar10_feat_resnet18_sz32_pt.npz"

if (-not (Test-Path $Dataset)) {
    throw "Missing CIFAR-10 feature cache: $Dataset"
}

$Common = @(
    "-m", "qprotohop",
    "--dataset", "npz",
    "--dataset-path", $Dataset,
    "--n-classes", "4",
    "--n-train", "6000",
    "--n-test", "1200",
    "--clients", "20",
    "--rounds", "25",
    "--eval-every", "25",
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
    "--methods", "qproto_full,qproto_hop,qproto_proto,no_schema,wrong_schema,forced_canonical,fedavg_forced,fedprox_forced,local_only,classical_kernel,centralized_kernel,centralized_qproto"
)

foreach ($Seed in 0,1,2,3,4) {
    $Out = "runs/real_cifar4_main_seed$Seed"
    & $Python @Common "--seed" "$Seed" "--out" $Out
}

& $Python "scripts/collect_results.py" "--root" "runs" "--out" "runs/summary.csv"
& $Python "scripts/report_statistics.py" "--summary" "runs/summary.csv" "--prefix" "real_cifar4_main" "--reference" "qproto_full" "--out" "runs/real_cifar4_main_statistics.csv"

