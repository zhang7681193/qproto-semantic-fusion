$ErrorActionPreference = "Stop"

$Python = "python"
$Dataset = "data\cifar10_feat_resnet18_sz32_pt.npz"

$Base = @(
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
    "--bandwidth", "6.0",
    "--anchor-size", "192",
    "--shots", "64,128,256,1024",
    "--eval-shots", "1024"
)

$Variants = @(
    @{ Name = "proto96"; Method = "qproto_proto"; Sketch = "96"; Hop = "48" },
    @{ Name = "hop48"; Method = "qproto_hop"; Sketch = "48"; Hop = "48" },
    @{ Name = "proto192"; Method = "qproto_proto"; Sketch = "192"; Hop = "96" },
    @{ Name = "hop96"; Method = "qproto_hop"; Sketch = "96"; Hop = "96" },
    @{ Name = "proto256"; Method = "qproto_proto"; Sketch = "256"; Hop = "128" },
    @{ Name = "hop128"; Method = "qproto_hop"; Sketch = "128"; Hop = "128" }
)

foreach ($Variant in $Variants) {
    foreach ($Seed in 0,1,2,3,4) {
        $Out = "runs/real_cifar4_comm_$($Variant.Name)_seed$Seed"
        & $Python @Base "--methods" $Variant.Method "--sketch-dim" $Variant.Sketch "--hop-dim" $Variant.Hop "--seed" "$Seed" "--out" $Out
    }
}

& $Python "scripts/collect_results.py" "--root" "runs" "--out" "runs/summary.csv"

