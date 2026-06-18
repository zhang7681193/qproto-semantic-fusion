# Real MHEALTH Wearable Multi-Source Fusion Benchmark

The task uses the real UCI MHEALTH wearable activity-recognition dataset. Chest, ECG, ankle, and arm sensor modalities are treated as semantic sources; each client observes only a heterogeneous subset.

| Method | n | Acc. | 95% CI | Bytes | Runtime s |
|---|---:|---:|---:|---:|---:|
| Mask-only metadata | 10 | 0.0840 | 0.0027 | 11092 | 0.580 |
| Zero-fill prototype | 10 | 0.7891 | 0.0242 | 11092 | 0.586 |
| Mean-impute prototype | 10 | 0.7894 | 0.0256 | 11092 | 0.705 |
| Value+mask prototype | 10 | 0.2660 | 0.0169 | 22132 | 1.229 |
| Anchor PCA imputation | 10 | 0.7598 | 0.0278 | 11092 | 11.689 |
| Learned ridge imputation | 10 | 0.8278 | 0.0279 | 11092 | 1.329 |
| Anchor autoencoder imputation | 10 | 0.8041 | 0.0290 | 11092 | 11.248 |
| Mask-aware pooled MLP | 10 | 0.8603 | 0.0199 | 22132 | 1.853 |
| HeMIS modality-dropout fusion | 10 | 0.8890 | 0.0246 | 22132 | 7.169 |
| View-wise late fusion | 10 | 0.8142 | 0.0261 | 11092 | 0.333 |
| Shared-view prototype | 10 | 0.7186 | 0.0440 | 1492 | 0.072 |
| Shared-view RFF equal bytes | 10 | 0.7205 | 0.0458 | 13876 | 0.864 |
| Zero-fill RFF equal bytes | 10 | 0.7743 | 0.0277 | 13876 | 1.005 |
| Coverage prototype all | 10 | 0.8198 | 0.0268 | 22132 | 1.406 |
| Group-balanced CProto all | 10 | 0.8142 | 0.0261 | 22132 | 1.644 |
| CProto equal bytes | 10 | 0.8598 | 0.0173 | 13876 | 0.917 |
| Group-balanced CProto equal bytes | 10 | 0.8260 | 0.0149 | 13876 | 1.034 |
| Random-key CProto equal bytes | 10 | 0.7981 | 0.0329 | 13876 | 0.625 |
| Random-key HOP equal bytes | 10 | 0.7981 | 0.0328 | 13876 | 1.209 |
| CHOP equal bytes | 10 | 0.8650 | 0.0407 | 13876 | 1.217 |
| Adaptive CHOP equal bytes | 10 | 0.8776 | 0.0218 | 13876 | 1.200 |

## Paired Seed Deltas

| Comparison | Mean delta | Wins | Normal approx. p |
|---|---:|---:|---:|
| CProto - zero-fill RFF equal bytes | 0.0856 | 10/10 | 0.0000 |
| CProto - shared-view RFF equal bytes | 0.1394 | 10/10 | 0.0000 |
| CProto - random-key HOP equal bytes | 0.0617 | 9/10 | 0.0000 |
| Random HOP - random CProto equal bytes | 0.0000 | 6/10 | 0.3830 |
| Group CProto - zero-fill RFF equal bytes | 0.0517 | 10/10 | 0.0000 |
| Group CProto - shared-view RFF equal bytes | 0.1056 | 10/10 | 0.0000 |
| Group all - coverage all | -0.0057 | 4/10 | 0.9376 |
| Coverage all - anchor PCA imputation | 0.0601 | 10/10 | 0.0000 |
| Coverage all - learned ridge imputation | -0.0079 | 3/10 | 0.9386 |
| Coverage all - anchor autoencoder imputation | 0.0158 | 8/10 | 0.0146 |
| Coverage all - mask-aware pooled MLP | -0.0405 | 0/10 | 1.0000 |
| Coverage all - HeMIS modality dropout | -0.0692 | 0/10 | 1.0000 |
| Coverage all - view-wise late fusion | 0.0057 | 6/10 | 0.0624 |
| Group all - HeMIS modality dropout | -0.0748 | 0/10 | 1.0000 |
| CHOP - CProto equal bytes | 0.0052 | 6/10 | 0.3919 |
| CHOP - zero-fill RFF equal bytes | 0.0907 | 9/10 | 0.0004 |
| CHOP - shared-view RFF equal bytes | 0.1446 | 9/10 | 0.0000 |
| CHOP - random-key HOP equal bytes | 0.0669 | 9/10 | 0.0150 |
| CHOP - anchor PCA imputation | 0.1052 | 9/10 | 0.0002 |
| CHOP - learned ridge imputation | 0.0372 | 8/10 | 0.0810 |
| CHOP - anchor autoencoder imputation | 0.0609 | 9/10 | 0.0081 |
| CHOP - mask-aware pooled MLP | 0.0047 | 7/10 | 0.4134 |
| CHOP - HeMIS modality dropout | -0.0240 | 3/10 | 0.8308 |
| CHOP - view-wise late fusion | 0.0508 | 9/10 | 0.0329 |
| Adaptive CHOP - CProto equal bytes | 0.0178 | 6/10 | 0.0018 |
| Adaptive CHOP - CHOP equal bytes | 0.0126 | 4/10 | 0.2535 |
| Adaptive CHOP - zero-fill RFF equal bytes | 0.1034 | 10/10 | 0.0000 |
| Adaptive CHOP - shared-view RFF equal bytes | 0.1572 | 10/10 | 0.0000 |
| Adaptive CHOP - random-key HOP equal bytes | 0.0795 | 9/10 | 0.0000 |
| Adaptive CHOP - HeMIS modality dropout | -0.0114 | 2/10 | 0.8582 |

