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

from prepare_pennylane_readout_npz import build_qnode, compute_readouts, make_observable_specs  # noqa: E402


def balanced_labels(n: int, n_classes: int, rng: np.random.Generator) -> np.ndarray:
    y = np.arange(n, dtype=np.int64) % n_classes
    rng.shuffle(y)
    return y


def highorder_angles(
    y: np.ndarray,
    *,
    n_qubits: int,
    strength: float,
    noise: float,
    seed: int,
) -> np.ndarray:
    rng = np.random.default_rng(seed)
    dim = 2 * n_qubits
    angles = rng.normal(0.0, noise, size=(len(y), dim))
    pairs = [(i, (i + 1) % dim) for i in range(dim)]
    for c in np.unique(y):
        idx = np.where(y == c)[0]
        a, b = pairs[int(c) % len(pairs)]
        t = rng.normal(0.0, strength, size=len(idx))
        s = 1.0 if int(c) % 2 == 0 else -1.0
        angles[idx, a] += t
        angles[idx, b] += s * t + rng.normal(0.0, noise * 0.35, size=len(idx))
        if int(c) >= 2:
            c2 = (b + 2) % dim
            u = rng.normal(0.0, strength * 0.65, size=len(idx))
            angles[idx, b] += u
            angles[idx, c2] -= u + rng.normal(0.0, noise * 0.35, size=len(idx))
    return np.clip(angles, -np.pi, np.pi).astype(np.float64)


def equalize_class_means(x_train: np.ndarray, y_train: np.ndarray, x_test: np.ndarray, y_test: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Remove first-order class mean signal to make the task HOP-dominated."""

    global_mean = x_train.mean(axis=0, keepdims=True)
    x_train_eq = x_train.copy()
    x_test_eq = x_test.copy()
    for c in np.unique(y_train):
        train_mask = y_train == c
        test_mask = y_test == c
        shift = x_train[train_mask].mean(axis=0, keepdims=True) - global_mean
        x_train_eq[train_mask] -= shift
        x_test_eq[test_mask] -= shift
    return np.clip(x_train_eq, -1.0, 1.0), np.clip(x_test_eq, -1.0, 1.0)


def main() -> None:
    ap = argparse.ArgumentParser("Generate a PennyLane high-order readout benchmark")
    ap.add_argument("--out", type=str, required=True)
    ap.add_argument("--n-classes", type=int, default=4)
    ap.add_argument("--n-train", type=int, default=1200)
    ap.add_argument("--n-test", type=int, default=500)
    ap.add_argument("--n-qubits", type=int, default=6)
    ap.add_argument("--depth", type=int, default=1)
    ap.add_argument("--observables", type=int, default=60)
    ap.add_argument("--strength", type=float, default=1.15)
    ap.add_argument("--noise", type=float, default=0.28)
    ap.add_argument("--keep-mean-signal", action="store_true")
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    rng = np.random.default_rng(args.seed)
    y_train = balanced_labels(args.n_train, args.n_classes, rng)
    y_test = balanced_labels(args.n_test, args.n_classes, rng)
    a_train = highorder_angles(
        y_train,
        n_qubits=args.n_qubits,
        strength=args.strength,
        noise=args.noise,
        seed=args.seed + 11,
    )
    a_test = highorder_angles(
        y_test,
        n_qubits=args.n_qubits,
        strength=args.strength,
        noise=args.noise,
        seed=args.seed + 13,
    )

    specs = make_observable_specs(args.n_qubits, args.observables)
    circuit = build_qnode(n_qubits=args.n_qubits, depth=args.depth, specs=specs, seed=args.seed + 17)
    x_train = compute_readouts(circuit, a_train)
    x_test = compute_readouts(circuit, a_test)
    if not args.keep_mean_signal:
        x_train, x_test = equalize_class_means(x_train, y_train, x_test, y_test)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        out,
        xtr=x_train.astype(np.float32),
        ytr=y_train.astype(np.int64),
        xte=x_test.astype(np.float32),
        yte=y_test.astype(np.int64),
        observable_specs=np.asarray([str(s) for s in specs]),
        backend=np.asarray(["pennylane_highorder_default_qubit"]),
        n_qubits=np.asarray([args.n_qubits]),
        depth=np.asarray([args.depth]),
        mean_equalized=np.asarray([not args.keep_mean_signal]),
    )
    print(f"Wrote {out} train={x_train.shape} test={x_test.shape}")


if __name__ == "__main__":
    main()

