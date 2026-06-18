$PY = "python"
$METHODS = "qproto_full,wrong_schema,forced_canonical,no_schema"

foreach ($seed in 0,1,2) {
  & $PY -m qprotohop --out "runs\schema_triptych_seed$seed" --methods $METHODS `
    --rounds 40 --eval-every 5 --n-train 3000 --n-test 1200 `
    --clients 20 --participation 0.4 --dirichlet-alpha 0.25 `
    --observables 64 --obs-per-client 24 --observable-overlap 0.35 `
    --shots 32,64,128,256,1024 --sketch-dim 64 --hop-dim 24 `
    --anchor-size 64 --probe-size 96 --seed $seed
}

