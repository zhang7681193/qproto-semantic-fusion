# IF-Style Paired Significance Report

One-sided paired t-tests are used for the directional claim that the QProto variant improves over the named control. Two-sided p-values are reported as a robustness check. Holm correction is applied across all reported comparisons.

## IF fusion

| Setting | Comparison | n | Delta acc. | 95% CI | Wins | Cohen dz | one-sided Holm p | two-sided Holm p |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| MNIST-10 | Masked-HOP - zero-fill | 5 | 0.0518 | 0.0138 | 5/5 | 4.67 | 0.0059 | 0.0119 |
| MNIST-10 | Masked-HOP - shared-observable | 5 | 0.0496 | 0.0129 | 5/5 | 4.78 | 0.0057 | 0.0113 |
| MNIST-10 | Masked-HOP - CProto | 5 | 0.0068 | 0.0028 | 5/5 | 2.98 | 0.0250 | 0.0500 |
| MNIST-10 | CHOP - zero-fill | 5 | 0.0468 | 0.0167 | 5/5 | 3.47 | 0.0149 | 0.0297 |
| Fashion-10 | Masked-HOP - zero-fill | 5 | 0.0152 | 0.0101 | 5/5 | 1.86 | 0.0851 | 0.1702 |
| Fashion-10 | Masked-HOP - shared-observable | 5 | 0.0064 | 0.0122 | 4/5 | 0.65 | 0.4422 | 0.8844 |
| Fashion-10 | Masked-HOP - CProto | 5 | 0.0027 | 0.0019 | 5/5 | 1.72 | 0.0869 | 0.1739 |
| Fashion-10 | CHOP - zero-fill | 5 | 0.0133 | 0.0108 | 5/5 | 1.53 | 0.1058 | 0.2116 |
| CIFAR-10 | Masked-HOP - zero-fill | 5 | 0.0326 | 0.0050 | 5/5 | 8.16 | 0.0009 | 0.0018 |
| CIFAR-10 | Masked-HOP - shared-observable | 5 | 0.0289 | 0.0195 | 5/5 | 1.83 | 0.0851 | 0.1702 |
| CIFAR-10 | Masked-HOP - CProto | 5 | 0.0037 | 0.0021 | 5/5 | 2.18 | 0.0574 | 0.1148 |
| CIFAR-10 | CHOP - zero-fill | 5 | 0.0292 | 0.0046 | 5/5 | 7.85 | 0.0010 | 0.0020 |

## IF scientific

| Setting | Comparison | n | Delta acc. | 95% CI | Wins | Cohen dz | one-sided Holm p | two-sided Holm p |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Covariance sensing | CHOP - zero-fill | 5 | 0.1051 | 0.0368 | 5/5 | 3.54 | 0.0144 | 0.0289 |
| Covariance sensing | CHOP - shared-observable | 5 | 0.1057 | 0.0856 | 5/5 | 1.53 | 0.1058 | 0.2116 |
| Covariance sensing | CHOP - CProto | 5 | 0.3743 | 0.0449 | 5/5 | 10.35 | 0.0004 | 0.0007 |
| Covariance sensing | Masked-HOP - Masked | 5 | 0.3192 | 0.0472 | 5/5 | 8.40 | 0.0008 | 0.0016 |

## Real missing-view

| Setting | Comparison | n | Delta acc. | 95% CI | Wins | Cohen dz | one-sided Holm p | two-sided Holm p |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| UCI HAR | CProto eq. - zero-fill RFF eq. | 5 | 0.4086 | 0.0380 | 5/5 | 13.34 | 0.0002 | 0.0003 |
| UCI HAR | CProto eq. - shared-view RFF eq. | 5 | 0.3620 | 0.0181 | 5/5 | 24.84 | <0.0001 | <0.0001 |
| UCI HAR | Coverage all - anchor AE | 5 | 0.0284 | 0.0066 | 5/5 | 5.38 | 0.0040 | 0.0079 |
| MFeat | Group-CProto eq. - zero-fill RFF eq. | 10 | 0.1097 | 0.0415 | 9/10 | 1.89 | 0.0031 | 0.0062 |
| MFeat | Group-CProto eq. - shared-view RFF eq. | 10 | 0.1820 | 0.0312 | 10/10 | 4.17 | <0.0001 | <0.0001 |
| MFeat | Group-CProto all - mask-aware MLP | 10 | 0.0084 | 0.0038 | 10/10 | 1.58 | 0.0083 | 0.0166 |

## Real high-order

| Setting | Comparison | n | Delta acc. | 95% CI | Wins | Cohen dz | one-sided Holm p | two-sided Holm p |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| MHEALTH | CHOP eq. - CProto eq. | 10 | 0.0052 | 0.0426 | 6/10 | 0.09 | 1.0000 | 1.0000 |
| MHEALTH | CHOP eq. - zero-fill RFF eq. | 10 | 0.0907 | 0.0618 | 9/10 | 1.05 | 0.0579 | 0.1158 |
| MHEALTH | CHOP eq. - shared-view RFF eq. | 10 | 0.1446 | 0.0817 | 9/10 | 1.27 | 0.0255 | 0.0511 |
| MHEALTH | CHOP eq. - mask-aware MLP | 10 | 0.0047 | 0.0487 | 7/10 | 0.07 | 1.0000 | 1.0000 |
| MHEALTH | Adaptive CHOP - CProto eq. | 10 | 0.0178 | 0.0138 | 6/10 | 0.92 | 0.0869 | 0.1739 |
| MHEALTH | Random HOP - random CProto eq. | 10 | 0.0000 | 0.0002 | 6/10 | 0.09 | 1.0000 | 1.0000 |

## Adaptive gate

| Setting | Comparison | n | Delta acc. | 95% CI | Wins | Cohen dz | one-sided Holm p | two-sided Holm p |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| UCI HAR | Adaptive CHOP - CHOP eq. | 5 | 0.1195 | 0.0308 | 5/5 | 4.82 | 0.0057 | 0.0113 |
| MFeat | Adaptive CHOP - CHOP eq. | 10 | 0.1439 | 0.0634 | 10/10 | 1.62 | 0.0071 | 0.0142 |
| PAMAP2 | Adaptive CHOP - CHOP eq. | 5 | 0.2300 | 0.1041 | 5/5 | 2.74 | 0.0269 | 0.0537 |
| PAMAP2 | Adaptive CHOP - zero-fill RFF eq. | 5 | 0.1163 | 0.0494 | 5/5 | 2.92 | 0.0255 | 0.0511 |
| PAMAP2 | Adaptive CHOP - shared-view RFF eq. | 5 | 0.4505 | 0.0337 | 5/5 | 16.60 | <0.0001 | 0.0001 |

## FL baselines

| Setting | Comparison | n | Delta acc. | 95% CI | Wins | Cohen dz | one-sided Holm p | two-sided Holm p |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| MNIST-10 | Masked-HOP - schema-FedProto | 5 | 0.3322 | 0.0357 | 5/5 | 11.56 | 0.0003 | 0.0005 |
| MNIST-10 | Masked-HOP - schema-FedAdam | 5 | 0.2884 | 0.0386 | 5/5 | 9.27 | 0.0006 | 0.0011 |
| MNIST-10 | Masked-HOP - no-schema | 5 | 0.5253 | 0.0329 | 5/5 | 19.85 | <0.0001 | <0.0001 |
| Fashion-10 | Masked-HOP - schema-FedProto | 5 | 0.1402 | 0.0282 | 5/5 | 6.17 | 0.0025 | 0.0050 |
| Fashion-10 | Masked-HOP - schema-FedAdam | 5 | 0.1181 | 0.0291 | 5/5 | 5.04 | 0.0049 | 0.0099 |
| Fashion-10 | Masked-HOP - no-schema | 5 | 0.4228 | 0.0222 | 5/5 | 23.67 | <0.0001 | <0.0001 |
| CIFAR-10 | Masked-HOP - schema-FedProto | 5 | 0.1855 | 0.0220 | 5/5 | 10.49 | 0.0004 | 0.0007 |
| CIFAR-10 | Masked-HOP - schema-FedAdam | 5 | 0.1725 | 0.0199 | 5/5 | 10.76 | 0.0003 | 0.0007 |
| CIFAR-10 | Masked-HOP - no-schema | 5 | 0.2879 | 0.0090 | 5/5 | 39.71 | <0.0001 | <0.0001 |

## High-order

| Setting | Comparison | n | Delta acc. | 95% CI | Wins | Cohen dz | one-sided Holm p | two-sided Holm p |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| PennyLane high-order | CHOP - CProto | 3 | 0.1989 | 0.0461 | 3/3 | 10.72 | 0.0255 | 0.0511 |
| PennyLane high-order | CHOP - schema-FedProto | 3 | 0.3172 | 0.0312 | 3/3 | 25.23 | 0.0063 | 0.0126 |

## Quantum backend

| Setting | Comparison | n | Delta acc. | 95% CI | Wins | Cohen dz | one-sided Holm p | two-sided Holm p |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Qiskit Aer | Masked-HOP - schema-FedProto | 3 | 0.1687 | 0.1441 | 3/3 | 2.91 | 0.1058 | 0.2116 |
| Qiskit Aer | Masked-HOP - FedDyn | 3 | 0.1781 | 0.1272 | 3/3 | 3.48 | 0.1058 | 0.2116 |


