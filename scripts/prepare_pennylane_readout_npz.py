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
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / ".mplcache"))

from qprotohop.data import load_npz_dataset  # noqa: E402


def make_observable_specs(n_qubits: int, max_observables: int) -> list[tuple[str, int, int | None]]:
    specs: list[tuple[str, int, int | None]] = []
    for basis in ["X", "Y", "Z"]:
        for q in range(n_qubits):
            specs.append((basis, q, None))
    for basis in ["XX", "YY", "ZZ"]:
        for a in range(n_qubits):
            for b in range(a + 1, n_qubits):
                specs.append((basis, a, b))
    return specs[:max_observables]


def build_qnode(*, n_qubits: int, depth: int, specs: list[tuple[str, int, int | None]], seed: int):
    import pennylane as qml

    rng = np.random.default_rng(seed)
    weights = rng.normal(0.0, 0.45, size=(depth, n_qubits, 2))
    dev = qml.device("default.qubit", wires=n_qubits, shots=None)

    def obs_from_spec(spec: tuple[str, int, int | None]):
        basis, a, b = spec
        if b is None:
            if basis == "X":
                return qml.PauliX(a)
            if basis == "Y":
                return qml.PauliY(a)
            return qml.PauliZ(a)
        if basis == "XX":
            return qml.PauliX(a) @ qml.PauliX(b)
        if basis == "YY":
            return qml.PauliY(a) @ qml.PauliY(b)
        return qml.PauliZ(a) @ qml.PauliZ(b)

    observables = [obs_from_spec(s) for s in specs]

    @qml.qnode(dev, interface=None)
    def circuit(angles: np.ndarray):
        for q in range(n_qubits):
            qml.RY(float(angles[q]), wires=q)
            qml.RZ(float(angles[n_qubits + q]), wires=q)
        for layer in range(depth):
            for q in range(n_qubits):
                qml.CNOT(wires=[q, (q + 1) % n_qubits])
            for q in range(n_qubits):
                qml.RY(float(weights[layer, q, 0]), wires=q)
                qml.RZ(float(weights[layer, q, 1]), wires=q)
        return [qml.expval(o) for o in observables]

    return circuit


def random_angle_features(x: np.ndarray, *, n_qubits: int, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    proj = rng.normal(0.0, 1.0 / np.sqrt(x.shape[1]), size=(x.shape[1], 2 * n_qubits))
    angles = x @ proj
    scale = np.std(angles, axis=0, keepdims=True) + 1e-8
    angles = np.clip(angles / scale, -3.0, 3.0)
    return angles.astype(np.float64)


def pca_angle_features(
    x_train: np.ndarray,
    x_test: np.ndarray,
    *,
    n_qubits: int,
) -> tuple[np.ndarray, np.ndarray]:
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


def compute_readouts(circuit, angles: np.ndarray, *, batch_log: int = 100) -> np.ndarray:
    rows = []
    for i, a in enumerate(angles):
        rows.append(np.asarray(circuit(a), dtype=np.float64))
        if batch_log > 0 and (i + 1) % batch_log == 0:
            print(f"computed {i + 1}/{len(angles)}", flush=True)
    return np.stack(rows, axis=0)


def class_signal_order(x: np.ndarray, y: np.ndarray, *, low_first: bool) -> np.ndarray:
    classes = np.unique(y)
    global_mean = x.mean(axis=0, keepdims=True)
    between = np.zeros((x.shape[1],), dtype=np.float64)
    within = np.zeros((x.shape[1],), dtype=np.float64)
    for c in classes:
        xc = x[y == c]
        if len(xc) == 0:
            continue
        diff = xc.mean(axis=0) - global_mean.reshape(-1)
        between += len(xc) * diff * diff
        within += ((xc - xc.mean(axis=0, keepdims=True)) ** 2).sum(axis=0)
    score = between / (within + 1e-8)
    return np.argsort(score) if low_first else np.argsort(-score)


def main() -> None:
    ap = argparse.ArgumentParser("Generate PennyLane VQC observable readout npz for QProto")
    ap.add_argument("--source", type=str, required=True)
    ap.add_argument("--out", type=str, required=True)
    ap.add_argument("--n-classes", type=int, default=4)
    ap.add_argument("--n-train", type=int, default=800)
    ap.add_argument("--n-test", type=int, default=300)
    ap.add_argument("--n-qubits", type=int, default=4)
    ap.add_argument("--depth", type=int, default=2)
    ap.add_argument("--observables", type=int, default=30)
    ap.add_argument("--angle-map", type=str, default="pca", choices=["pca", "random"])
    ap.add_argument("--sort-observables", type=str, default="none", choices=["none", "low-signal-first", "high-signal-first"])
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
    specs = make_observable_specs(args.n_qubits, args.observables)
    circuit = build_qnode(n_qubits=args.n_qubits, depth=args.depth, specs=specs, seed=args.seed + 17)
    if args.angle_map == "pca":
        a_train, a_test = pca_angle_features(dataset.x_train, dataset.x_test, n_qubits=args.n_qubits)
    else:
        a_train = random_angle_features(dataset.x_train, n_qubits=args.n_qubits, seed=args.seed + 23)
        a_test = random_angle_features(dataset.x_test, n_qubits=args.n_qubits, seed=args.seed + 23)
    xtr = compute_readouts(circuit, a_train)
    xte = compute_readouts(circuit, a_test)
    if args.sort_observables != "none":
        order = class_signal_order(xtr, dataset.y_train, low_first=args.sort_observables == "low-signal-first")
        xtr = xtr[:, order]
        xte = xte[:, order]
        specs = [specs[int(i)] for i in order]
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        out,
        xtr=xtr.astype(np.float32),
        ytr=dataset.y_train.astype(np.int64),
        xte=xte.astype(np.float32),
        yte=dataset.y_test.astype(np.int64),
        observable_specs=np.asarray([str(s) for s in specs]),
        backend=np.asarray(["pennylane_default_qubit"]),
        n_qubits=np.asarray([args.n_qubits]),
        depth=np.asarray([args.depth]),
        angle_map=np.asarray([args.angle_map]),
    )
    print(f"Wrote {out} train={xtr.shape} test={xte.shape}")


if __name__ == "__main__":
    main()

