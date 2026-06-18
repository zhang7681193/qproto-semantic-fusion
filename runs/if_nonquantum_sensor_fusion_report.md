# Real UCI HAR Missing-View Sensor Fusion Benchmark

The task uses the real UCI HAR smartphone-sensor feature dataset. Feature groups are treated as semantic sensor views, and each federated client observes only a subset of groups.

| Method | n | Acc. | 95% CI | Bytes | Runtime s |
|---|---:|---:|---:|---:|---:|
| Mask-only metadata | 5 | 0.1625 | 0.0054 | 13492 | 1.063 |
| Zero-fill prototype | 5 | 0.2748 | 0.0355 | 13492 | 1.057 |
| Mean-impute prototype | 5 | 0.5690 | 0.0318 | 13492 | 1.497 |
| Value+mask prototype | 5 | 0.2078 | 0.0355 | 26956 | 2.050 |
| Anchor PCA imputation | 5 | 0.7795 | 0.0117 | 13492 | 26.368 |
| Learned ridge imputation | 5 | 0.7696 | 0.0158 | 13492 | 3.486 |
| Anchor autoencoder imputation | 5 | 0.7528 | 0.0048 | 13492 | 14.623 |
| Mask-aware pooled MLP | 5 | 0.7572 | 0.0220 | 26956 | 4.778 |
| HeMIS modality-dropout fusion | 5 | 0.8210 | 0.0226 | 26956 | 32.261 |
| View-wise late fusion | 5 | 0.7170 | 0.0166 | 13492 | 0.294 |
| Shared-view prototype | 5 | 0.3905 | 0.0209 | 52 | 0.013 |
| Shared-view RFF equal bytes | 5 | 0.3911 | 0.0211 | 7708 | 0.647 |
| Zero-fill RFF equal bytes | 5 | 0.3445 | 0.0381 | 7708 | 1.204 |
| Coverage prototype all | 5 | 0.7812 | 0.0027 | 26956 | 2.136 |
| Group-balanced CProto all | 5 | 0.7170 | 0.0166 | 26956 | 2.407 |
| CProto equal bytes | 5 | 0.7530 | 0.0089 | 7708 | 0.545 |
| Group-balanced CProto equal bytes | 5 | 0.7159 | 0.0163 | 7708 | 0.571 |
| Random-key CProto equal bytes | 5 | 0.6325 | 0.0331 | 7708 | 0.472 |
| Random-key HOP equal bytes | 5 | 0.6157 | 0.0403 | 7708 | 0.702 |
| CHOP equal bytes | 5 | 0.6321 | 0.0272 | 7708 | 0.675 |
| Adaptive CHOP equal bytes | 5 | 0.7516 | 0.0111 | 7708 | 0.719 |

## Paired Seed Deltas

| Comparison | Mean delta | Wins | Normal approx. p |
|---|---:|---:|---:|
| CProto - zero-fill RFF equal bytes | 0.4086 | 5/5 | 0.0000 |
| CProto - shared-view RFF equal bytes | 0.3620 | 5/5 | 0.0000 |
| CProto - random-key HOP equal bytes | 0.1373 | 5/5 | 0.0000 |
| Random HOP - random CProto equal bytes | -0.0167 | 1/5 | 0.9999 |
| Group CProto - zero-fill RFF equal bytes | 0.3715 | 5/5 | 0.0000 |
| Group CProto - shared-view RFF equal bytes | 0.3249 | 5/5 | 0.0000 |
| Group all - coverage all | -0.0642 | 0/5 | 1.0000 |
| Coverage all - anchor PCA imputation | 0.0017 | 2/5 | 0.3460 |
| Coverage all - learned ridge imputation | 0.0116 | 4/5 | 0.0395 |
| Coverage all - anchor autoencoder imputation | 0.0284 | 5/5 | 0.0000 |
| Coverage all - mask-aware pooled MLP | 0.0240 | 4/5 | 0.0030 |
| Coverage all - HeMIS modality dropout | -0.0398 | 0/5 | 1.0000 |
| Coverage all - view-wise late fusion | 0.0642 | 5/5 | 0.0000 |
| Group all - HeMIS modality dropout | -0.1041 | 0/5 | 1.0000 |
| CHOP - CProto equal bytes | -0.1210 | 0/5 | 1.0000 |
| CHOP - zero-fill RFF equal bytes | 0.2876 | 5/5 | 0.0000 |
| CHOP - shared-view RFF equal bytes | 0.2410 | 5/5 | 0.0000 |
| CHOP - random-key HOP equal bytes | 0.0163 | 4/5 | 0.1536 |
| CHOP - anchor PCA imputation | -0.1474 | 0/5 | 1.0000 |
| CHOP - learned ridge imputation | -0.1376 | 0/5 | 1.0000 |
| CHOP - anchor autoencoder imputation | -0.1207 | 0/5 | 1.0000 |
| CHOP - mask-aware pooled MLP | -0.1252 | 0/5 | 1.0000 |
| CHOP - HeMIS modality dropout | -0.1890 | 0/5 | 1.0000 |
| CHOP - view-wise late fusion | -0.0849 | 0/5 | 1.0000 |
| Adaptive CHOP - CProto equal bytes | -0.0015 | 0/5 | 0.8413 |
| Adaptive CHOP - CHOP equal bytes | 0.1195 | 5/5 | 0.0000 |
| Adaptive CHOP - zero-fill RFF equal bytes | 0.4071 | 5/5 | 0.0000 |
| Adaptive CHOP - shared-view RFF equal bytes | 0.3605 | 5/5 | 0.0000 |
| Adaptive CHOP - random-key HOP equal bytes | 0.1359 | 5/5 | 0.0000 |
| Adaptive CHOP - HeMIS modality dropout | -0.0695 | 0/5 | 1.0000 |

