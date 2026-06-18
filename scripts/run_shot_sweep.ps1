$PY = "python"
$METHODS = "qproto_hop,qproto_full,wrong_schema,no_schema"

foreach ($shots in "32","64","128","256","1024") {
  foreach ($seed in 0,1,2) {
    & $PY -m qprotohop --out "runs\shot${shots}_seed$seed" --methods $METHODS `
      --rounds 35 --eval-every 5 --n-train 3000 --n-test 1200 `
      --clients 20 --participation 0.4 --dirichlet-alpha 0.25 `
      --observables 64 --obs-per-client 24 --observable-overlap 0.35 `
      --shots $shots --eval-shots 1024 --sketch-dim 64 --hop-dim 24 `
      --anchor-size 64 --probe-size 96 --seed $seed
  }
}

& $PY scripts\collect_results.py --root runs --out runs\summary.csv

