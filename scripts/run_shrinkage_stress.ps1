$PY = "python"
$METHODS = "qproto_hop,qproto_full,no_schema,wrong_schema"

foreach ($scale in "1.0","2.5","4.0") {
  foreach ($seed in 0,1,2) {
    $tag = $scale.Replace(".","p")
    & $PY -m qprotohop --out "runs\shrink_scale${tag}_seed$seed" --methods $METHODS `
      --rounds 40 --eval-every 5 --n-train 3000 --n-test 1200 `
      --clients 24 --participation 0.5 --dirichlet-alpha 0.5 `
      --observables 64 --obs-per-client 24 --observable-overlap 0.35 `
      --shots 8,16,32,512,1024 --eval-shots 1024 --shot-noise-scale $scale `
      --sketch-dim 64 --hop-dim 24 --hop-weight 0.12 `
      --anchor-size 64 --probe-size 96 --c-shot 0.5 --seed $seed
  }
}

& $PY scripts\collect_results.py --root runs --out runs\summary.csv

