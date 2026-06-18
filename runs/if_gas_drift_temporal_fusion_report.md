# Real Gas Sensor Array Drift Missing-View Fusion Benchmark

The task uses the real UCI Gas Sensor Array Drift dataset. Six gas identities are classified from a 16-sensor chemical array; each federated client observes only a subset of sensor sources.

| Method | n | Acc. | 95% CI | Bytes | Runtime s |
|---|---:|---:|---:|---:|---:|
| Mask-only metadata | 5 | 0.1657 | 0.0034 | 3100 | 0.927 |
| Zero-fill prototype | 5 | 0.3707 | 0.0175 | 3100 | 0.921 |
| Mean-impute prototype | 5 | 0.3710 | 0.0172 | 3100 | 1.231 |
| Value+mask prototype | 5 | 0.2514 | 0.0154 | 6172 | 1.726 |
| Anchor PCA imputation | 5 | 0.4374 | 0.0106 | 3100 | 20.783 |
| Learned ridge imputation | 5 | 0.4317 | 0.0051 | 3100 | 1.847 |
| Anchor autoencoder imputation | 5 | 0.4282 | 0.0061 | 3100 | 8.077 |
| Mask-aware pooled MLP | 5 | 0.5214 | 0.0253 | 6172 | 2.680 |
| View-wise late fusion | 5 | 0.3977 | 0.0064 | 3100 | 0.417 |
| Shared-view prototype | 5 | 0.2490 | 0.0000 | 412 | 0.110 |
| Shared-view RFF equal bytes | 5 | 0.2470 | 0.0067 | 6940 | 2.430 |
| Zero-fill RFF equal bytes | 5 | 0.3668 | 0.0252 | 6940 | 2.876 |
| Coverage prototype all | 5 | 0.3751 | 0.0045 | 6172 | 2.068 |
| Group-balanced CProto all | 5 | 0.3977 | 0.0064 | 6172 | 3.013 |
| CProto equal bytes | 5 | 0.3751 | 0.0045 | 6940 | 2.150 |
| Group-balanced CProto equal bytes | 5 | 0.3977 | 0.0064 | 6940 | 2.905 |
| Random-key CProto equal bytes | 5 | 0.3764 | 0.0321 | 6940 | 1.526 |
| Random-key HOP equal bytes | 5 | 0.3766 | 0.0321 | 6940 | 3.180 |
| CHOP equal bytes | 5 | 0.3636 | 0.0041 | 6940 | 3.136 |
| Adaptive CHOP equal bytes | 5 | 0.3636 | 0.0041 | 6940 | 3.185 |

## Paired Seed Deltas

| Comparison | Mean delta | Wins | Normal approx. p |
|---|---:|---:|---:|
| CProto - zero-fill RFF equal bytes | 0.0083 | 2/5 | 0.1559 |
| CProto - shared-view RFF equal bytes | 0.1281 | 5/5 | 0.0000 |
| CProto - random-key HOP equal bytes | -0.0015 | 3/5 | 0.5548 |
| Random HOP - random CProto equal bytes | 0.0002 | 4/5 | 0.0229 |
| Group CProto - zero-fill RFF equal bytes | 0.0310 | 5/5 | 0.0001 |
| Group CProto - shared-view RFF equal bytes | 0.1508 | 5/5 | 0.0000 |
| Group all - coverage all | 0.0227 | 5/5 | 0.0000 |
| Coverage all - anchor PCA imputation | -0.0624 | 0/5 | 1.0000 |
| Coverage all - learned ridge imputation | -0.0566 | 0/5 | 1.0000 |
| Coverage all - anchor autoencoder imputation | -0.0532 | 0/5 | 1.0000 |
| Coverage all - mask-aware pooled MLP | -0.1463 | 0/5 | 1.0000 |
| Coverage all - view-wise late fusion | -0.0227 | 0/5 | 1.0000 |
| CHOP - CProto equal bytes | -0.0115 | 0/5 | 1.0000 |
| CHOP - zero-fill RFF equal bytes | -0.0032 | 1/5 | 0.6495 |
| CHOP - shared-view RFF equal bytes | 0.1166 | 5/5 | 0.0000 |
| CHOP - random-key HOP equal bytes | -0.0130 | 2/5 | 0.8892 |
| CHOP - anchor PCA imputation | -0.0739 | 0/5 | 1.0000 |
| CHOP - learned ridge imputation | -0.0681 | 0/5 | 1.0000 |
| CHOP - anchor autoencoder imputation | -0.0647 | 0/5 | 1.0000 |
| CHOP - mask-aware pooled MLP | -0.1578 | 0/5 | 1.0000 |
| CHOP - view-wise late fusion | -0.0342 | 0/5 | 1.0000 |
| Adaptive CHOP - CProto equal bytes | -0.0115 | 0/5 | 1.0000 |
| Adaptive CHOP - CHOP equal bytes | 0.0000 | 0/5 | 1.0000 |
| Adaptive CHOP - zero-fill RFF equal bytes | -0.0032 | 1/5 | 0.6495 |
| Adaptive CHOP - shared-view RFF equal bytes | 0.1166 | 5/5 | 0.0000 |
| Adaptive CHOP - random-key HOP equal bytes | -0.0130 | 2/5 | 0.8892 |


