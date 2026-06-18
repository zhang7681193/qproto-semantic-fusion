$PY = "python"
$METHODS = "qproto_proto,qproto_hop,qproto_full,no_schema,wrong_schema"

foreach ($seed in 0,1,2) {
  & $PY -m qprotohop --out "runs\hop_cov_seed$seed" --methods $METHODS `
    --data-structure covariance --class-sep 0.0 --cov-boost 6.0 `
    --rounds 40 --eval-every 5 --n-train 3000 --n-test 1200 `
    --clients 16 --participation 0.75 --dirichlet-alpha 1.0 `
    --observables 64 --obs-per-client 56 --observable-overlap 0.85 `
    --shots 256,512,1024 --sketch-dim 12 --hop-dim 128 `
    --hop-weight 20.0 --bandwidth 3.0 --anchor-size 96 --probe-size 128 `
    --seed $seed
}

& $PY scripts\collect_results.py --root runs --out runs\summary.csv

