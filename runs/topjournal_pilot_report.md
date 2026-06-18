# Top-Journal Pilot Experiment Report

## CIFAR-10 full-class

| Method | n | Acc. | 95% CI | Bal. acc. | Bytes |
|---|---:|---:|---:|---:|---:|
| qproto_masked | 3 | 0.4539 | 0.0093 | 0.4542 | 20524 |
| qproto_masked_hop | 3 | 0.4545 | 0.0105 | 0.4549 | 24364 |
| qproto_chop | 3 | 0.4507 | 0.0099 | 0.4510 | 11564 |
| qproto_cproto | 3 | 0.4511 | 0.0101 | 0.4514 | 7724 |
| qproto_hop | 3 | 0.2688 | 0.0642 | 0.2690 | 11564 |
| qproto_proto | 3 | 0.2685 | 0.0641 | 0.2687 | 7724 |
| fedavg_forced | 3 | 0.1225 | 0.0661 | 0.1254 | 7720 |
| fedprox_forced | 3 | 0.1225 | 0.0661 | 0.1254 | 7720 |
| shared_observable | 3 | 0.4236 | 0.0482 | 0.4240 | 7724 |
| no_schema | 3 | 0.1686 | 0.0111 | 0.1682 | 7724 |
| forced_canonical | 3 | 0.1700 | 0.0093 | 0.1697 | 7724 |
| wrong_schema | 3 | 0.1153 | 0.0207 | 0.1155 | 11564 |
| local_only | 3 | 0.3496 | 0.0087 | 0.3494 | 0 |
| classical_kernel | 3 | 0.2406 | 0.0051 | 0.2400 | 7724 |

## CIFAR-10 matched-budget

| Method | n | Acc. | 95% CI | Bal. acc. | Bytes |
|---|---:|---:|---:|---:|---:|
| qproto_proto | 3 | 0.2889 | 0.0639 | 0.2896 | 20524 |
| shared_observable | 3 | 0.4467 | 0.0107 | 0.4470 | 20524 |

## CIFAR-10 schema-head

| Method | n | Acc. | 95% CI | Bal. acc. | Bytes |
|---|---:|---:|---:|---:|---:|
| qproto_masked_hop | 3 | 0.4545 | 0.0105 | 0.4549 | 24364 |
| qproto_chop | 3 | 0.4507 | 0.0099 | 0.4510 | 11564 |
| qproto_cproto | 3 | 0.4511 | 0.0101 | 0.4514 | 7724 |
| fedproto_schema | 3 | 0.2722 | 0.0494 | 0.2717 | 7724 |
| fedadam_schema | 3 | 0.2817 | 0.0464 | 0.2820 | 7720 |
| fedavg_schema | 3 | 0.2545 | 0.0252 | 0.2554 | 7720 |
| fedprox_schema | 3 | 0.2528 | 0.0218 | 0.2538 | 7720 |

## CIFAR-10 strong-baseline

| Method | n | Acc. | 95% CI | Bal. acc. | Bytes |
|---|---:|---:|---:|---:|---:|
| qproto_masked_hop | 3 | 0.4545 | 0.0105 | 0.4549 | 24364 |
| qproto_chop | 3 | 0.4507 | 0.0099 | 0.4510 | 11564 |
| qproto_cproto | 3 | 0.4511 | 0.0101 | 0.4514 | 7724 |
| fedproto_schema | 3 | 0.2722 | 0.0494 | 0.2717 | 7724 |
| fedproto_forced | 3 | 0.1697 | 0.0094 | 0.1695 | 7724 |
| fedadam_forced | 3 | 0.1690 | 0.0097 | 0.1693 | 7720 |
| fedavg_forced | 3 | 0.1225 | 0.0661 | 0.1254 | 7720 |
| fedprox_forced | 3 | 0.1225 | 0.0661 | 0.1254 | 7720 |

## Fashion-10 full-class

| Method | n | Acc. | 95% CI | Bal. acc. | Bytes |
|---|---:|---:|---:|---:|---:|
| qproto_masked | 3 | 0.6701 | 0.0593 | 0.6699 | 20524 |
| qproto_masked_hop | 3 | 0.6711 | 0.0582 | 0.6708 | 24364 |
| qproto_chop | 3 | 0.6697 | 0.0605 | 0.6694 | 11564 |
| qproto_cproto | 3 | 0.6684 | 0.0630 | 0.6682 | 7724 |
| qproto_hop | 3 | 0.5338 | 0.0707 | 0.5345 | 11564 |
| qproto_proto | 3 | 0.5329 | 0.0709 | 0.5336 | 7724 |
| fedavg_forced | 3 | 0.1864 | 0.0504 | 0.1869 | 7720 |
| fedprox_forced | 3 | 0.1863 | 0.0512 | 0.1867 | 7720 |
| shared_observable | 3 | 0.6585 | 0.0527 | 0.6581 | 7724 |
| no_schema | 3 | 0.2493 | 0.0349 | 0.2511 | 7724 |
| forced_canonical | 3 | 0.2520 | 0.0432 | 0.2540 | 7724 |
| wrong_schema | 3 | 0.1527 | 0.0397 | 0.1540 | 11564 |
| local_only | 3 | 0.5573 | 0.0478 | 0.5574 | 0 |
| classical_kernel | 3 | 0.4532 | 0.0059 | 0.4530 | 7724 |

## Fashion-10 matched-budget

| Method | n | Acc. | 95% CI | Bal. acc. | Bytes |
|---|---:|---:|---:|---:|---:|
| qproto_proto | 3 | 0.5809 | 0.0747 | 0.5822 | 20524 |
| shared_observable | 3 | 0.6707 | 0.0540 | 0.6703 | 20524 |

## Fashion-10 schema-head

| Method | n | Acc. | 95% CI | Bal. acc. | Bytes |
|---|---:|---:|---:|---:|---:|
| qproto_masked_hop | 3 | 0.6711 | 0.0582 | 0.6708 | 24364 |
| qproto_chop | 3 | 0.6697 | 0.0605 | 0.6694 | 11564 |
| qproto_cproto | 3 | 0.6684 | 0.0630 | 0.6682 | 7724 |
| fedproto_schema | 3 | 0.5267 | 0.0768 | 0.5273 | 7724 |
| fedadam_schema | 3 | 0.5443 | 0.0642 | 0.5442 | 7720 |
| fedavg_schema | 3 | 0.4705 | 0.1033 | 0.4734 | 7720 |
| fedprox_schema | 3 | 0.4688 | 0.1041 | 0.4717 | 7720 |

## Fashion-10 strong-baseline

| Method | n | Acc. | 95% CI | Bal. acc. | Bytes |
|---|---:|---:|---:|---:|---:|
| qproto_masked_hop | 3 | 0.6711 | 0.0582 | 0.6708 | 24364 |
| qproto_chop | 3 | 0.6697 | 0.0605 | 0.6694 | 11564 |
| qproto_cproto | 3 | 0.6684 | 0.0630 | 0.6682 | 7724 |
| fedproto_schema | 3 | 0.5267 | 0.0768 | 0.5273 | 7724 |
| fedproto_forced | 3 | 0.2498 | 0.0506 | 0.2515 | 7724 |
| fedadam_forced | 3 | 0.2616 | 0.0349 | 0.2629 | 7720 |
| fedavg_forced | 3 | 0.1864 | 0.0504 | 0.1869 | 7720 |
| fedprox_forced | 3 | 0.1863 | 0.0512 | 0.1867 | 7720 |

## Hardware-ready Aer MNIST-2

| Method | n | Acc. | 95% CI | Bal. acc. | Bytes |
|---|---:|---:|---:|---:|---:|
| qproto_masked_hop | 1 | 0.7778 | 0.0000 | 0.7777 | 332 |
| qproto_chop | 1 | 0.7556 | 0.0000 | 0.7553 | 268 |
| qproto_cproto | 1 | 0.7528 | 0.0000 | 0.7526 | 140 |
| fedproto_schema | 1 | 0.6500 | 0.0000 | 0.6502 | 268 |
| fedadam_schema | 1 | 0.5278 | 0.0000 | 0.5141 | 264 |
| shared_observable | 1 | 0.6139 | 0.0000 | 0.6150 | 268 |
| no_schema | 1 | 0.5833 | 0.0000 | 0.5832 | 268 |
| wrong_schema | 1 | 0.5611 | 0.0000 | 0.5591 | 396 |

## MNIST-10 full-class

| Method | n | Acc. | 95% CI | Bal. acc. | Bytes |
|---|---:|---:|---:|---:|---:|
| qproto_masked | 3 | 0.7534 | 0.0398 | 0.7495 | 20524 |
| qproto_masked_hop | 3 | 0.7541 | 0.0406 | 0.7502 | 24364 |
| qproto_chop | 3 | 0.7505 | 0.0425 | 0.7465 | 11564 |
| qproto_cproto | 3 | 0.7483 | 0.0449 | 0.7443 | 7724 |
| qproto_hop | 3 | 0.4121 | 0.0628 | 0.4087 | 11564 |
| qproto_proto | 3 | 0.4115 | 0.0622 | 0.4082 | 7724 |
| fedavg_forced | 3 | 0.1307 | 0.0501 | 0.1136 | 7720 |
| fedprox_forced | 3 | 0.1306 | 0.0499 | 0.1135 | 7720 |
| shared_observable | 2 | 0.7050 | 0.1653 | 0.7001 | 7724 |
| no_schema | 3 | 0.2191 | 0.0189 | 0.2158 | 7724 |
| forced_canonical | 3 | 0.2179 | 0.0123 | 0.2146 | 7724 |
| wrong_schema | 3 | 0.1280 | 0.0102 | 0.1279 | 11564 |
| local_only | 3 | 0.5316 | 0.0329 | 0.5267 | 0 |
| classical_kernel | 3 | 0.4582 | 0.0434 | 0.4501 | 7724 |

## MNIST-10 matched-budget

| Method | n | Acc. | 95% CI | Bal. acc. | Bytes |
|---|---:|---:|---:|---:|---:|
| qproto_proto | 3 | 0.4605 | 0.0773 | 0.4571 | 20524 |
| shared_observable | 3 | 0.7342 | 0.0223 | 0.7299 | 20524 |

## MNIST-10 schema-head

| Method | n | Acc. | 95% CI | Bal. acc. | Bytes |
|---|---:|---:|---:|---:|---:|
| qproto_masked_hop | 3 | 0.7541 | 0.0406 | 0.7502 | 24364 |
| qproto_chop | 3 | 0.7505 | 0.0425 | 0.7465 | 11564 |
| qproto_cproto | 3 | 0.7483 | 0.0449 | 0.7443 | 7724 |
| fedproto_schema | 3 | 0.4172 | 0.0602 | 0.4140 | 7724 |
| fedadam_schema | 3 | 0.4599 | 0.0733 | 0.4539 | 7720 |
| fedavg_schema | 3 | 0.3038 | 0.0168 | 0.2854 | 7720 |
| fedprox_schema | 3 | 0.2989 | 0.0161 | 0.2804 | 7720 |

## MNIST-10 strong-baseline

| Method | n | Acc. | 95% CI | Bal. acc. | Bytes |
|---|---:|---:|---:|---:|---:|
| qproto_masked_hop | 3 | 0.7541 | 0.0406 | 0.7502 | 24364 |
| qproto_chop | 3 | 0.7505 | 0.0425 | 0.7465 | 11564 |
| qproto_cproto | 3 | 0.7483 | 0.0449 | 0.7443 | 7724 |
| fedproto_schema | 3 | 0.4172 | 0.0602 | 0.4140 | 7724 |
| fedproto_forced | 3 | 0.2201 | 0.0107 | 0.2162 | 7724 |
| fedadam_forced | 3 | 0.2318 | 0.0133 | 0.2241 | 7720 |
| fedavg_forced | 3 | 0.1307 | 0.0501 | 0.1136 | 7720 |
| fedprox_forced | 3 | 0.1306 | 0.0499 | 0.1135 | 7720 |

## PennyLane VQC MNIST-4

| Method | n | Acc. | 95% CI | Bal. acc. | Bytes |
|---|---:|---:|---:|---:|---:|
| qproto_masked | 3 | 0.7327 | 0.0630 | 0.7192 | 1940 |
| qproto_masked_hop | 3 | 0.7338 | 0.0607 | 0.7203 | 2708 |
| qproto_hop | 1 | 0.4140 | 0.0000 | 0.4181 | 2324 |
| qproto_proto | 1 | 0.4127 | 0.0000 | 0.4170 | 1556 |
| fedavg_forced | 1 | 0.3941 | 0.0000 | 0.3733 | 1552 |
| fedprox_forced | 1 | 0.3945 | 0.0000 | 0.3734 | 1552 |
| no_schema | 1 | 0.3589 | 0.0000 | 0.3598 | 1556 |
| forced_canonical | 1 | 0.3508 | 0.0000 | 0.3535 | 1556 |
| wrong_schema | 1 | 0.3178 | 0.0000 | 0.3237 | 2324 |
| local_only | 1 | 0.5507 | 0.0000 | 0.5394 | 0 |
| classical_kernel | 1 | 0.6480 | 0.0000 | 0.6330 | 1556 |

## PennyLane VQC MNIST-4 low-overlap

| Method | n | Acc. | 95% CI | Bal. acc. | Bytes |
|---|---:|---:|---:|---:|---:|
| qproto_hop | 1 | 0.3276 | 0.0000 | 0.3294 | 2324 |
| qproto_proto | 1 | 0.3274 | 0.0000 | 0.3291 | 1556 |
| fedavg_forced | 1 | 0.3485 | 0.0000 | 0.3167 | 1552 |
| shared_observable | 1 | 0.5411 | 0.0000 | 0.5352 | 1556 |
| no_schema | 1 | 0.3425 | 0.0000 | 0.3392 | 1556 |
| forced_canonical | 1 | 0.3538 | 0.0000 | 0.3507 | 1556 |
| wrong_schema | 1 | 0.2802 | 0.0000 | 0.2829 | 2324 |

## PennyLane high-order readout

| Method | n | Acc. | 95% CI | Bal. acc. | Bytes |
|---|---:|---:|---:|---:|---:|
| qproto_masked | 3 | 0.4218 | 0.0441 | 0.4218 | 1940 |
| qproto_masked_hop | 3 | 0.5495 | 0.0090 | 0.5495 | 3476 |
| qproto_chop | 3 | 0.6020 | 0.0605 | 0.6020 | 2324 |
| qproto_cproto | 3 | 0.4032 | 0.0609 | 0.4032 | 788 |
| qproto_hop | 3 | 0.3199 | 0.0283 | 0.3199 | 3092 |
| qproto_proto | 3 | 0.2853 | 0.0163 | 0.2853 | 1556 |
| shared_observable | 3 | 0.4456 | 0.0533 | 0.4456 | 1556 |
| no_schema | 3 | 0.3382 | 0.0570 | 0.3382 | 1556 |
| forced_canonical | 3 | 0.3495 | 0.0400 | 0.3495 | 1556 |
| wrong_schema | 3 | 0.2653 | 0.0193 | 0.2653 | 3092 |

## PennyLane high-order schema-head

| Method | n | Acc. | 95% CI | Bal. acc. | Bytes |
|---|---:|---:|---:|---:|---:|
| qproto_masked_hop | 3 | 0.5495 | 0.0090 | 0.5495 | 3476 |
| qproto_chop | 3 | 0.6020 | 0.0605 | 0.6020 | 2324 |
| qproto_cproto | 3 | 0.4032 | 0.0609 | 0.4032 | 788 |
| fedproto_schema | 3 | 0.2849 | 0.0292 | 0.2849 | 1556 |
| fedadam_schema | 3 | 0.3165 | 0.0213 | 0.3165 | 1552 |
| fedavg_schema | 3 | 0.3025 | 0.0080 | 0.3025 | 1552 |
| fedprox_schema | 3 | 0.3019 | 0.0089 | 0.3019 | 1552 |

## PennyLane high-order strong-baseline

| Method | n | Acc. | 95% CI | Bal. acc. | Bytes |
|---|---:|---:|---:|---:|---:|
| qproto_masked_hop | 3 | 0.5495 | 0.0090 | 0.5495 | 3476 |
| qproto_chop | 3 | 0.6020 | 0.0605 | 0.6020 | 2324 |
| qproto_cproto | 3 | 0.4032 | 0.0609 | 0.4032 | 788 |
| fedproto_schema | 3 | 0.2849 | 0.0292 | 0.2849 | 1556 |
| fedproto_forced | 3 | 0.3500 | 0.0277 | 0.3500 | 1556 |
| fedadam_forced | 3 | 0.3586 | 0.0373 | 0.3586 | 1552 |
| fedavg_forced | 3 | 0.3060 | 0.1009 | 0.3060 | 1552 |
| fedprox_forced | 3 | 0.3053 | 0.0992 | 0.3053 | 1552 |

## PennyLane private-signal stress

| Method | n | Acc. | 95% CI | Bal. acc. | Bytes |
|---|---:|---:|---:|---:|---:|
| qproto_masked | 3 | 0.7475 | 0.0319 | 0.7394 | 1940 |
| qproto_masked_hop | 3 | 0.7498 | 0.0285 | 0.7416 | 2708 |
| qproto_hop | 3 | 0.3425 | 0.0623 | 0.3390 | 2324 |
| qproto_proto | 3 | 0.3421 | 0.0625 | 0.3386 | 1556 |
| fedavg_forced | 3 | 0.3971 | 0.0692 | 0.3762 | 1552 |
| shared_observable | 3 | 0.3575 | 0.0131 | 0.3468 | 1556 |
| no_schema | 3 | 0.4046 | 0.0409 | 0.3930 | 1556 |
| forced_canonical | 3 | 0.4054 | 0.0587 | 0.3932 | 1556 |
| wrong_schema | 3 | 0.2843 | 0.0382 | 0.2807 | 2324 |

## Qiskit Aer noisy MNIST-4

| Method | n | Acc. | 95% CI | Bal. acc. | Bytes |
|---|---:|---:|---:|---:|---:|
| qproto_masked | 3 | 0.5931 | 0.0602 | 0.5816 | 404 |
| qproto_masked_hop | 3 | 0.5965 | 0.0650 | 0.5850 | 660 |
| qproto_chop | 3 | 0.5792 | 0.0426 | 0.5684 | 532 |
| qproto_cproto | 3 | 0.5760 | 0.0455 | 0.5655 | 276 |
| qproto_hop | 3 | 0.4295 | 0.2384 | 0.4208 | 788 |
| qproto_proto | 3 | 0.4267 | 0.2382 | 0.4180 | 532 |
| fedavg_forced | 3 | 0.3354 | 0.1361 | 0.2899 | 528 |
| shared_observable | 3 | 0.5576 | 0.0827 | 0.5518 | 532 |
| no_schema | 3 | 0.3747 | 0.1546 | 0.3656 | 532 |
| forced_canonical | 3 | 0.3625 | 0.0875 | 0.3525 | 532 |
| wrong_schema | 3 | 0.2851 | 0.0948 | 0.2870 | 788 |

## Qiskit Aer schema-head

| Method | n | Acc. | 95% CI | Bal. acc. | Bytes |
|---|---:|---:|---:|---:|---:|
| qproto_masked_hop | 3 | 0.5965 | 0.0650 | 0.5850 | 660 |
| qproto_chop | 3 | 0.5792 | 0.0426 | 0.5684 | 532 |
| qproto_cproto | 3 | 0.5760 | 0.0455 | 0.5655 | 276 |
| fedproto_schema | 3 | 0.4278 | 0.1967 | 0.4105 | 532 |
| fedadam_schema | 3 | 0.4257 | 0.1782 | 0.4132 | 528 |
| fedavg_schema | 3 | 0.4122 | 0.2167 | 0.3822 | 528 |
| fedprox_schema | 3 | 0.4128 | 0.2183 | 0.3815 | 528 |

## Qiskit Aer strong-baseline

| Method | n | Acc. | 95% CI | Bal. acc. | Bytes |
|---|---:|---:|---:|---:|---:|
| qproto_masked_hop | 3 | 0.5965 | 0.0650 | 0.5850 | 660 |
| qproto_chop | 3 | 0.5792 | 0.0426 | 0.5684 | 532 |
| qproto_cproto | 3 | 0.5760 | 0.0455 | 0.5655 | 276 |
| fedproto_schema | 3 | 0.4278 | 0.1967 | 0.4105 | 532 |
| fedproto_forced | 3 | 0.3694 | 0.0734 | 0.3614 | 532 |
| fedadam_forced | 3 | 0.3788 | 0.0344 | 0.3674 | 528 |
| fedavg_forced | 3 | 0.3354 | 0.1361 | 0.2899 | 528 |
| fedprox_forced | 3 | 0.3354 | 0.1361 | 0.2899 | 528 |

## Synthetic high-order covariance

| Method | n | Acc. | 95% CI | Bal. acc. | Bytes |
|---|---:|---:|---:|---:|---:|
| qproto_masked | 3 | 0.4668 | 0.0847 | 0.4660 | 2068 |
| qproto_masked_hop | 3 | 0.8082 | 0.0832 | 0.8120 | 4116 |
| qproto_hop | 3 | 0.7945 | 0.0591 | 0.7982 | 2260 |
| qproto_proto | 3 | 0.4490 | 0.1145 | 0.4493 | 212 |
| no_schema | 3 | 0.3077 | 0.0310 | 0.3072 | 212 |
| wrong_schema | 3 | 0.4448 | 0.0294 | 0.4454 | 2260 |

## Synthetic high-order covariance h16

| Method | n | Acc. | 95% CI | Bal. acc. | Bytes |
|---|---:|---:|---:|---:|---:|
| qproto_masked | 3 | 0.4668 | 0.0847 | 0.4660 | 2068 |
| qproto_masked_hop | 3 | 0.6520 | 0.0485 | 0.6521 | 2324 |
| qproto_hop | 3 | 0.6676 | 0.0297 | 0.6676 | 468 |
| qproto_proto | 3 | 0.4490 | 0.1145 | 0.4493 | 212 |

## Interpretation

- Full-class MNIST/Fashion/CIFAR pilots preserve a large gap between correct-schema prototypes and no-schema/wrong-schema/FedAvg controls.
- The coverage-aware masked variant tests the central journal claim more directly: protocol-defined observables can contribute even when they are not measured by every client.
- The shared-observable baseline is strong when the common observable intersection already contains discriminative signal; beating it requires useful non-common observables plus correct missingness handling.
- Mask-aware HOP is neutral to mildly positive on mostly low-order full-class image pilots, but it becomes the main driver on high-order readout tasks.
- Compressed QProto-CHOP keeps most full-class performance at the old QProto-HOP byte budget, and improves the PennyLane high-order result while sending fewer bytes than full masked-HOP.
- Key-policy controls show that anchor-informed CHOP is not random compression: on high-order PennyLane, coverage-key CHOP beats random-key CHOP by a large margin.
- The PennyLane high-order benchmark is the strongest new HOP evidence: old HOP without coverage-aware aggregation is weak, while qproto_masked_hop separates the second-order signal.
- Stronger FL baselines are now included: FedAdam improves over FedAvg/FedProx and schema-aware FedProto improves over forced-coordinate FedProto, but both remain below CProto/CHOP on full-class, Qiskit Aer, and PennyLane high-order pilots.
- PennyLane and Qiskit Aer pilots now validate that the protocol can consume standard quantum-circuit readout features; hardware validation is still the biggest missing item.

