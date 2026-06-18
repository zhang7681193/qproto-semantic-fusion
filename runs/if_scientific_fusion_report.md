# IF-Style Scientific Fusion Report

Synthetic non-image latent covariance-sensing task. Classes have weak mean signal and differ mainly through high-order readout structure; clients observe heterogeneous observable subsets.

| Method | n | Acc. | 95% CI | Bal. acc. | Bytes |
|---|---:|---:|---:|---:|---:|
| Mask-only metadata | 5 | 0.2007 | 0.0019 | 0.2000 | 1944 |
| Schema zero-fill | 5 | 0.6273 | 0.0295 | 0.6263 | 1944 |
| No schema | 5 | 0.2926 | 0.0160 | 0.2920 | 1944 |
| Forced canonical | 5 | 0.2901 | 0.0093 | 0.2888 | 1944 |
| Shared observables | 5 | 0.6267 | 0.0696 | 0.6264 | 1944 |
| FedProto schema | 5 | 0.2898 | 0.0108 | 0.2888 | 1944 |
| FedAdam schema | 5 | 0.3325 | 0.0128 | 0.3305 | 1940 |
| QProto-Masked | 5 | 0.3718 | 0.0130 | 0.3714 | 3864 |
| CProto | 5 | 0.3581 | 0.0276 | 0.3574 | 1944 |
| QProto-Masked-HOP | 5 | 0.6909 | 0.0412 | 0.6928 | 5784 |
| CHOP | 5 | 0.7324 | 0.0237 | 0.7344 | 3864 |

