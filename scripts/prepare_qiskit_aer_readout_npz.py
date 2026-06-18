from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
QDEPS = ROOT / ".qdeps"
if QDEPS.exists():
    sys.path.insert(0, str(QDEPS))

from qprotohop.data import load_npz_dataset  # noqa: E402


def pca_angle_features(x_train: np.ndarray, x_test: np.ndarray, *, n_qubits: int) -> tuple[np.ndarray, np.ndarray]:
    n_components = 2 * n_qubits
    mean = x_train.mean(axis=0, keepdims=True)
    xt = x_train - mean
    xv = x_test - mean
    _, _, vt = np.linalg.svd(xt, full_matrices=False)
    proj = vt[:n_components].T
    a_train = xt @ proj
    a_test = xv @ proj
    scale = np.percentile(np.abs(a_train), 90, axis=0, keepdims=True) + 1e-8
    a_train = np.clip((np.pi / 2.0) * a_train / scale, -np.pi, np.pi)
    a_test = np.clip((np.pi / 2.0) * a_test / scale, -np.pi, np.pi)
    return a_train.astype(np.float64), a_test.astype(np.float64)


def observable_specs(n_qubits: int) -> list[tuple[str, int]]:
    return [(basis, q) for basis in ["X", "Y", "Z"] for q in range(n_qubits)]


def build_circuits(angles: np.ndarray, *, n_qubits: int, depth: int, weights: np.ndarray, specs: list[tuple[str, int]]):
    from qiskit import QuantumCircuit

    circuits = []
    for sample_id, a in enumerate(angles):
        for basis, q_meas in specs:
            qc = QuantumCircuit(n_qubits, 1)
            qc.metadata = {"sample_id": sample_id, "basis": basis, "wire": q_meas}
            for q in range(n_qubits):
                qc.ry(float(a[q]), q)
                qc.rz(float(a[n_qubits + q]), q)
            for layer in range(depth):
                for q in range(n_qubits):
                    qc.cx(q, (q + 1) % n_qubits)
                for q in range(n_qubits):
                    qc.ry(float(weights[layer, q, 0]), q)
                    qc.rz(float(weights[layer, q, 1]), q)
            if basis == "X":
                qc.h(q_meas)
            elif basis == "Y":
                qc.sdg(q_meas)
                qc.h(q_meas)
            qc.measure(q_meas, 0)
            circuits.append(qc)
    return circuits


def make_noise_model(*, depol1: float, depol2: float, readout_p: float):
    from qiskit_aer.noise import NoiseModel, ReadoutError, depolarizing_error

    noise = NoiseModel()
    if depol1 > 0:
        noise.add_all_qubit_quantum_error(depolarizing_error(depol1, 1), ["ry", "rz", "h", "sdg"])
    if depol2 > 0:
        noise.add_all_qubit_quantum_error(depolarizing_error(depol2, 2), ["cx"])
    if readout_p > 0:
        noise.add_all_qubit_readout_error(ReadoutError([[1 - readout_p, readout_p], [readout_p, 1 - readout_p]]))
    return noise


def run_aer_expectations(
    angles: np.ndarray,
    *,
    n_qubits: int,
    depth: int,
    specs: list[tuple[str, int]],
    weights: np.ndarray,
    shots: int,
    depol1: float,
    depol2: float,
    readout_p: float,
    seed: int,
    chunk_size: int,
) -> np.ndarray:
    from qiskit import transpile
    from qiskit_aer import AerSimulator

    noise = make_noise_model(depol1=depol1, depol2=depol2, readout_p=readout_p)
    sim = AerSimulator(noise_model=noise, seed_simulator=seed)
    circuits = build_circuits(angles, n_qubits=n_qubits, depth=depth, weights=weights, specs=specs)
    out = np.zeros((len(angles), len(specs)), dtype=np.float64)
    for start in range(0, len(circuits), chunk_size):
        chunk = circuits[start : start + chunk_size]
        tqc = transpile(chunk, sim, optimization_level=0)
        result = sim.run(tqc, shots=shots).result()
        for local_idx, qc in enumerate(chunk):
            counts = result.get_counts(local_idx)
            n0 = counts.get("0", 0)
            n1 = counts.get("1", 0)
            sample_id = int(qc.metadata["sample_id"])
            spec_id = specs.index((qc.metadata["basis"], qc.metadata["wire"]))
            out[sample_id, spec_id] = (n0 - n1) / max(shots, 1)
        print(f"computed circuits {min(start + chunk_size, len(circuits))}/{len(circuits)}", flush=True)
    return out


def main() -> None:
    ap = argparse.ArgumentParser("Generate Qiskit Aer noisy readout npz for QProto")
    ap.add_argument("--source", type=str, required=True)
    ap.add_argument("--out", type=str, required=True)
    ap.add_argument("--n-classes", type=int, default=4)
    ap.add_argument("--n-train", type=int, default=300)
    ap.add_argument("--n-test", type=int, default=120)
    ap.add_argument("--n-qubits", type=int, default=4)
    ap.add_argument("--depth", type=int, default=1)
    ap.add_argument("--shots", type=int, default=256)
    ap.add_argument("--depol1", type=float, default=0.002)
    ap.add_argument("--depol2", type=float, default=0.01)
    ap.add_argument("--readout-p", type=float, default=0.02)
    ap.add_argument("--chunk-size", type=int, default=200)
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
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        out,
        xtr=xtr.astype(np.float32),
        ytr=dataset.y_train.astype(np.int64),
        xte=xte.astype(np.float32),
        yte=dataset.y_test.astype(np.int64),
        observable_specs=np.asarray([str(s) for s in specs]),
        backend=np.asarray(["qiskit_aer_noisy"]),
        n_qubits=np.asarray([args.n_qubits]),
        depth=np.asarray([args.depth]),
        shots=np.asarray([args.shots]),
        depol1=np.asarray([args.depol1]),
        depol2=np.asarray([args.depol2]),
        readout_p=np.asarray([args.readout_p]),
    )
    print(f"Wrote {out} train={xtr.shape} test={xte.shape}")


if __name__ == "__main__":
    main()

