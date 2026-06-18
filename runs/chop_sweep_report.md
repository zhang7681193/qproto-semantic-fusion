# CHOP Communication Sweep Report

## CIFAR-10

| K | Method | n | Acc. | 95% CI | Bal. acc. | Bytes |
|---:|---|---:|---:|---:|---:|---:|
| 32 | qproto_chop | 3 | 0.4051 | 0.0061 | 0.4051 | 6444 |
| 32 | qproto_cproto | 3 | 0.4039 | 0.0074 | 0.4039 | 2604 |
| 64 | qproto_chop | 3 | 0.4407 | 0.0053 | 0.4410 | 9004 |
| 64 | qproto_cproto | 3 | 0.4402 | 0.0051 | 0.4405 | 5164 |
| 96 | qproto_chop | 3 | 0.4507 | 0.0099 | 0.4510 | 11564 |
| 96 | qproto_cproto | 3 | 0.4511 | 0.0101 | 0.4514 | 7724 |
| 128 | qproto_chop | 3 | 0.4526 | 0.0108 | 0.4530 | 14124 |
| 128 | qproto_cproto | 3 | 0.4519 | 0.0102 | 0.4523 | 10284 |

## Fashion-10

| K | Method | n | Acc. | 95% CI | Bal. acc. | Bytes |
|---:|---|---:|---:|---:|---:|---:|
| 32 | qproto_chop | 3 | 0.6315 | 0.0673 | 0.6317 | 6444 |
| 32 | qproto_cproto | 3 | 0.6305 | 0.0654 | 0.6306 | 2604 |
| 64 | qproto_chop | 3 | 0.6626 | 0.0575 | 0.6624 | 9004 |
| 64 | qproto_cproto | 3 | 0.6609 | 0.0588 | 0.6608 | 5164 |
| 96 | qproto_chop | 3 | 0.6697 | 0.0605 | 0.6694 | 11564 |
| 96 | qproto_cproto | 3 | 0.6684 | 0.0630 | 0.6682 | 7724 |
| 128 | qproto_chop | 3 | 0.6704 | 0.0581 | 0.6702 | 14124 |
| 128 | qproto_cproto | 3 | 0.6690 | 0.0599 | 0.6688 | 10284 |

## MNIST-10

| K | Method | n | Acc. | 95% CI | Bal. acc. | Bytes |
|---:|---|---:|---:|---:|---:|---:|
| 32 | qproto_chop | 3 | 0.6628 | 0.0532 | 0.6567 | 6444 |
| 32 | qproto_cproto | 3 | 0.6596 | 0.0545 | 0.6534 | 2604 |
| 64 | qproto_chop | 3 | 0.7299 | 0.0444 | 0.7255 | 9004 |
| 64 | qproto_cproto | 3 | 0.7270 | 0.0397 | 0.7227 | 5164 |
| 96 | qproto_chop | 3 | 0.7505 | 0.0425 | 0.7465 | 11564 |
| 96 | qproto_cproto | 3 | 0.7483 | 0.0449 | 0.7443 | 7724 |
| 128 | qproto_chop | 3 | 0.7529 | 0.0415 | 0.7490 | 14124 |
| 128 | qproto_cproto | 3 | 0.7509 | 0.0408 | 0.7470 | 10284 |

## PennyLane high-order

| K | Method | n | Acc. | 95% CI | Bal. acc. | Bytes |
|---:|---|---:|---:|---:|---:|---:|
| 8 | qproto_chop | 3 | 0.6385 | 0.0213 | 0.6385 | 1812 |
| 8 | qproto_cproto | 3 | 0.3890 | 0.0493 | 0.3890 | 276 |
| 16 | qproto_chop | 3 | 0.6135 | 0.0308 | 0.6135 | 2068 |
| 16 | qproto_cproto | 3 | 0.3939 | 0.0479 | 0.3939 | 532 |
| 24 | qproto_chop | 3 | 0.6020 | 0.0605 | 0.6020 | 2324 |
| 24 | qproto_cproto | 3 | 0.4032 | 0.0609 | 0.4032 | 788 |
| 32 | qproto_chop | 3 | 0.6102 | 0.0472 | 0.6102 | 2580 |
| 32 | qproto_cproto | 3 | 0.4119 | 0.0358 | 0.4119 | 1044 |
| 48 | qproto_chop | 3 | 0.5785 | 0.0275 | 0.5785 | 3092 |
| 48 | qproto_cproto | 3 | 0.4186 | 0.0343 | 0.4186 | 1556 |

## Qiskit Aer MNIST-4

| K | Method | n | Acc. | 95% CI | Bal. acc. | Bytes |
|---:|---|---:|---:|---:|---:|---:|
| 4 | qproto_chop | 3 | 0.5563 | 0.0402 | 0.5496 | 404 |
| 4 | qproto_cproto | 3 | 0.5542 | 0.0398 | 0.5465 | 148 |
| 6 | qproto_chop | 3 | 0.5639 | 0.0778 | 0.5556 | 468 |
| 6 | qproto_cproto | 3 | 0.5594 | 0.0696 | 0.5508 | 212 |
| 8 | qproto_chop | 3 | 0.5792 | 0.0426 | 0.5684 | 532 |
| 8 | qproto_cproto | 3 | 0.5760 | 0.0455 | 0.5655 | 276 |
| 10 | qproto_chop | 3 | 0.5944 | 0.0650 | 0.5841 | 596 |
| 10 | qproto_cproto | 3 | 0.5889 | 0.0598 | 0.5788 | 340 |
| 12 | qproto_chop | 3 | 0.5965 | 0.0650 | 0.5850 | 660 |
| 12 | qproto_cproto | 3 | 0.5931 | 0.0602 | 0.5816 | 404 |

## Interpretation

- CHOP should be compared to CProto at the same K because they use the same selected observable keys.
- On high-order readout, a widening gap between CHOP and CProto supports the claim that HOP captures second-order information rather than merely benefiting from key selection.
- On mostly low-order image tasks, a small CHOP-CProto gap is acceptable; the goal there is communication-efficient preservation of coverage-aware QProto performance.


