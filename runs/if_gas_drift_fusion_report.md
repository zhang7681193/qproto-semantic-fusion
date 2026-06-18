# Real Gas Sensor Array Drift Missing-View Fusion Benchmark

The task uses the real UCI Gas Sensor Array Drift dataset. Six gas identities are classified from a 16-sensor chemical array; each federated client observes only a subset of sensor sources.

| Method | n | Acc. | 95% CI | Bytes | Runtime s |
|---|---:|---:|---:|---:|---:|
| Mask-only metadata | 5 | 0.1674 | 0.0069 | 3100 | 0.535 |
| Zero-fill prototype | 5 | 0.5955 | 0.0164 | 3100 | 0.542 |
| Mean-impute prototype | 5 | 0.5959 | 0.0164 | 3100 | 0.717 |
| Value+mask prototype | 5 | 0.3198 | 0.0285 | 6172 | 1.029 |
| Anchor PCA imputation | 5 | 0.5689 | 0.0072 | 3100 | 13.177 |
| Learned ridge imputation | 5 | 0.5594 | 0.0067 | 3100 | 1.116 |
| Anchor autoencoder imputation | 5 | 0.5599 | 0.0037 | 3100 | 7.475 |
| Mask-aware pooled MLP | 5 | 0.8981 | 0.0143 | 6172 | 3.675 |
| View-wise late fusion | 5 | 0.5945 | 0.0053 | 3100 | 0.261 |
| Shared-view prototype | 5 | 0.4482 | 0.0038 | 412 | 0.064 |
| Shared-view RFF equal bytes | 5 | 0.4479 | 0.0092 | 6940 | 1.576 |
| Zero-fill RFF equal bytes | 5 | 0.6011 | 0.0221 | 6940 | 1.844 |
| Coverage prototype all | 5 | 0.6034 | 0.0068 | 6172 | 1.187 |
| Group-balanced CProto all | 5 | 0.5945 | 0.0053 | 6172 | 1.576 |
| CProto equal bytes | 5 | 0.6034 | 0.0068 | 6940 | 1.154 |
| Group-balanced CProto equal bytes | 5 | 0.5945 | 0.0053 | 6940 | 1.563 |
| Random-key CProto equal bytes | 5 | 0.5977 | 0.0120 | 6940 | 0.903 |
| Random-key HOP equal bytes | 5 | 0.5980 | 0.0118 | 6940 | 1.712 |
| CHOP equal bytes | 5 | 0.5922 | 0.0116 | 6940 | 1.720 |
| Adaptive CHOP equal bytes | 5 | 0.6037 | 0.0067 | 6940 | 1.249 |

## Paired Seed Deltas

| Comparison | Mean delta | Wins | Normal approx. p |
|---|---:|---:|---:|
| CProto - zero-fill RFF equal bytes | 0.0023 | 4/5 | 0.3587 |
| CProto - shared-view RFF equal bytes | 0.1555 | 5/5 | 0.0000 |
| CProto - random-key HOP equal bytes | 0.0055 | 4/5 | 0.0895 |
| Random HOP - random CProto equal bytes | 0.0003 | 4/5 | 0.0167 |
| Group CProto - zero-fill RFF equal bytes | -0.0067 | 1/5 | 0.8312 |
| Group CProto - shared-view RFF equal bytes | 0.1465 | 5/5 | 0.0000 |
| Group all - coverage all | -0.0090 | 0/5 | 1.0000 |
| Coverage all - anchor PCA imputation | 0.0345 | 5/5 | 0.0000 |
| Coverage all - learned ridge imputation | 0.0440 | 5/5 | 0.0000 |
| Coverage all - anchor autoencoder imputation | 0.0436 | 5/5 | 0.0000 |
| Coverage all - mask-aware pooled MLP | -0.2946 | 0/5 | 1.0000 |
| Coverage all - view-wise late fusion | 0.0090 | 5/5 | 0.0000 |
| CHOP - CProto equal bytes | -0.0112 | 1/5 | 0.9776 |
| CHOP - zero-fill RFF equal bytes | -0.0090 | 2/5 | 0.8733 |
| CHOP - shared-view RFF equal bytes | 0.1443 | 5/5 | 0.0000 |
| CHOP - random-key HOP equal bytes | -0.0058 | 2/5 | 0.7776 |
| CHOP - anchor PCA imputation | 0.0233 | 4/5 | 0.0001 |
| CHOP - learned ridge imputation | 0.0328 | 5/5 | 0.0000 |
| CHOP - anchor autoencoder imputation | 0.0323 | 5/5 | 0.0000 |
| CHOP - mask-aware pooled MLP | -0.3059 | 0/5 | 1.0000 |
| CHOP - view-wise late fusion | -0.0023 | 3/5 | 0.6710 |
| Adaptive CHOP - CProto equal bytes | 0.0002 | 1/5 | 0.1587 |
| Adaptive CHOP - CHOP equal bytes | 0.0115 | 4/5 | 0.0180 |
| Adaptive CHOP - zero-fill RFF equal bytes | 0.0025 | 4/5 | 0.3443 |
| Adaptive CHOP - shared-view RFF equal bytes | 0.1557 | 5/5 | 0.0000 |
| Adaptive CHOP - random-key HOP equal bytes | 0.0057 | 4/5 | 0.0824 |


