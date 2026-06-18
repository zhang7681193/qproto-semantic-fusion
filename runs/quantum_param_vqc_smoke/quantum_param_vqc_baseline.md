# Quantum-Parameter VQC Federated Baseline

This is a standard trainable PennyLane VQC baseline with shared ansatz and canonical Pauli-Z class readout. It is included as a parameter-aggregation reference; unlike QProto, it assumes homogeneous model/readout semantics.

| Method | n | Acc. | 95% CI | Bal. acc. | Bytes/client/round | Params |
|---|---:|---:|---:|---:|---:|---:|
| vqc_fedavg | 1 | 0.1500 | 0.0000 | 0.2121 | 128 | 16 |
| vqc_init | 1 | 0.1500 | 0.0000 | 0.2121 | 128 | 16 |
