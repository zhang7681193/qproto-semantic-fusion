$PY = "python"
$ErrorActionPreference = "Stop"

# Low-order sketch dimension on the default mean-structured benchmark.
foreach ($dim in 16,32,64,128) {
  foreach ($seed in 0,1,2) {
    & $PY -m qprotohop --out "runs\sketchdim${dim}_seed$seed" `
      --methods qproto_proto,qproto_full,no_schema,wrong_schema `
      --rounds 30 --eval-every 5 --n-train 2600 --n-test 1000 `
      --clients 20 --participation 0.4 --dirichlet-alpha 0.25 `
      --observables 64 --obs-per-client 24 --observable-overlap 0.35 `
      --shots 32,64,128,256,1024 --sketch-dim $dim --hop-dim 24 `
      --anchor-size 64 --probe-size 96 --seed $seed
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
  }
}

# HOP dimension on the covariance/high-order benchmark.
foreach ($hop in 8,16,32,64,128) {
  foreach ($seed in 0,1,2) {
    & $PY -m qprotohop --out "runs\hopdim${hop}_seed$seed" `
      --methods qproto_proto,qproto_hop,qproto_full `
      --data-structure covariance --class-sep 0.0 --cov-boost 6.0 `
      --rounds 35 --eval-every 5 --n-train 2600 --n-test 1000 `
      --clients 16 --participation 0.75 --dirichlet-alpha 1.0 `
      --observables 64 --obs-per-client 56 --observable-overlap 0.85 `
      --shots 256,512,1024 --sketch-dim 12 --hop-dim $hop `
      --hop-weight 20.0 --bandwidth 3.0 --anchor-size 96 --probe-size 128 `
      --seed $seed
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
  }
}

& $PY scripts\collect_results.py --root runs --out runs\summary.csv
& $PY scripts\report_dimension_sensitivity.py --summary runs\summary.csv > runs\dimension_sensitivity.csv

