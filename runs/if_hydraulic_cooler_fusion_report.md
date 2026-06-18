# Real Hydraulic Condition Monitoring Multi-Source Fusion Benchmark

The task uses the real UCI Hydraulic Systems condition-monitoring dataset. The target is the cooler state; pressure, flow, temperature, vibration, power, and efficiency sensors are treated as semantic sources.

| Method | n | Acc. | 95% CI | Bytes | Runtime s |
|---|---:|---:|---:|---:|---:|
| Mask-only metadata | 5 | 0.3332 | 0.0003 | 2056 | 0.060 |
| Zero-fill prototype | 5 | 0.9398 | 0.0303 | 2056 | 0.056 |
| Mean-impute prototype | 5 | 0.9388 | 0.0306 | 2056 | 0.072 |
| Value+mask prototype | 5 | 0.6669 | 0.0950 | 4096 | 0.129 |
| Anchor PCA imputation | 5 | 0.9798 | 0.0057 | 2056 | 2.705 |
| Learned ridge imputation | 5 | 0.9777 | 0.0071 | 2056 | 0.533 |
| Anchor autoencoder imputation | 5 | 0.9802 | 0.0070 | 2056 | 5.384 |
| Mask-aware pooled MLP | 5 | 0.9928 | 0.0086 | 4096 | 0.420 |
| HeMIS modality-dropout fusion | 5 | 0.9969 | 0.0044 | 4096 | 5.429 |
| View-wise late fusion | 5 | 0.9754 | 0.0118 | 2056 | 0.015 |
| Shared-view prototype | 5 | 0.7988 | 0.0176 | 256 | 0.004 |
| Shared-view RFF equal bytes | 5 | 0.8329 | 0.0183 | 3472 | 0.159 |
| Zero-fill RFF equal bytes | 5 | 0.9682 | 0.0136 | 3472 | 0.259 |
| Coverage prototype all | 5 | 0.9721 | 0.0176 | 4096 | 0.130 |
| Group-balanced CProto all | 5 | 0.9754 | 0.0118 | 4096 | 0.153 |
| CProto equal bytes | 5 | 0.9731 | 0.0162 | 3472 | 0.107 |
| Group-balanced CProto equal bytes | 5 | 0.9732 | 0.0124 | 3472 | 0.116 |
| Random-key CProto equal bytes | 5 | 0.9692 | 0.0241 | 3472 | 0.068 |
| Random-key HOP equal bytes | 5 | 0.9668 | 0.0252 | 3472 | 0.133 |
| CHOP equal bytes | 5 | 0.9766 | 0.0160 | 3472 | 0.134 |

## Paired Seed Deltas

| Comparison | Mean delta | Wins | Normal approx. p |
|---|---:|---:|---:|
| CProto - zero-fill RFF equal bytes | 0.0049 | 2/5 | 0.1665 |
| CProto - shared-view RFF equal bytes | 0.1401 | 5/5 | 0.0000 |
| CProto - random-key HOP equal bytes | 0.0062 | 4/5 | 0.0488 |
| Random HOP - random CProto equal bytes | -0.0023 | 0/5 | 1.0000 |
| Group CProto - zero-fill RFF equal bytes | 0.0050 | 2/5 | 0.1305 |
| Group CProto - shared-view RFF equal bytes | 0.1402 | 5/5 | 0.0000 |
| Group all - coverage all | 0.0032 | 3/5 | 0.0679 |
| Coverage all - anchor PCA imputation | -0.0077 | 1/5 | 0.9631 |
| Coverage all - learned ridge imputation | -0.0056 | 1/5 | 0.9231 |
| Coverage all - anchor autoencoder imputation | -0.0081 | 0/5 | 0.9826 |
| Coverage all - mask-aware pooled MLP | -0.0207 | 0/5 | 0.9989 |
| Coverage all - HeMIS modality dropout | -0.0248 | 0/5 | 0.9999 |
| Coverage all - view-wise late fusion | -0.0032 | 2/5 | 0.9321 |
| Group all - HeMIS modality dropout | -0.0215 | 0/5 | 1.0000 |
| CHOP - CProto equal bytes | 0.0035 | 4/5 | 0.3345 |
| CHOP - zero-fill RFF equal bytes | 0.0084 | 4/5 | 0.0607 |
| CHOP - shared-view RFF equal bytes | 0.1436 | 5/5 | 0.0000 |
| CHOP - random-key HOP equal bytes | 0.0097 | 4/5 | 0.1990 |
| CHOP - anchor PCA imputation | -0.0032 | 4/5 | 0.7005 |
| CHOP - learned ridge imputation | -0.0011 | 4/5 | 0.5697 |
| CHOP - anchor autoencoder imputation | -0.0037 | 3/5 | 0.7237 |
| CHOP - mask-aware pooled MLP | -0.0163 | 1/5 | 0.9874 |
| CHOP - HeMIS modality dropout | -0.0203 | 0/5 | 0.9994 |
| CHOP - view-wise late fusion | 0.0012 | 4/5 | 0.4320 |

