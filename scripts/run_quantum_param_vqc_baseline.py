from __future__ import annotations

import argparse
import csv
import json
import math
import os
import sys
from pathlib import Path
from typing import Any

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
QDEPS = ROOT / ".qdeps"
if QDEPS.exists():
    sys.path.insert(0, str(QDEPS))
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / ".mplcache"))

from qprotohop.data import dirichlet_partition, load_npz_dataset  # noqa: E402


def pca_angles(x_train: np.ndarray, x_test: np.ndarray, *, n_qubits: int) -> tuple[np.ndarray, np.ndarray]:
    mean = x_train.mean(axis=0, keepdims=True)
    xt = x_train - mean
    xv = x_test - mean
    _, _, vt = np.linalg.svd(xt, full_matrices=False)
    proj = vt[:n_qubits].T
    a_train = xt @ proj
    a_test = xv @ proj
    scale = np.percentile(np.abs(a_train), 90, axis=0, keepdims=True) + 1e-8
    a_train = np.clip((np.pi / 2.0) * a_train / scale, -np.pi, np.pi)
    a_test = np.clip((np.pi / 2.0) * a_test / scale, -np.pi, np.pi)
    return a_train.astype(np.float64), a_test.astype(np.float64)


def build_vqc(*, n_qubits: int, n_layers: int, n_classes: int):
    import pennylane as qml

    dev = qml.device("default.qubit", wires=n_qubits, shots=None)

    @qml.qnode(dev, interface="autograd", diff_method="backprop")
    def circuit(angles, weights):
        for q in range(n_qubits):
            qml.RY(angles[q], wires=q)
        for layer in range(n_layers):
            for q in range(n_qubits):
                qml.RY(weights[layer, q, 0], wires=q)
                qml.RZ(weights[layer, q, 1], wires=q)
            for q in range(n_qubits - 1):
                qml.CNOT(wires=[q, q + 1])
            if n_qubits > 2:
                qml.CNOT(wires=[n_qubits - 1, 0])
            for q in range(n_qubits):
                qml.RX(weights[layer, q, 2], wires=q)
        return [qml.expval(qml.PauliZ(q)) for q in range(n_classes)]

    return circuit


def softmax_np(logits: np.ndarray) -> np.ndarray:
    logits = logits - np.max(logits, axis=1, keepdims=True)
    exp = np.exp(logits)
    return exp / (np.sum(exp, axis=1, keepdims=True) + 1e-12)


def accuracy_np(logits: np.ndarray, y: np.ndarray) -> float:
    pred = np.argmax(logits, axis=1)
    return float(np.mean(pred == y))


def balanced_accuracy_np(logits: np.ndarray, y: np.ndarray, n_classes: int) -> float:
    pred = np.argmax(logits, axis=1)
    vals = []
    for c in range(n_classes):
        mask = y == c
        if np.any(mask):
            vals.append(float(np.mean(pred[mask] == y[mask])))
    return float(np.mean(vals)) if vals else 0.0


def predict_logits(circuit, weights: np.ndarray, bias: np.ndarray, x: np.ndarray, *, logit_scale: float) -> np.ndarray:
    rows = []
    for xi in x:
        z = np.asarray(circuit(xi, weights), dtype=np.float64)
        rows.append(logit_scale * z + bias)
    return np.stack(rows, axis=0)


def train_local(
    *,
    circuit,
    init_weights: np.ndarray,
    init_bias: np.ndarray,
    x: np.ndarray,
    y: np.ndarray,
    n_classes: int,
    steps: int,
    batch_size: int,
    lr: float,
    prox_mu: float,
    logit_scale: float,
    seed: int,
) -> tuple[np.ndarray, np.ndarray]:
    import pennylane as qml
    from pennylane import numpy as pnp

    rng = np.random.default_rng(seed)
    weights = pnp.array(init_weights, requires_grad=True)
    bias = pnp.array(init_bias, requires_grad=True)
    ref_w = pnp.array(init_weights, requires_grad=False)
    ref_b = pnp.array(init_bias, requires_grad=False)

    def loss_fn(w, b, xb, yb):
        losses = []
        for i in range(len(yb)):
            z = pnp.stack(circuit(xb[i], w))
            logits = logit_scale * z + b
            m = pnp.max(logits)
            logsum = m + pnp.log(pnp.sum(pnp.exp(logits - m)))
            losses.append(logsum - logits[int(yb[i])])
        loss = pnp.mean(pnp.stack(losses))
        if prox_mu > 0:
            loss = loss + 0.5 * prox_mu * (pnp.sum((w - ref_w) ** 2) + pnp.sum((b - ref_b) ** 2))
        return loss

    grad_fn = qml.grad(loss_fn, argnums=[0, 1])
    for _ in range(steps):
        if len(y) <= batch_size:
            idx = np.arange(len(y))
        else:
            idx = rng.choice(len(y), size=batch_size, replace=False)
        xb = pnp.array(x[idx], requires_grad=False)
        yb = np.asarray(y[idx], dtype=np.int64)
        gw, gb = grad_fn(weights, bias, xb, yb)
        weights = weights - lr * gw
        bias = bias - lr * gb
    return np.asarray(weights, dtype=np.float64), np.asarray(bias, dtype=np.float64)


def train_centralized(
    *,
    circuit,
    weights: np.ndarray,
    bias: np.ndarray,
    x_train: np.ndarray,
    y_train: np.ndarray,
    n_classes: int,
    rounds: int,
    local_steps: int,
    batch_size: int,
    lr: float,
    logit_scale: float,
    seed: int,
) -> tuple[np.ndarray, np.ndarray]:
    steps = max(1, rounds * local_steps)
    return train_local(
        circuit=circuit,
        init_weights=weights,
        init_bias=bias,
        x=x_train,
        y=y_train,
        n_classes=n_classes,
        steps=steps,
        batch_size=batch_size,
        lr=lr,
        prox_mu=0.0,
        logit_scale=logit_scale,
        seed=seed,
    )


def train_federated(
    *,
    method: str,
    circuit,
    init_weights: np.ndarray,
    init_bias: np.ndarray,
    x_train: np.ndarray,
    y_train: np.ndarray,
    client_indices: list[np.ndarray],
    n_classes: int,
    rounds: int,
    participation: float,
    local_steps: int,
    batch_size: int,
    lr: float,
    fedprox_mu: float,
    logit_scale: float,
    seed: int,
) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    weights = init_weights.copy()
    bias = init_bias.copy()
    n_clients = len(client_indices)
    m = max(1, int(round(participation * n_clients)))
    for rnd in range(rounds):
        participants = rng.choice(n_clients, size=m, replace=False)
        local_ws = []
        local_bs = []
        alphas = []
        for cid in participants:
            idx = client_indices[int(cid)]
            if len(idx) == 0:
                continue
            w_i, b_i = train_local(
                circuit=circuit,
                init_weights=weights,
                init_bias=bias,
                x=x_train[idx],
                y=y_train[idx],
                n_classes=n_classes,
                steps=local_steps,
                batch_size=batch_size,
                lr=lr,
                prox_mu=(fedprox_mu if method == "vqc_fedprox" else 0.0),
                logit_scale=logit_scale,
                seed=seed + 1000 * rnd + int(cid),
            )
            local_ws.append(w_i)
            local_bs.append(b_i)
            alphas.append(float(len(idx)))
        if not local_ws:
            continue
        a = np.asarray(alphas, dtype=np.float64)
        a = a / (a.sum() + 1e-12)
        weights = np.sum(np.stack(local_ws, axis=0) * a[:, None, None, None], axis=0)
        bias = np.sum(np.stack(local_bs, axis=0) * a[:, None], axis=0)
    return weights, bias


def summarize_method(
    *,
    method: str,
    circuit,
    weights: np.ndarray,
    bias: np.ndarray,
    x_test: np.ndarray,
    y_test: np.ndarray,
    n_classes: int,
    rounds: int,
    clients: int,
    participation: float,
    logit_scale: float,
) -> dict[str, Any]:
    logits = predict_logits(circuit, weights, bias, x_test, logit_scale=logit_scale)
    param_scalars = int(np.prod(weights.shape) + np.prod(bias.shape))
    payload = 8 * param_scalars
    return {
        "method": method,
        "final_acc": accuracy_np(logits, y_test),
        "final_balanced_acc": balanced_accuracy_np(logits, y_test, n_classes),
        "bytes_per_client_round": payload,
        "total_upload_bytes": float(payload * rounds * max(1, int(round(clients * participation)))),
        "param_scalars": param_scalars,
    }


def run_seed(args: argparse.Namespace, seed: int) -> dict[str, Any]:
    dataset = load_npz_dataset(
        args.source,
        n_train=args.n_train,
        n_test=args.n_test,
        n_classes=args.n_classes,
        test_fraction=0.25,
        seed=seed,
    )
    x_train, x_test = pca_angles(dataset.x_train, dataset.x_test, n_qubits=args.n_qubits)
    client_indices = dirichlet_partition(
        dataset.y_train,
        n_clients=args.clients,
        alpha=args.dirichlet_alpha,
        seed=seed + 31,
        min_size=max(2, args.batch_size // 2),
    )
    if args.n_classes > args.n_qubits:
        raise ValueError("This compact VQC baseline uses one Pauli-Z logit per class; set n_qubits >= n_classes.")
    circuit = build_vqc(n_qubits=args.n_qubits, n_layers=args.layers, n_classes=args.n_classes)
    rng = np.random.default_rng(seed + 17)
    init_weights = rng.normal(0.0, args.init_scale, size=(args.layers, args.n_qubits, 3))
    init_bias = np.zeros((args.n_classes,), dtype=np.float64)

    summaries = []
    for method in args.methods.split(","):
        method = method.strip()
        if not method:
            continue
        if method == "vqc_centralized":
            weights, bias = train_centralized(
                circuit=circuit,
                weights=init_weights,
                bias=init_bias,
                x_train=x_train,
                y_train=dataset.y_train,
                n_classes=args.n_classes,
                rounds=args.rounds,
                local_steps=args.local_steps,
                batch_size=args.batch_size,
                lr=args.lr,
                logit_scale=args.logit_scale,
                seed=seed + 71,
            )
        elif method in {"vqc_fedavg", "vqc_fedprox"}:
            weights, bias = train_federated(
                method=method,
                circuit=circuit,
                init_weights=init_weights,
                init_bias=init_bias,
                x_train=x_train,
                y_train=dataset.y_train,
                client_indices=client_indices,
                n_classes=args.n_classes,
                rounds=args.rounds,
                participation=args.participation,
                local_steps=args.local_steps,
                batch_size=args.batch_size,
                lr=args.lr,
                fedprox_mu=args.fedprox_mu,
                logit_scale=args.logit_scale,
                seed=seed + 101,
            )
        elif method == "vqc_init":
            weights, bias = init_weights, init_bias
        else:
            raise ValueError(f"Unknown method {method}")
        summaries.append(
            summarize_method(
                method=method,
                circuit=circuit,
                weights=weights,
                bias=bias,
                x_test=x_test,
                y_test=dataset.y_test,
                n_classes=args.n_classes,
                rounds=args.rounds,
                clients=args.clients,
                participation=args.participation,
                logit_scale=args.logit_scale,
            )
        )
    return {
        "seed": seed,
        "dataset": {
            "source": args.source,
            "n_train": int(len(dataset.y_train)),
            "n_test": int(len(dataset.y_test)),
            "n_classes": int(args.n_classes),
            "n_qubits": int(args.n_qubits),
            "layers": int(args.layers),
        },
        "summaries": summaries,
    }


def mean_ci95(xs: list[float]) -> tuple[float, float]:
    if not xs:
        return 0.0, 0.0
    if len(xs) == 1:
        return float(xs[0]), 0.0
    tcrit = {1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776}.get(len(xs) - 1, 1.96)
    return float(np.mean(xs)), float(tcrit * np.std(xs, ddof=1) / math.sqrt(len(xs)))


def write_reports(out_dir: Path, seed_results: list[dict[str, Any]]) -> None:
    rows: list[dict[str, Any]] = []
    for res in seed_results:
        for s in res["summaries"]:
            rows.append({"seed": res["seed"], **s})
    csv_path = out_dir / "quantum_param_vqc_baseline.csv"
    fields = [
        "seed",
        "method",
        "final_acc",
        "final_balanced_acc",
        "bytes_per_client_round",
        "total_upload_bytes",
        "param_scalars",
    ]
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    methods = sorted({str(r["method"]) for r in rows})
    md_lines = [
        "# Quantum-Parameter VQC Federated Baseline",
        "",
        "This is a standard trainable PennyLane VQC baseline with shared ansatz and canonical Pauli-Z class readout. It is included as a parameter-aggregation reference; unlike QProto, it assumes homogeneous model/readout semantics.",
        "",
        "| Method | n | Acc. | 95% CI | Bal. acc. | Bytes/client/round | Params |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for method in methods:
        vals = [r for r in rows if r["method"] == method]
        acc_mean, acc_ci = mean_ci95([float(v["final_acc"]) for v in vals])
        bal_mean, _ = mean_ci95([float(v["final_balanced_acc"]) for v in vals])
        bytes_mean = float(np.mean([float(v["bytes_per_client_round"]) for v in vals]))
        params_mean = float(np.mean([float(v["param_scalars"]) for v in vals]))
        md_lines.append(
            f"| {method} | {len(vals)} | {acc_mean:.4f} | {acc_ci:.4f} | {bal_mean:.4f} | {bytes_mean:.0f} | {params_mean:.0f} |"
        )
    (out_dir / "quantum_param_vqc_baseline.md").write_text("\n".join(md_lines), encoding="utf-8")

    tex_lines = [
        "\\begin{table}[t]",
        "\\centering",
        "\\caption{Trainable PennyLane VQC parameter-aggregation baseline. This baseline uses a shared ansatz and canonical readout, so it tests standard quantum-parameter FL rather than heterogeneous-readout prototype aggregation.}",
        "\\label{tab:quantum-param-vqc}",
        "\\begin{tabular}{lrrrr}",
        "\\toprule",
        "Method & Acc. & 95\\% CI & Bal. acc. & Bytes \\\\",
        "\\midrule",
    ]
    labels = {
        "vqc_init": "VQC init",
        "vqc_fedavg": "VQC FedAvg",
        "vqc_fedprox": "VQC FedProx",
        "vqc_centralized": "VQC centralized",
    }
    for method in ["vqc_init", "vqc_fedavg", "vqc_fedprox", "vqc_centralized"]:
        vals = [r for r in rows if r["method"] == method]
        if not vals:
            continue
        acc_mean, acc_ci = mean_ci95([float(v["final_acc"]) for v in vals])
        bal_mean, _ = mean_ci95([float(v["final_balanced_acc"]) for v in vals])
        bytes_mean = float(np.mean([float(v["bytes_per_client_round"]) for v in vals]))
        tex_lines.append(
            f"{labels.get(method, method)} & {acc_mean:.3f} & {acc_ci:.3f} & {bal_mean:.3f} & {bytes_mean:.0f} \\\\"
        )
    tex_lines.extend(["\\bottomrule", "\\end{tabular}", "\\end{table}", ""])
    (out_dir / "table_quantum_param_vqc.tex").write_text("\n".join(tex_lines), encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser("Run a small trainable PennyLane VQC parameter-FL baseline")
    ap.add_argument("--source", type=str, default="data/mnist.npz")
    ap.add_argument("--out", type=str, default="runs/quantum_param_vqc_baseline")
    ap.add_argument("--seeds", type=str, default="0,1,2")
    ap.add_argument("--methods", type=str, default="vqc_init,vqc_fedavg,vqc_fedprox,vqc_centralized")
    ap.add_argument("--n-classes", type=int, default=4)
    ap.add_argument("--n-train", type=int, default=360)
    ap.add_argument("--n-test", type=int, default=240)
    ap.add_argument("--n-qubits", type=int, default=4)
    ap.add_argument("--layers", type=int, default=1)
    ap.add_argument("--clients", type=int, default=12)
    ap.add_argument("--dirichlet-alpha", type=float, default=0.5)
    ap.add_argument("--participation", type=float, default=0.75)
    ap.add_argument("--rounds", type=int, default=8)
    ap.add_argument("--local-steps", type=int, default=5)
    ap.add_argument("--batch-size", type=int, default=16)
    ap.add_argument("--lr", type=float, default=0.08)
    ap.add_argument("--fedprox-mu", type=float, default=0.02)
    ap.add_argument("--logit-scale", type=float, default=2.0)
    ap.add_argument("--init-scale", type=float, default=0.08)
    ap.add_argument("--reuse-existing", action="store_true")
    args = ap.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    seeds = [int(s.strip()) for s in args.seeds.split(",") if s.strip()]
    results = []
    for seed in seeds:
        seed_path = out_dir / f"seed{seed}.json"
        if args.reuse_existing and seed_path.exists():
            print(f"seed {seed} (reuse)", flush=True)
            results.append(json.loads(seed_path.read_text(encoding="utf-8")))
            continue
        print(f"seed {seed}", flush=True)
        result = run_seed(args, seed)
        results.append(result)
        seed_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
        for s in result["summaries"]:
            print(
                f"  {s['method']:>16} acc={s['final_acc']:.4f} bal={s['final_balanced_acc']:.4f} bytes={s['bytes_per_client_round']}",
                flush=True,
            )
    (out_dir / "metrics.json").write_text(json.dumps({"seeds": results}, indent=2), encoding="utf-8")
    write_reports(out_dir, results)
    print(f"Wrote {out_dir}")


if __name__ == "__main__":
    main()

