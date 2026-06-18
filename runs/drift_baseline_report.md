# Drift-Control Baseline Report

## PennyLane high-order

| Method | n | Acc. | 95% CI | Bal. acc. | Bytes |
|---|---:|---:|---:|---:|---:|
| FedAdam schema | 3 | 0.3165 | 0.0213 | 0.3165 | 1552 |
| FedProto schema | 3 | 0.2849 | 0.0292 | 0.2849 | 1556 |
| SCAFFOLD schema | 3 | 0.2834 | 0.0087 | 0.2834 | 3104 |
| FedDyn schema | 3 | 0.2985 | 0.0112 | 0.2985 | 1552 |
| CProto | 3 | 0.4032 | 0.0609 | 0.4032 | 788 |
| CHOP | 3 | 0.6020 | 0.0605 | 0.6020 | 2324 |
| Masked-HOP | 3 | 0.5495 | 0.0090 | 0.5495 | 3476 |

## Qiskit Aer MNIST-4

| Method | n | Acc. | 95% CI | Bal. acc. | Bytes |
|---|---:|---:|---:|---:|---:|
| FedAdam schema | 3 | 0.4257 | 0.1782 | 0.4132 | 528 |
| FedProto schema | 3 | 0.4278 | 0.1967 | 0.4105 | 532 |
| SCAFFOLD schema | 3 | 0.3573 | 0.1906 | 0.3401 | 1056 |
| FedDyn schema | 3 | 0.4184 | 0.1875 | 0.3893 | 528 |
| CProto | 3 | 0.5760 | 0.0455 | 0.5655 | 276 |
| CHOP | 3 | 0.5792 | 0.0426 | 0.5684 | 532 |
| Masked-HOP | 3 | 0.5965 | 0.0650 | 0.5850 | 660 |


