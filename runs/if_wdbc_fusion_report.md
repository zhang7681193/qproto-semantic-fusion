# Real WDBC Biomedical Missing-View Fusion Benchmark

The task uses the real Wisconsin Diagnostic Breast Cancer dataset. Ten measurement families are treated as semantic biomedical views, and each federated client observes only a subset of families.

| Method | n | Acc. | 95% CI | Bytes | Runtime s |
|---|---:|---:|---:|---:|---:|
| Mask-only metadata | 10 | 0.5088 | 0.0147 | 252 | 0.003 |
| Zero-fill prototype | 10 | 0.9207 | 0.0062 | 252 | 0.003 |
| Mean-impute prototype | 10 | 0.9223 | 0.0065 | 252 | 0.004 |
| Value+mask prototype | 10 | 0.7799 | 0.0449 | 492 | 0.003 |
| Anchor PCA imputation | 10 | 0.8825 | 0.0141 | 252 | 0.565 |
| Learned ridge imputation | 10 | 0.9238 | 0.0083 | 252 | 0.029 |
| Anchor autoencoder imputation | 10 | 0.9198 | 0.0092 | 252 | 6.481 |
| Mask-aware pooled MLP | 10 | 0.9204 | 0.0078 | 492 | 0.706 |
| View-wise late fusion | 10 | 0.9208 | 0.0076 | 252 | 0.015 |
| Shared-view prototype | 10 | 0.8965 | 0.0092 | 36 | 0.004 |
| Shared-view RFF equal bytes | 10 | 0.8959 | 0.0063 | 396 | 0.010 |
| Zero-fill RFF equal bytes | 10 | 0.9109 | 0.0076 | 396 | 0.014 |
| Coverage prototype all | 10 | 0.9218 | 0.0062 | 492 | 0.017 |
| Group-balanced CProto all | 10 | 0.9208 | 0.0076 | 492 | 0.050 |
| CProto equal bytes | 10 | 0.9218 | 0.0062 | 396 | 0.011 |
| Group-balanced CProto equal bytes | 10 | 0.9208 | 0.0076 | 396 | 0.043 |
| Random-key HOP equal bytes | 10 | 0.9046 | 0.0113 | 396 | 0.017 |
| CHOP equal bytes | 10 | 0.9228 | 0.0061 | 396 | 0.019 |

## Paired Seed Deltas

| Comparison | Mean delta | Wins | Normal approx. p |
|---|---:|---:|---:|
| CProto - zero-fill RFF equal bytes | 0.0109 | 9/10 | 0.0003 |
| CProto - shared-view RFF equal bytes | 0.0259 | 9/10 | 0.0000 |
| CProto - random-key HOP equal bytes | 0.0172 | 9/10 | 0.0013 |
| Group CProto - zero-fill RFF equal bytes | 0.0099 | 8/10 | 0.0025 |
| Group CProto - shared-view RFF equal bytes | 0.0249 | 9/10 | 0.0000 |
| Group all - coverage all | -0.0009 | 2/10 | 0.7845 |
| Coverage all - anchor PCA imputation | 0.0393 | 10/10 | 0.0000 |
| Coverage all - learned ridge imputation | -0.0020 | 3/10 | 0.9263 |
| Coverage all - anchor autoencoder imputation | 0.0020 | 5/10 | 0.1789 |
| Coverage all - mask-aware pooled MLP | 0.0014 | 5/10 | 0.3015 |
| Coverage all - view-wise late fusion | 0.0009 | 8/10 | 0.2155 |
| CHOP - CProto equal bytes | 0.0011 | 6/10 | 0.2407 |
| CHOP - zero-fill RFF equal bytes | 0.0119 | 9/10 | 0.0011 |
| CHOP - shared-view RFF equal bytes | 0.0269 | 10/10 | 0.0000 |
| CHOP - random-key HOP equal bytes | 0.0183 | 9/10 | 0.0006 |
| CHOP - anchor PCA imputation | 0.0404 | 10/10 | 0.0000 |
| CHOP - learned ridge imputation | -0.0009 | 4/10 | 0.6647 |
| CHOP - anchor autoencoder imputation | 0.0030 | 6/10 | 0.1243 |
| CHOP - mask-aware pooled MLP | 0.0025 | 7/10 | 0.1802 |
| CHOP - view-wise late fusion | 0.0020 | 6/10 | 0.1482 |

