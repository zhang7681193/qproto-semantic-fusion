$PY = "python"
$ErrorActionPreference = "Stop"
$METHODS = "qproto_full,qproto_proto,no_schema,wrong_schema,fedavg_forced,fedprox_forced"

foreach ($alpha in "0.05","0.10","0.25","0.50","1.00","5.00") {
  foreach ($seed in 0,1,2) {
    $tag = $alpha.Replace(".","p")
    & $PY -m qprotohop --out "runs\noniid_a${tag}_seed$seed" --methods $METHODS `
      --rounds 35 --eval-every 5 --n-train 3000 --n-test 1200 `
      --clients 20 --participation 0.4 --dirichlet-alpha $alpha `
      --observables 64 --obs-per-client 24 --observable-overlap 0.35 `
      --shots 32,64,128,256,1024 --sketch-dim 64 --hop-dim 24 `
      --anchor-size 64 --probe-size 96 --seed $seed
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
  }
}

& $PY scripts\collect_results.py --root runs --out runs\summary.csv
& $PY scripts\report_noniid_sensitivity.py --summary runs\summary.csv > runs\noniid_sensitivity.csv

