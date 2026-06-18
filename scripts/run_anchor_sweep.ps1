$PY = "python"
$METHODS = "qproto_proto,qproto_hop,qproto_full,no_schema,wrong_schema"

foreach ($anchor in 0,8,32,64,128) {
  foreach ($seed in 0,1,2) {
    & $PY -m qprotohop --out "runs\anchor${anchor}_seed$seed" --methods $METHODS `
      --rounds 35 --eval-every 5 --n-train 3000 --n-test 1200 `
      --clients 20 --participation 0.4 --dirichlet-alpha 0.25 `
      --observables 64 --obs-per-client 24 --observable-overlap 0.35 `
      --shots 32,64,128,256,1024 --sketch-dim 64 --hop-dim 24 `
      --anchor-size $anchor --anchor-normalize --probe-size 96 --seed $seed
  }
}

& $PY scripts\collect_results.py --root runs --out runs\summary.csv
& $PY scripts\report_convergence.py --root runs --prefix anchor --out runs\anchor_convergence.csv

