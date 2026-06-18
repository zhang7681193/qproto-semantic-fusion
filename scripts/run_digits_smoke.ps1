$PY = "python"
$ErrorActionPreference = "Stop"
$METHODS = "classical_kernel,centralized_kernel,no_schema,forced_canonical,wrong_schema,qproto_proto,qproto_hop,qproto_full"

& $PY -m qprotohop --out "runs\digits_smoke" --dataset digits --methods $METHODS `
  --n-train 1200 --n-test 400 --n-classes 10 `
  --rounds 20 --eval-every 5 --clients 12 --participation 0.5 `
  --dirichlet-alpha 0.5 --observables 96 --obs-per-client 40 `
  --observable-overlap 0.5 --shots 128,256,1024 `
  --sketch-dim 64 --hop-dim 32 --classical-sketch-dim 96 `
  --anchor-size 96 --probe-size 96 --seed 0
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

& $PY scripts\collect_results.py --root runs --out runs\summary.csv

