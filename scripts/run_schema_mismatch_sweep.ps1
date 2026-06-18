$PY = "python"
$ErrorActionPreference = "Stop"
$METHODS = "qproto_full,wrong_schema,no_schema,forced_canonical"

foreach ($shift in 1,3,7,15,31) {
  foreach ($seed in 0,1,2) {
    & $PY -m qprotohop --out "runs\mismatch_shift${shift}_seed$seed" --methods $METHODS `
      --wrong-shift $shift --rounds 35 --eval-every 5 `
      --n-train 3000 --n-test 1200 --clients 20 --participation 0.4 `
      --dirichlet-alpha 0.25 --observables 64 --obs-per-client 24 `
      --observable-overlap 0.35 --shots 32,64,128,256,1024 `
      --sketch-dim 64 --hop-dim 24 --anchor-size 64 --probe-size 96 `
      --seed $seed
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
  }
}

& $PY scripts\collect_results.py --root runs --out runs\summary.csv
& $PY scripts\report_statistics.py --summary runs\summary.csv --prefix mismatch_shift --reference qproto_full --out runs\mismatch_statistics.csv
& $PY scripts\report_schema_mismatch.py --summary runs\summary.csv > runs\mismatch_by_shift.csv

