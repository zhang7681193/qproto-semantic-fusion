# Real PAMAP2 Wearable Multi-Source Fusion Benchmark

The task uses the real UCI PAMAP2 wearable activity-recognition dataset. Heart-rate, hand, chest, and ankle IMU modalities are treated as semantic sources; each client observes only a heterogeneous subset.

| Method | n | Acc. | 95% CI | Bytes | Runtime s |
|---|---:|---:|---:|---:|---:|
| Mask-only metadata | 5 | 0.0809 | 0.0067 | 17812 | 2.110 |
| Zero-fill prototype | 5 | 0.6681 | 0.0333 | 17812 | 2.175 |
| Mean-impute prototype | 5 | 0.6694 | 0.0333 | 17812 | 2.519 |
| Value+mask prototype | 5 | 0.1989 | 0.0365 | 35572 | 4.269 |
| Anchor PCA imputation | 5 | 0.6930 | 0.0491 | 17812 | 61.355 |
| Learned ridge imputation | 5 | 0.7372 | 0.0469 | 17812 | 4.293 |
| View-wise late fusion | 5 | 0.7251 | 0.0418 | 17812 | 1.159 |
| Shared-view prototype | 5 | 0.2691 | 0.0212 | 532 | 0.062 |
| Shared-view RFF equal bytes | 5 | 0.2750 | 0.0204 | 18484 | 2.437 |
| Zero-fill RFF equal bytes | 5 | 0.6091 | 0.0654 | 18484 | 3.158 |
| Coverage prototype all | 5 | 0.7184 | 0.0452 | 35572 | 5.158 |
| Group-balanced CProto all | 5 | 0.7251 | 0.0418 | 35572 | 6.159 |
| CProto equal bytes | 5 | 0.7255 | 0.0412 | 18484 | 2.779 |
| Group-balanced CProto equal bytes | 5 | 0.7023 | 0.0579 | 18484 | 3.171 |
| Random-key CProto equal bytes | 5 | 0.7015 | 0.0390 | 18484 | 1.794 |
| Random-key HOP equal bytes | 5 | 0.7018 | 0.0394 | 18484 | 3.425 |
| CHOP equal bytes | 5 | 0.4955 | 0.1421 | 18484 | 3.447 |
| Adaptive CHOP equal bytes | 5 | 0.7255 | 0.0412 | 18484 | 3.098 |

## Paired Seed Deltas

| Comparison | Mean delta | Wins | Normal approx. p |
|---|---:|---:|---:|
| CProto - zero-fill RFF equal bytes | 0.1163 | 5/5 | 0.0000 |
| CProto - shared-view RFF equal bytes | 0.4505 | 5/5 | 0.0000 |
| CProto - random-key HOP equal bytes | 0.0236 | 5/5 | 0.0000 |
| Random HOP - random CProto equal bytes | 0.0004 | 4/5 | 0.0448 |
| Group CProto - zero-fill RFF equal bytes | 0.0931 | 5/5 | 0.0000 |
| Group CProto - shared-view RFF equal bytes | 0.4273 | 5/5 | 0.0000 |
| Group all - coverage all | 0.0067 | 3/5 | 0.1193 |
| Coverage all - anchor PCA imputation | 0.0254 | 5/5 | 0.0000 |
| Coverage all - learned ridge imputation | -0.0189 | 1/5 | 0.9943 |
| Coverage all - view-wise late fusion | -0.0067 | 2/5 | 0.8807 |
| CHOP - CProto equal bytes | -0.2300 | 0/5 | 1.0000 |
| CHOP - zero-fill RFF equal bytes | -0.1137 | 0/5 | 0.9989 |
| CHOP - shared-view RFF equal bytes | 0.2205 | 5/5 | 0.0000 |
| CHOP - random-key HOP equal bytes | -0.2064 | 0/5 | 1.0000 |
| CHOP - anchor PCA imputation | -0.1975 | 0/5 | 1.0000 |
| CHOP - learned ridge imputation | -0.2418 | 0/5 | 1.0000 |
| CHOP - view-wise late fusion | -0.2296 | 0/5 | 1.0000 |
| Adaptive CHOP - CProto equal bytes | 0.0000 | 0/5 | 1.0000 |
| Adaptive CHOP - CHOP equal bytes | 0.2300 | 5/5 | 0.0000 |
| Adaptive CHOP - zero-fill RFF equal bytes | 0.1163 | 5/5 | 0.0000 |
| Adaptive CHOP - shared-view RFF equal bytes | 0.4505 | 5/5 | 0.0000 |
| Adaptive CHOP - random-key HOP equal bytes | 0.0236 | 5/5 | 0.0000 |

