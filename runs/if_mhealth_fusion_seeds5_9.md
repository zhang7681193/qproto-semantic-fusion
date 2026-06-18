# Real MHEALTH Wearable Multi-Source Fusion Benchmark

The task uses the real UCI MHEALTH wearable activity-recognition dataset. Chest, ECG, ankle, and arm sensor modalities are treated as semantic sources; each client observes only a heterogeneous subset.

| Method | n | Acc. | 95% CI | Bytes | Runtime s |
|---|---:|---:|---:|---:|---:|
| Mask-only metadata | 5 | 0.0840 | 0.0047 | 11092 | 0.559 |
| Zero-fill prototype | 5 | 0.7744 | 0.0590 | 11092 | 0.572 |
| Mean-impute prototype | 5 | 0.7739 | 0.0617 | 11092 | 0.667 |
| Value+mask prototype | 5 | 0.2516 | 0.0166 | 22132 | 1.193 |
| Anchor PCA imputation | 5 | 0.7499 | 0.0618 | 11092 | 11.416 |
| Learned ridge imputation | 5 | 0.8109 | 0.0552 | 11092 | 1.334 |
| Anchor autoencoder imputation | 5 | 0.7833 | 0.0517 | 11092 | 10.518 |
| Mask-aware pooled MLP | 5 | 0.8404 | 0.0415 | 22132 | 1.751 |
| View-wise late fusion | 5 | 0.8013 | 0.0558 | 11092 | 0.318 |
| Shared-view prototype | 5 | 0.7258 | 0.0715 | 1492 | 0.072 |
| Shared-view RFF equal bytes | 5 | 0.7302 | 0.0762 | 13876 | 0.875 |
| Zero-fill RFF equal bytes | 5 | 0.7583 | 0.0630 | 13876 | 1.015 |
| Coverage prototype all | 5 | 0.8067 | 0.0537 | 22132 | 1.410 |
| Group-balanced CProto all | 5 | 0.8013 | 0.0558 | 22132 | 1.657 |
| CProto equal bytes | 5 | 0.8402 | 0.0302 | 13876 | 0.910 |
| Group-balanced CProto equal bytes | 5 | 0.8103 | 0.0255 | 13876 | 1.006 |
| Random-key CProto equal bytes | 5 | 0.7973 | 0.0693 | 13876 | 0.611 |
| Random-key HOP equal bytes | 5 | 0.7973 | 0.0694 | 13876 | 1.166 |
| CHOP equal bytes | 5 | 0.8280 | 0.0963 | 13876 | 1.181 |
| Adaptive CHOP equal bytes | 5 | 0.8620 | 0.0532 | 13876 | 1.164 |

## Paired Seed Deltas

| Comparison | Mean delta | Wins | Normal approx. p |
|---|---:|---:|---:|
| CProto - zero-fill RFF equal bytes | 0.0819 | 5/5 | 0.0000 |
| CProto - shared-view RFF equal bytes | 0.1100 | 5/5 | 0.0000 |
| CProto - random-key HOP equal bytes | 0.0429 | 4/5 | 0.0114 |
| Random HOP - random CProto equal bytes | -0.0000 | 3/5 | 0.5244 |
| Group CProto - zero-fill RFF equal bytes | 0.0520 | 5/5 | 0.0003 |
| Group CProto - shared-view RFF equal bytes | 0.0801 | 5/5 | 0.0002 |
| Group all - coverage all | -0.0054 | 2/5 | 0.9035 |
| Coverage all - anchor PCA imputation | 0.0568 | 5/5 | 0.0000 |
| Coverage all - learned ridge imputation | -0.0042 | 2/5 | 0.7000 |
| Coverage all - anchor autoencoder imputation | 0.0233 | 5/5 | 0.0280 |
| Coverage all - mask-aware pooled MLP | -0.0337 | 0/5 | 0.9966 |
| Coverage all - view-wise late fusion | 0.0054 | 3/5 | 0.0965 |
| CHOP - CProto equal bytes | -0.0122 | 2/5 | 0.6304 |
| CHOP - zero-fill RFF equal bytes | 0.0697 | 4/5 | 0.0955 |
| CHOP - shared-view RFF equal bytes | 0.0978 | 4/5 | 0.0282 |
| CHOP - random-key HOP equal bytes | 0.0308 | 4/5 | 0.2837 |
| CHOP - anchor PCA imputation | 0.0781 | 4/5 | 0.0739 |
| CHOP - learned ridge imputation | 0.0172 | 4/5 | 0.3685 |
| CHOP - anchor autoencoder imputation | 0.0447 | 4/5 | 0.1761 |
| CHOP - mask-aware pooled MLP | -0.0123 | 3/5 | 0.6131 |
| CHOP - view-wise late fusion | 0.0268 | 4/5 | 0.3044 |
| Adaptive CHOP - CProto equal bytes | 0.0218 | 3/5 | 0.0261 |
| Adaptive CHOP - CHOP equal bytes | 0.0339 | 3/5 | 0.1654 |
| Adaptive CHOP - zero-fill RFF equal bytes | 0.1037 | 5/5 | 0.0000 |
| Adaptive CHOP - shared-view RFF equal bytes | 0.1318 | 5/5 | 0.0000 |
| Adaptive CHOP - random-key HOP equal bytes | 0.0647 | 4/5 | 0.0026 |

