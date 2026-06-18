# IF-Style Heterogeneous Fusion Control Report

## CIFAR-10

| Method | n | Acc. | 95% CI | Bal. acc. | Bytes |
|---|---:|---:|---:|---:|---:|
| Mask-only metadata | 5 | 0.0998 | 0.0010 | 0.1000 | 7724 |
| Schema zero-fill | 5 | 0.4213 | 0.0022 | 0.4215 | 7724 |
| No schema | 5 | 0.1661 | 0.0064 | 0.1659 | 7724 |
| Forced canonical | 5 | 0.1666 | 0.0072 | 0.1665 | 7724 |
| Shared observables | 5 | 0.4251 | 0.0173 | 0.4256 | 7724 |
| RFF prototype | 5 | 0.2659 | 0.0235 | 0.2656 | 7724 |
| CProto | 5 | 0.4502 | 0.0045 | 0.4507 | 7724 |
| CHOP | 5 | 0.4505 | 0.0039 | 0.4510 | 11564 |
| QProto-Masked | 5 | 0.4536 | 0.0034 | 0.4541 | 20524 |
| QProto-Masked-HOP | 5 | 0.4539 | 0.0039 | 0.4545 | 24364 |

## Fashion-10

| Method | n | Acc. | 95% CI | Bal. acc. | Bytes |
|---|---:|---:|---:|---:|---:|
| Mask-only metadata | 5 | 0.1004 | 0.0019 | 0.1000 | 7724 |
| Schema zero-fill | 5 | 0.6471 | 0.0224 | 0.6463 | 7724 |
| No schema | 5 | 0.2395 | 0.0251 | 0.2402 | 7724 |
| Forced canonical | 5 | 0.2421 | 0.0262 | 0.2430 | 7724 |
| Shared observables | 5 | 0.6559 | 0.0192 | 0.6553 | 7724 |
| RFF prototype | 5 | 0.5232 | 0.0446 | 0.5230 | 7724 |
| CProto | 5 | 0.6596 | 0.0269 | 0.6590 | 7724 |
| CHOP | 5 | 0.6605 | 0.0265 | 0.6598 | 11564 |
| QProto-Masked | 5 | 0.6615 | 0.0257 | 0.6608 | 20524 |
| QProto-Masked-HOP | 5 | 0.6623 | 0.0255 | 0.6616 | 24364 |

## MNIST-10

| Method | n | Acc. | 95% CI | Bal. acc. | Bytes |
|---|---:|---:|---:|---:|---:|
| Mask-only metadata | 5 | 0.0993 | 0.0026 | 0.1000 | 7724 |
| Schema zero-fill | 5 | 0.6925 | 0.0204 | 0.6882 | 7724 |
| No schema | 5 | 0.2190 | 0.0098 | 0.2162 | 7724 |
| Forced canonical | 5 | 0.2181 | 0.0116 | 0.2151 | 7724 |
| Shared observables | 5 | 0.6947 | 0.0179 | 0.6906 | 7724 |
| RFF prototype | 5 | 0.4072 | 0.0319 | 0.4040 | 7724 |
| CProto | 5 | 0.7375 | 0.0297 | 0.7336 | 7724 |
| CHOP | 5 | 0.7392 | 0.0298 | 0.7353 | 11564 |
| QProto-Masked | 5 | 0.7434 | 0.0273 | 0.7396 | 20524 |
| QProto-Masked-HOP | 5 | 0.7443 | 0.0269 | 0.7405 | 24364 |


