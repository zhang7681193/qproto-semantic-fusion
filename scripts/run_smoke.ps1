$PY = "python"

& $PY -m qprotohop --out runs\smoke --methods all --rounds 6 --eval-every 3 `
  --n-train 600 --n-test 240 --clients 8 --participation 0.5 `
  --observables 32 --obs-per-client 14 --sketch-dim 32 --hop-dim 12 `
  --anchor-size 24 --probe-size 32 --seed 1

