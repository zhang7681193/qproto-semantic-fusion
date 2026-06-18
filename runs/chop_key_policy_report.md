# CHOP Key Policy Control Report

## CIFAR-10

| Policy | K | Method | n | Acc. | 95% CI | Bal. acc. | Bytes |
|---|---:|---|---:|---:|---:|---:|---:|
| variance | 96 | qproto_chop | 3 | 0.4507 | 0.0099 | 0.4510 | 11564 |
| variance | 96 | qproto_cproto | 3 | 0.4511 | 0.0101 | 0.4514 | 7724 |
| coverage | 96 | qproto_chop | 3 | 0.4523 | 0.0120 | 0.4527 | 11564 |
| coverage | 96 | qproto_cproto | 3 | 0.4515 | 0.0121 | 0.4518 | 7724 |
| random | 96 | qproto_chop | 3 | 0.3910 | 0.0337 | 0.3916 | 11564 |
| random | 96 | qproto_cproto | 3 | 0.3904 | 0.0337 | 0.3910 | 7724 |

## MNIST-10

| Policy | K | Method | n | Acc. | 95% CI | Bal. acc. | Bytes |
|---|---:|---|---:|---:|---:|---:|---:|
| variance | 96 | qproto_chop | 3 | 0.7505 | 0.0425 | 0.7465 | 11564 |
| variance | 96 | qproto_cproto | 3 | 0.7483 | 0.0449 | 0.7443 | 7724 |
| coverage | 96 | qproto_chop | 3 | 0.7494 | 0.0394 | 0.7454 | 11564 |
| coverage | 96 | qproto_cproto | 3 | 0.7481 | 0.0425 | 0.7441 | 7724 |
| random | 96 | qproto_chop | 3 | 0.6619 | 0.0492 | 0.6564 | 11564 |
| random | 96 | qproto_cproto | 3 | 0.6604 | 0.0463 | 0.6549 | 7724 |

## PennyLane high-order

| Policy | K | Method | n | Acc. | 95% CI | Bal. acc. | Bytes |
|---|---:|---|---:|---:|---:|---:|---:|
| variance | 8 | qproto_chop | 5 | 0.6244 | 0.0466 | 0.6244 | 1812 |
| variance | 8 | qproto_cproto | 5 | 0.3919 | 0.0189 | 0.3919 | 276 |
| coverage | 8 | qproto_chop | 5 | 0.6588 | 0.0590 | 0.6588 | 1812 |
| coverage | 8 | qproto_cproto | 5 | 0.3943 | 0.0321 | 0.3943 | 276 |
| random | 8 | qproto_chop | 5 | 0.4306 | 0.0355 | 0.4306 | 1812 |
| random | 8 | qproto_cproto | 5 | 0.2914 | 0.0424 | 0.2914 | 276 |

## Qiskit Aer MNIST-4

| Policy | K | Method | n | Acc. | 95% CI | Bal. acc. | Bytes |
|---|---:|---|---:|---:|---:|---:|---:|
| variance | 10 | qproto_chop | 3 | 0.5944 | 0.0650 | 0.5841 | 596 |
| variance | 10 | qproto_cproto | 3 | 0.5889 | 0.0598 | 0.5788 | 340 |
| coverage | 10 | qproto_chop | 3 | 0.5903 | 0.0823 | 0.5790 | 596 |
| coverage | 10 | qproto_cproto | 3 | 0.5847 | 0.0765 | 0.5736 | 340 |
| random | 10 | qproto_chop | 3 | 0.5823 | 0.1042 | 0.5719 | 596 |
| random | 10 | qproto_cproto | 3 | 0.5767 | 0.0879 | 0.5669 | 340 |

## Interpretation

- Variance policy is the proposed public-anchor key selection rule.
- Random policy controls whether compression merely needs any K observables.
- Coverage policy controls whether selecting frequently observed keys is enough without value variation.
- CHOP should be compared against CProto within the same policy and K.


