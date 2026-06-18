# Real UCI Multiple Features Missing-View Fusion Benchmark

The task uses the real UCI Multiple Features handwritten-digit dataset. Six feature families are treated as semantic views, and each federated client observes only a subset of families.

| Method | n | Acc. | 95% CI | Bytes | Runtime s |
|---|---:|---:|---:|---:|---:|
| Mask-only metadata | 10 | 0.1000 | 0.0000 | 26004 | 0.570 |
| Zero-fill prototype | 10 | 0.8180 | 0.0164 | 26004 | 0.576 |
| Mean-impute prototype | 10 | 0.8246 | 0.0158 | 26004 | 0.676 |
| Value+mask prototype | 10 | 0.1955 | 0.0172 | 51964 | 1.158 |
| Anchor PCA imputation | 10 | 0.9013 | 0.0190 | 26004 | 38.492 |
| Learned ridge imputation | 10 | 0.9282 | 0.0108 | 26004 | 2.757 |
| Anchor autoencoder imputation | 10 | 0.9247 | 0.0107 | 26004 | 18.535 |
| Mask-aware pooled MLP | 10 | 0.9402 | 0.0087 | 51964 | 1.449 |
| HeMIS modality-dropout fusion | 10 | 0.9655 | 0.0063 | 51964 | 2.872 |
| View-wise late fusion | 10 | 0.9486 | 0.0080 | 26004 | 0.212 |
| Shared-view prototype | 10 | 0.6915 | 0.0086 | 284 | 0.003 |
| Shared-view RFF equal bytes | 10 | 0.6940 | 0.0077 | 16684 | 0.430 |
| Zero-fill RFF equal bytes | 10 | 0.7663 | 0.0168 | 16684 | 0.691 |
| Coverage prototype all | 10 | 0.9216 | 0.0103 | 51964 | 1.329 |
| Group-balanced CProto all | 10 | 0.9486 | 0.0080 | 51964 | 1.574 |
| CProto equal bytes | 10 | 0.8683 | 0.0212 | 16684 | 0.430 |
| Group-balanced CProto equal bytes | 10 | 0.8760 | 0.0269 | 16684 | 0.476 |
| Random-key CProto equal bytes | 10 | 0.8910 | 0.0123 | 16684 | 0.324 |
| Random-key HOP equal bytes | 10 | 0.8830 | 0.0196 | 16684 | 0.511 |
| CHOP equal bytes | 10 | 0.7221 | 0.0659 | 16684 | 0.500 |
| Adaptive CHOP equal bytes | 10 | 0.8660 | 0.0221 | 16684 | 0.523 |

## Paired Seed Deltas

| Comparison | Mean delta | Wins | Normal approx. p |
|---|---:|---:|---:|
| CProto - zero-fill RFF equal bytes | 0.1020 | 10/10 | 0.0000 |
| CProto - shared-view RFF equal bytes | 0.1743 | 10/10 | 0.0000 |
| CProto - random-key HOP equal bytes | -0.0147 | 5/10 | 0.8629 |
| Random HOP - random CProto equal bytes | -0.0080 | 7/10 | 0.8539 |
| Group CProto - zero-fill RFF equal bytes | 0.1097 | 9/10 | 0.0000 |
| Group CProto - shared-view RFF equal bytes | 0.1820 | 10/10 | 0.0000 |
| Group all - coverage all | 0.0269 | 10/10 | 0.0000 |
| Coverage all - anchor PCA imputation | 0.0204 | 8/10 | 0.0001 |
| Coverage all - learned ridge imputation | -0.0066 | 1/10 | 0.9996 |
| Coverage all - anchor autoencoder imputation | -0.0030 | 3/10 | 0.9799 |
| Coverage all - mask-aware pooled MLP | -0.0185 | 0/10 | 1.0000 |
| Coverage all - HeMIS modality dropout | -0.0439 | 0/10 | 1.0000 |
| Coverage all - view-wise late fusion | -0.0269 | 0/10 | 1.0000 |
| Group all - HeMIS modality dropout | -0.0169 | 0/10 | 1.0000 |
| CHOP - CProto equal bytes | -0.1461 | 0/10 | 1.0000 |
| CHOP - zero-fill RFF equal bytes | -0.0441 | 3/10 | 0.9021 |
| CHOP - shared-view RFF equal bytes | 0.0281 | 5/10 | 0.1999 |
| CHOP - random-key HOP equal bytes | -0.1609 | 1/10 | 1.0000 |
| CHOP - anchor PCA imputation | -0.1791 | 0/10 | 1.0000 |
| CHOP - learned ridge imputation | -0.2061 | 0/10 | 1.0000 |
| CHOP - anchor autoencoder imputation | -0.2025 | 0/10 | 1.0000 |
| CHOP - mask-aware pooled MLP | -0.2180 | 0/10 | 1.0000 |
| CHOP - HeMIS modality dropout | -0.2434 | 0/10 | 1.0000 |
| CHOP - view-wise late fusion | -0.2264 | 0/10 | 1.0000 |
| Adaptive CHOP - CProto equal bytes | -0.0023 | 0/10 | 0.8413 |
| Adaptive CHOP - CHOP equal bytes | 0.1439 | 10/10 | 0.0000 |
| Adaptive CHOP - zero-fill RFF equal bytes | 0.0997 | 10/10 | 0.0000 |
| Adaptive CHOP - shared-view RFF equal bytes | 0.1720 | 10/10 | 0.0000 |
| Adaptive CHOP - random-key HOP equal bytes | -0.0170 | 5/10 | 0.8920 |
| Adaptive CHOP - HeMIS modality dropout | -0.0995 | 0/10 | 1.0000 |

