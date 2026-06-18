# Quantum-Parameter VQC Federated Baseline

This is a standard trainable PennyLane VQC baseline with shared ansatz and canonical Pauli-Z class readout. It is included as a parameter-aggregation reference; unlike QProto, it assumes homogeneous model/readout semantics.

| Method | n | Acc. | 95% CI | Bal. acc. | Bytes/client/round | Params |
|---|---:|---:|---:|---:|---:|---:|
| vqc_centralized | 5 | 0.5200 | 0.0625 | 0.4999 | 128 | 16 |
| vqc_fedavg | 5 | 0.5350 | 0.0841 | 0.5145 | 128 | 16 |
| vqc_fedprox | 5 | 0.5340 | 0.0824 | 0.5133 | 128 | 16 |
| vqc_init | 5 | 0.2430 | 0.0854 | 0.2355 | 128 | 16 |
