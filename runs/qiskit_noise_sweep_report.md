# Qiskit Aer Noise Sweep Report

## Clean, depth 1, 1024 shots

| Method | n | Acc. | 95% CI | Bal. acc. | Bytes |
|---|---:|---:|---:|---:|---:|
| qproto_masked_hop | 5 | 0.5795 | 0.0252 | 0.5745 | 660 |
| qproto_chop | 5 | 0.5723 | 0.0324 | 0.5658 | 532 |
| qproto_masked | 5 | 0.5765 | 0.0224 | 0.5720 | 404 |
| qproto_cproto | 5 | 0.5683 | 0.0410 | 0.5620 | 276 |
| fedproto_schema | 5 | 0.4542 | 0.0402 | 0.4544 | 532 |
| fedadam_schema | 5 | 0.4377 | 0.0300 | 0.4412 | 528 |
| shared_observable | 5 | 0.5180 | 0.0387 | 0.5147 | 532 |
| no_schema | 5 | 0.3598 | 0.0282 | 0.3575 | 532 |
| wrong_schema | 5 | 0.3202 | 0.0574 | 0.3217 | 788 |

## Low shot, 128 shots

| Method | n | Acc. | 95% CI | Bal. acc. | Bytes |
|---|---:|---:|---:|---:|---:|
| qproto_masked_hop | 5 | 0.5473 | 0.0426 | 0.5448 | 660 |
| qproto_chop | 5 | 0.5497 | 0.0576 | 0.5489 | 532 |
| qproto_masked | 5 | 0.5445 | 0.0416 | 0.5426 | 404 |
| qproto_cproto | 5 | 0.5455 | 0.0539 | 0.5450 | 276 |
| fedproto_schema | 5 | 0.4098 | 0.0370 | 0.4114 | 532 |
| fedadam_schema | 5 | 0.3975 | 0.0309 | 0.4004 | 528 |
| shared_observable | 5 | 0.4660 | 0.0257 | 0.4630 | 532 |
| no_schema | 5 | 0.3397 | 0.0393 | 0.3350 | 532 |
| wrong_schema | 5 | 0.3085 | 0.0396 | 0.3094 | 788 |

## High readout error

| Method | n | Acc. | 95% CI | Bal. acc. | Bytes |
|---|---:|---:|---:|---:|---:|
| qproto_masked_hop | 5 | 0.5717 | 0.0123 | 0.5675 | 660 |
| qproto_chop | 5 | 0.5833 | 0.0265 | 0.5769 | 532 |
| qproto_masked | 5 | 0.5680 | 0.0169 | 0.5635 | 404 |
| qproto_cproto | 5 | 0.5725 | 0.0206 | 0.5653 | 276 |
| fedproto_schema | 5 | 0.4365 | 0.0363 | 0.4370 | 532 |
| fedadam_schema | 5 | 0.4250 | 0.0335 | 0.4280 | 528 |
| shared_observable | 5 | 0.4960 | 0.0324 | 0.4926 | 532 |
| no_schema | 5 | 0.3555 | 0.0330 | 0.3535 | 532 |
| wrong_schema | 5 | 0.3138 | 0.0523 | 0.3140 | 788 |

## High depolarizing noise

| Method | n | Acc. | 95% CI | Bal. acc. | Bytes |
|---|---:|---:|---:|---:|---:|
| qproto_masked_hop | 5 | 0.5925 | 0.0254 | 0.5866 | 660 |
| qproto_chop | 5 | 0.5930 | 0.0352 | 0.5864 | 532 |
| qproto_masked | 5 | 0.5863 | 0.0244 | 0.5804 | 404 |
| qproto_cproto | 5 | 0.5853 | 0.0332 | 0.5795 | 276 |
| fedproto_schema | 5 | 0.4437 | 0.0435 | 0.4431 | 532 |
| fedadam_schema | 5 | 0.4308 | 0.0290 | 0.4342 | 528 |
| shared_observable | 5 | 0.5060 | 0.0208 | 0.5031 | 532 |
| no_schema | 5 | 0.3515 | 0.0394 | 0.3465 | 532 |
| wrong_schema | 5 | 0.3120 | 0.0486 | 0.3118 | 788 |

## Depth 2

| Method | n | Acc. | 95% CI | Bal. acc. | Bytes |
|---|---:|---:|---:|---:|---:|
| qproto_masked_hop | 5 | 0.6118 | 0.0434 | 0.6090 | 660 |
| qproto_chop | 5 | 0.5887 | 0.0372 | 0.5882 | 532 |
| qproto_masked | 5 | 0.6080 | 0.0443 | 0.6051 | 404 |
| qproto_cproto | 5 | 0.5840 | 0.0453 | 0.5834 | 276 |
| fedproto_schema | 5 | 0.4822 | 0.0517 | 0.4775 | 532 |
| fedadam_schema | 5 | 0.4622 | 0.0541 | 0.4626 | 528 |
| shared_observable | 5 | 0.5380 | 0.0635 | 0.5320 | 532 |
| no_schema | 5 | 0.3700 | 0.0311 | 0.3648 | 532 |
| wrong_schema | 5 | 0.3230 | 0.0448 | 0.3231 | 788 |


