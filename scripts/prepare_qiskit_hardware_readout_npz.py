from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
QDEPS = ROOT / ".qdeps"
if QDEPS.exists():
    sys.path.insert(0, str(QDEPS))
SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from qprotohop.data import load_npz_dataset  # noqa: E402
from prepare_qiskit_aer_readout_npz import (  # noqa: E402
    build_circuits,
    observable_specs,
    pca_angle_features,
    run_aer_expectations,
)


def _bit_expectation(counts: dict, shots: int) -> float:
    n0 = 0
    n1 = 0
    for key, value in counts.items():
        bit = str(key).replace(" ", "")[-1]
        if bit == "0":
            n0 += int(value)
        elif bit == "1":
            n1 += int(value)
    return float(n0 - n1) / max(int(shots), 1)


def _load_ibm_backend(*, backend_name: str, token_env: str, instance: str = ""):
    token = os.environ.get(token_env, "") if token_env else ""
    try:
        from qiskit_ibm_runtime import QiskitRuntimeService

        kwargs = {}
        if token:
            kwargs["token"] = token
        if instance:
            kwargs["instance"] = instance
        try:
            service = QiskitRuntimeService(channel="ibm_quantum_platform", **kwargs)
        except TypeError:
            service = QiskitRuntimeService(**kwargs)
        return service.backend(backend_name)
    except Exception as runtime_error:
        try:
            from qiskit_ibm_provider import IBMProvider

            provider = IBMProvider(token=token) if token else IBMProvider()
            return provider.get_backend(backend_name)
        except Exception as provider_error:
            raise RuntimeError(
                "IBM backend access requires qiskit-ibm-runtime or qiskit-ibm-provider "
                f"and a valid token in {token_env}. Runtime error: {runtime_error}; "
                f"provider error: {provider_error}"
            ) from provider_error


def run_backend_expectations(
    angles: np.ndarray,
    *,
    backend,
    n_qubits: int,
    depth: int,
    specs: list[tuple[str, int]],
    weights: np.ndarray,
    shots: int,
    chunk_size: int,
    optimization_level: int,
) -> np.ndarray:
    from qiskit import transpile

    circuits = build_circuits(angles, n_qubits=n_qubits, depth=depth, weights=weights, specs=specs)
    out = np.zeros((len(angles), len(specs)), dtype=np.float64)
    spec_to_id = {spec: i for i, spec in enumerate(specs)}
    for start in range(0, len(circuits), chunk_size):
        chunk = circuits[start : start + chunk_size]
        tqc = transpile(chunk, backend, optimization_level=optimization_level)
        job = backend.run(tqc, shots=shots)
        print(f"submitted {job.job_id()} circuits {start + 1}-{min(start + len(chunk), len(circuits))}", flush=True)
        result = job.result()
        for local_idx, qc in enumerate(chunk):
            counts = result.get_counts(local_idx)
            sample_id = int(qc.metadata["sample_id"])
            spec_id = spec_to_id[(qc.metadata["basis"], qc.metadata["wire"])]
            out[sample_id, spec_id] = _bit_expectation(counts, shots)
        print(f"completed circuits {min(start + chunk_size, len(circuits))}/{len(circuits)}", flush=True)
    return out


def save_dataset(
    *,
    out: Path,
    xtr: np.ndarray,
    ytr: np.ndarray,
    xte: np.ndarray,
    yte: np.ndarray,
    specs: list[tuple[str, int]],
    metadata: dict,
) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        out,
        xtr=xtr.astype(np.float32),
        ytr=ytr.astype(np.int64),
        xte=xte.astype(np.float32),
        yte=yte.astype(np.int64),
        observable_specs=np.asarray([str(s) for s in specs]),
        metadata_json=np.asarray([json.dumps(metadata, sort_keys=True)]),
        backend=np.asarray([metadata.get("backend", "unknown")]),
        n_qubits=np.asarray([metadata["n_qubits"]]),
        depth=np.asarray([metadata["depth"]]),
        shots=np.asarray([metadata["shots"]]),
    )
    print(f"Wrote {out} train={xtr.shape} test={xte.shape}")


def main() -> None:
    ap = argparse.ArgumentParser("Generate hardware-ready Qiskit observable readout npz for QProto")
    ap.add_argument("--source", type=str, required=True)
    ap.add_argument("--out", type=str, required=True)
    ap.add_argument("--backend-mode", type=str, default="aer", choices=["aer", "ibm"])
    ap.add_argument("--ibm-backend", type=str, default="")
    ap.add_argument("--token-env", type=str, default="IBM_QUANTUM_TOKEN")
    ap.add_argument("--instance", type=str, default="")
    ap.add_argument("--n-classes", type=int, default=2)
    ap.add_argument("--n-train", type=int, default=120)
    ap.add_argument("--n-test", type=int, default=60)
    ap.add_argument("--n-qubits", type=int, default=4)
    ap.add_argument("--depth", type=int, default=1)
    ap.add_argument("--shots", type=int, default=512)
    ap.add_argument("--depol1", type=float, default=0.002)
    ap.add_argument("--depol2", type=float, default=0.01)
    ap.add_argument("--readout-p", type=float, default=0.02)
    ap.add_argument("--chunk-size", type=int, default=120)
    ap.add_argument("--optimization-level", type=int, default=1)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    dataset = load_npz_dataset(
        args.source,
        n_train=args.n_train,
        n_test=args.n_test,
        n_classes=args.n_classes,
        test_fraction=0.25,
        seed=args.seed,
    )
    a_train, a_test = pca_angle_features(dataset.x_train, dataset.x_test, n_qubits=args.n_qubits)
    rng = np.random.default_rng(args.seed + 17)
    weights = rng.normal(0.0, 0.35, size=(args.depth, args.n_qubits, 2))
    specs = observable_specs(args.n_qubits)

    metadata = {
        "backend_mode": args.backend_mode,
        "backend": "qiskit_aer_hardware_protocol" if args.backend_mode == "aer" else args.ibm_backend,
        "n_classes": args.n_classes,
        "n_train": int(len(dataset.y_train)),
        "n_test": int(len(dataset.y_test)),
        "n_qubits": args.n_qubits,
        "depth": args.depth,
        "shots": args.shots,
        "seed": args.seed,
        "n_observables": len(specs),
    }

    if args.backend_mode == "aer":
        xtr = run_aer_expectations(
            a_train,
            n_qubits=args.n_qubits,
            depth=args.depth,
            specs=specs,
            weights=weights,
            shots=args.shots,
            depol1=args.depol1,
            depol2=args.depol2,
            readout_p=args.readout_p,
            seed=args.seed + 101,
            chunk_size=args.chunk_size,
        )
        xte = run_aer_expectations(
            a_test,
            n_qubits=args.n_qubits,
            depth=args.depth,
            specs=specs,
            weights=weights,
            shots=args.shots,
            depol1=args.depol1,
            depol2=args.depol2,
            readout_p=args.readout_p,
            seed=args.seed + 202,
            chunk_size=args.chunk_size,
        )
        metadata.update({"depol1": args.depol1, "depol2": args.depol2, "readout_p": args.readout_p})
    else:
        if not args.ibm_backend:
            raise ValueError("--ibm-backend is required when --backend-mode ibm")
        backend = _load_ibm_backend(backend_name=args.ibm_backend, token_env=args.token_env, instance=args.instance)
        xtr = run_backend_expectations(
            a_train,
            backend=backend,
            n_qubits=args.n_qubits,
            depth=args.depth,
            specs=specs,
            weights=weights,
            shots=args.shots,
            chunk_size=args.chunk_size,
            optimization_level=args.optimization_level,
        )
        xte = run_backend_expectations(
            a_test,
            backend=backend,
            n_qubits=args.n_qubits,
            depth=args.depth,
            specs=specs,
            weights=weights,
            shots=args.shots,
            chunk_size=args.chunk_size,
            optimization_level=args.optimization_level,
        )

    save_dataset(
        out=Path(args.out),
        xtr=xtr,
        ytr=dataset.y_train,
        xte=xte,
        yte=dataset.y_test,
        specs=specs,
        metadata=metadata,
    )


if __name__ == "__main__":
    main()

