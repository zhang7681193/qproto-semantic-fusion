# Pairwise Delta Report

| Comparison | Group | n | Mean acc. delta | 95% CI | Wins |
|---|---|---:|---:|---:|---:|
| masked-HOP minus masked | PennyLane high-order | 3 | 0.1277 | 0.0421 | 3/3 |
| masked-HOP minus old-HOP | PennyLane high-order | 3 | 0.2296 | 0.0350 | 3/3 |
| CHOP minus CProto | PennyLane high-order K=8 | 3 | 0.2496 | 0.0705 | 3/3 |
| coverage-key CHOP minus random-key CHOP | PennyLane high-order K=8 | 5 | 0.2282 | 0.0664 | 5/5 |
| variance-key CHOP minus random-key CHOP | MNIST-10 K=96 | 3 | 0.0886 | 0.0160 | 3/3 |
| coverage-key CHOP minus random-key CHOP | CIFAR-10 K=96 | 3 | 0.0614 | 0.0440 | 3/3 |
| CHOP minus schema-FedProto | MNIST-10 strong-baseline | 3 | 0.3333 | 0.0269 | 3/3 |
| CHOP minus schema-FedProto | CIFAR-10 strong-baseline | 3 | 0.1785 | 0.0579 | 3/3 |
| CHOP minus schema-FedProto | Qiskit Aer strong-baseline | 3 | 0.1514 | 0.2268 | 3/3 |
| CHOP minus schema-FedProto | PennyLane high-order strong-baseline | 3 | 0.3172 | 0.0312 | 3/3 |
| CHOP minus FedAdam | PennyLane high-order strong-baseline | 3 | 0.2435 | 0.0690 | 3/3 |
| CHOP minus schema-FedAdam | MNIST-10 schema-head | 3 | 0.2906 | 0.0309 | 3/3 |
| CHOP minus schema-FedAdam | CIFAR-10 schema-head | 3 | 0.1690 | 0.0540 | 3/3 |
| CHOP minus schema-FedAdam | PennyLane high-order schema-head | 3 | 0.2856 | 0.0424 | 3/3 |


