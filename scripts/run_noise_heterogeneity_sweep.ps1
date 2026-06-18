$PY = "python"
$ErrorActionPreference = "Stop"
$METHODS = "qproto_full,qproto_hop,qproto_proto,no_schema,wrong_schema,fedavg_forced,fedprox_forced"

$settings = @(
  @{ tag = "low"; readout = "0.01"; rstd = "0.005"; depol = "0.005"; dstd = "0.003" },
  @{ tag = "mid"; readout = "0.03"; rstd = "0.015"; depol = "0.02"; dstd = "0.010" },
  @{ tag = "high"; readout = "0.08"; rstd = "0.030"; depol = "0.06"; dstd = "0.025" }
)

foreach ($s in $settings) {
  foreach ($seed in 0,1,2) {
    & $PY -m qprotohop --out "runs\noise_$($s.tag)_seed$seed" --methods $METHODS `
      --readout-p $s.readout --readout-std $s.rstd --depol-p $s.depol --depol-std $s.dstd `
      --rounds 35 --eval-every 5 --n-train 3000 --n-test 1200 `
      --clients 20 --participation 0.4 --dirichlet-alpha 0.25 `
      --observables 64 --obs-per-client 24 --observable-overlap 0.35 `
      --shots 32,64,128,256,1024 --sketch-dim 64 --hop-dim 24 `
      --anchor-size 64 --probe-size 96 --seed $seed
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
  }
}

& $PY scripts\collect_results.py --root runs --out runs\summary.csv
& $PY scripts\report_statistics.py --summary runs\summary.csv --prefix noise_ --reference qproto_full --out runs\noise_statistics.csv
& $PY scripts\report_noise_sensitivity.py --summary runs\summary.csv > runs\noise_by_level.csv

