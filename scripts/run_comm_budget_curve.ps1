$PY = "python"
$ErrorActionPreference = "Stop"

$settings = @(
  @{ tag = "012"; proto = "12";  hsketch = "8";  hhop = "4" },
  @{ tag = "024"; proto = "24";  hsketch = "12"; hhop = "12" },
  @{ tag = "048"; proto = "48";  hsketch = "16"; hhop = "32" },
  @{ tag = "096"; proto = "96";  hsketch = "24"; hhop = "72" },
  @{ tag = "144"; proto = "144"; hsketch = "32"; hhop = "112" }
)

foreach ($s in $settings) {
  foreach ($seed in 0,1,2) {
    & $PY -m qprotohop --out "runs\comm_proto_$($s.tag)_seed$seed" `
      --methods qproto_proto `
      --data-structure covariance --class-sep 0.0 --cov-boost 6.0 `
      --rounds 35 --eval-every 5 --n-train 2600 --n-test 1000 `
      --clients 16 --participation 0.75 --dirichlet-alpha 1.0 `
      --observables 64 --obs-per-client 56 --observable-overlap 0.85 `
      --shots 256,512,1024 --sketch-dim $s.proto --hop-dim 1 `
      --hop-weight 20.0 --bandwidth 3.0 --anchor-size 96 --probe-size 128 `
      --seed $seed
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

    & $PY -m qprotohop --out "runs\comm_hop_$($s.tag)_seed$seed" `
      --methods qproto_hop `
      --data-structure covariance --class-sep 0.0 --cov-boost 6.0 `
      --rounds 35 --eval-every 5 --n-train 2600 --n-test 1000 `
      --clients 16 --participation 0.75 --dirichlet-alpha 1.0 `
      --observables 64 --obs-per-client 56 --observable-overlap 0.85 `
      --shots 256,512,1024 --sketch-dim $s.hsketch --hop-dim $s.hhop `
      --hop-weight 20.0 --bandwidth 3.0 --anchor-size 96 --probe-size 128 `
      --seed $seed
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
  }
}

& $PY scripts\collect_results.py --root runs --out runs\summary.csv
& $PY scripts\report_comm_budget.py --summary runs\summary.csv > runs\comm_budget_curve.csv

