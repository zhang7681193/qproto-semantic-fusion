# Experiment Fairness Audit

## Seed Coverage

| Group | Seeds found | Count |
|---|---:|---:|
| Final MNIST-10 full-class | 0,1,2,3,4 | 5 |
| Final Fashion-10 full-class | 0,1,2,3,4 | 5 |
| Final CIFAR-10 full-class | 0,1,2,3,4 | 5 |
| IF fusion MNIST-10 | 0,1,2,3,4 | 5 |
| IF fusion Fashion-10 | 0,1,2,3,4 | 5 |
| IF fusion CIFAR-10 | 0,1,2,3,4 | 5 |
| IF scientific fusion | 0,1,2,3,4 | 5 |
| MNIST-10 full-class | 0,1,2 | 3 |
| Fashion-10 full-class | 0,1,2 | 3 |
| CIFAR-10 full-class | 0,1,2 | 3 |
| Qiskit Aer noise | 0,1,2,3,4 | 5 |
| Qiskit Aer drift | 0,1,2 | 3 |
| PennyLane high-order drift | 0,1,2 | 3 |
| MNIST-10 scale/overlap | 0,1,2 | 3 |
| Fashion-10 scale/overlap | 0,1,2 | 3 |
| CIFAR-10 scale/overlap | 0,1,2 | 3 |
| PennyLane high-order overlap | 0,1,2 | 3 |

## Automated Checks

Status: PASS

- No missing LaTeX table inputs detected.
- Qiskit Aer noise-sweep runs do not add downstream synthetic noise.
- Required methods are present in strong/drift/noise baseline groups.
- Communication accounting is internally consistent for audited baselines.

Notes:
- topjournal_mnist10_shared_seed0 is an auxiliary legacy run and is excluded from formal full-class tables.

## Interpretation

The audit checks mechanical fairness and metadata consistency. It does not prove that every baseline is globally optimally tuned; tuned FedAdam/FedProto/SCAFFOLD/FedDyn audits should be reported as optimizer baselines, while QProto variants should be compared at matched or explicitly stated communication budgets.


