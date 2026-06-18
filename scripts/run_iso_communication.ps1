$PY = "python"

$COMMON = @(
  "--data-structure", "covariance",
  "--class-sep", "0.0",
  "--cov-boost", "6.0",
  "--rounds", "40",
  "--eval-every", "5",
  "--n-train", "3000",
  "--n-test", "1200",
  "--clients", "16",
  "--participation", "0.75",
  "--dirichlet-alpha", "1.0",
  "--observables", "64",
  "--obs-per-client", "56",
  "--observable-overlap", "0.85",
  "--shots", "256,512,1024",
  "--bandwidth", "3.0",
  "--anchor-size", "96",
  "--probe-size", "128"
)

foreach ($seed in 0,1,2) {
  # Low communication budget: both are 212 bytes/client/round for 4 classes.
  & $PY -m qprotohop --out "runs\iso_proto_low_seed$seed" --methods qproto_proto `
    @COMMON --sketch-dim 12 --hop-dim 128 --hop-weight 20.0 --seed $seed

  & $PY -m qprotohop --out "runs\iso_hop_low_seed$seed" --methods qproto_hop `
    @COMMON --sketch-dim 8 --hop-dim 4 --hop-weight 20.0 --seed $seed

  # High communication budget: both are 2260 bytes/client/round for 4 classes.
  & $PY -m qprotohop --out "runs\iso_proto_high_seed$seed" --methods qproto_proto `
    @COMMON --sketch-dim 140 --hop-dim 128 --hop-weight 20.0 --seed $seed

  & $PY -m qprotohop --out "runs\iso_hop_high_seed$seed" --methods qproto_hop `
    @COMMON --sketch-dim 12 --hop-dim 128 --hop-weight 20.0 --seed $seed
}

& $PY scripts\collect_results.py --root runs --out runs\summary.csv

