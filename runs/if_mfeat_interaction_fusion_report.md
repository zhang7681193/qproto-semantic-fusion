# Semi-Real MFeat Cross-Source Interaction Benchmark

The task uses real UCI Multiple Features source vectors but defines labels by cross-source interaction signs. It is a semi-real stress test for high-order source fusion rather than a standard digit-recognition benchmark.

| Method | n | Acc. | 95% CI | Bytes | Runtime s |
|---|---:|---:|---:|---:|---:|
| Mask-only metadata | 5 | 0.2479 | 0.0098 | 10404 | 0.342 |
| Zero-fill prototype | 5 | 0.4264 | 0.0085 | 10404 | 0.331 |
| Mean-impute prototype | 5 | 0.4255 | 0.0071 | 10404 | 0.468 |
| Value+mask prototype | 5 | 0.2594 | 0.0308 | 20788 | 0.702 |
| Anchor PCA imputation | 5 | 0.4143 | 0.0146 | 10404 | 55.080 |
| Learned ridge imputation | 5 | 0.4268 | 0.0176 | 10404 | 6.214 |
| Anchor autoencoder imputation | 5 | 0.4293 | 0.0167 | 10404 | 33.362 |
| Mask-aware pooled MLP | 5 | 0.4613 | 0.0209 | 20788 | 3.142 |
| View-wise late fusion | 5 | 0.4208 | 0.0265 | 10404 | 0.178 |
| Shared-view prototype | 5 | 0.3977 | 0.0260 | 116 | 0.002 |
| Shared-view RFF equal bytes | 5 | 0.3973 | 0.0262 | 7188 | 0.652 |
| Zero-fill RFF equal bytes | 5 | 0.3958 | 0.0055 | 7188 | 1.837 |
| Coverage prototype all | 5 | 0.4280 | 0.0065 | 20788 | 0.696 |
| Group-balanced CProto all | 5 | 0.4208 | 0.0265 | 20788 | 1.055 |
| CProto equal bytes | 5 | 0.4146 | 0.0099 | 7188 | 0.291 |
| Group-balanced CProto equal bytes | 5 | 0.4126 | 0.0277 | 7188 | 0.366 |
| Random-key HOP equal bytes | 5 | 0.4201 | 0.0124 | 7188 | 0.264 |
| CHOP equal bytes | 5 | 0.4169 | 0.0159 | 7188 | 0.291 |

## Paired Seed Deltas

| Comparison | Mean delta | Wins | Normal approx. p |
|---|---:|---:|---:|
| CProto - zero-fill RFF equal bytes | 0.0188 | 5/5 | 0.0001 |
| CProto - shared-view RFF equal bytes | 0.0173 | 4/5 | 0.0139 |
| CProto - random-key HOP equal bytes | -0.0055 | 2/5 | 0.8888 |
| Group CProto - zero-fill RFF equal bytes | 0.0168 | 4/5 | 0.0741 |
| Group CProto - shared-view RFF equal bytes | 0.0153 | 5/5 | 0.0105 |
| Group all - coverage all | -0.0072 | 2/5 | 0.7874 |
| Coverage all - anchor PCA imputation | 0.0137 | 4/5 | 0.0200 |
| Coverage all - learned ridge imputation | 0.0012 | 4/5 | 0.4270 |
| Coverage all - anchor autoencoder imputation | -0.0013 | 3/5 | 0.5866 |
| Coverage all - mask-aware pooled MLP | -0.0333 | 0/5 | 1.0000 |
| Coverage all - view-wise late fusion | 0.0072 | 3/5 | 0.2126 |
| CHOP - CProto equal bytes | 0.0023 | 2/5 | 0.2771 |
| CHOP - zero-fill RFF equal bytes | 0.0211 | 5/5 | 0.0030 |
| CHOP - shared-view RFF equal bytes | 0.0196 | 5/5 | 0.0000 |
| CHOP - random-key HOP equal bytes | -0.0032 | 2/5 | 0.6984 |
| CHOP - anchor PCA imputation | 0.0027 | 4/5 | 0.3316 |
| CHOP - learned ridge imputation | -0.0098 | 0/5 | 0.9984 |
| CHOP - anchor autoencoder imputation | -0.0123 | 0/5 | 0.9986 |
| CHOP - mask-aware pooled MLP | -0.0443 | 0/5 | 1.0000 |
| CHOP - view-wise late fusion | -0.0038 | 1/5 | 0.8005 |

