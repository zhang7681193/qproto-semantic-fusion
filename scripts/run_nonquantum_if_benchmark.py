from __future__ import annotations

import argparse
import csv
import math
import statistics as st
import time
from dataclasses import dataclass
from pathlib import Path

import numpy as np

try:
    import torch
    from torch import nn
except Exception:  # pragma: no cover - optional strong baselines
    torch = None
    nn = None


T_CRIT_95 = {1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571}


@dataclass(frozen=True)
class SensorSchema:
    client_id: int
    coords: np.ndarray


@dataclass
class BenchmarkData:
    x_train: np.ndarray
    y_train: np.ndarray
    x_test: np.ndarray
    y_test: np.ndarray
    anchor: np.ndarray
    schemas: list[SensorSchema]
    client_indices: list[np.ndarray]
    high_order_pairs: list[tuple[int, int]]
    view_dim: int
    n_views: int
    n_classes: int
    groups: list[np.ndarray]


def balanced_labels(n: int, n_classes: int, rng: np.random.Generator) -> np.ndarray:
    y = np.arange(n, dtype=np.int64) % n_classes
    rng.shuffle(y)
    return y


def generate_sensor_features(
    *,
    n: int,
    y: np.ndarray,
    n_views: int,
    view_dim: int,
    n_classes: int,
    seed: int,
    return_pairs: bool = False,
) -> tuple[np.ndarray, list[tuple[int, int]]]:
    rng = np.random.default_rng(seed)
    d = n_views * view_dim
    x = rng.normal(0.0, 0.55, size=(n, d))

    high_order_pairs: list[tuple[int, int]] = []
    weak_means = np.zeros((n_classes, d), dtype=np.float64)
    for c in range(n_classes):
        # Keep the common first view weak, and place class-specific evidence in
        # non-shared views so that shared-view fusion is a real boundary case.
        mean_view = 1 + ((2 * c + 3) % (n_views - 1))
        dims = mean_view * view_dim + np.array([c % view_dim, (c + 3) % view_dim])
        weak_means[c, dims] = 0.12 * np.array([1.0, -1.0 if c % 2 else 1.0])

        pair_view_a = 1 + ((3 * c + 1) % (n_views - 1))
        pair_view_b = 1 + ((5 * c + 4) % (n_views - 1))
        a = pair_view_a * view_dim + ((c + 1) % view_dim)
        b = pair_view_b * view_dim + ((2 * c + 5) % view_dim)
        if a == b:
            pair_view_b = 1 + (pair_view_b % (n_views - 1))
            b = pair_view_b * view_dim + ((2 * c + 6) % view_dim)
        high_order_pairs.append((a, b))

    for c in range(n_classes):
        m = np.where(y == c)[0]
        if len(m) == 0:
            continue
        x[m] += weak_means[c]
        # Covariance signal: zero-mean latent factors change source
        # interactions while keeping first-order means intentionally weak.
        for j, (a, b) in enumerate(high_order_pairs):
            h = rng.normal(0.0, 1.0, size=len(m))
            amp = 1.55 if j == c else 0.05
            sign = 1.0 if (c + j) % 2 == 0 else -1.0
            x[m, a] += amp * h
            x[m, b] += amp * sign * h

    # Add a weak common calibration view that is correlated with class but not
    # strong enough to make shared-observable fusion solve the task.
    for c in range(n_classes):
        m = y == c
        common_coord = c % view_dim
        x[m, common_coord] += 0.05 * (c - (n_classes - 1) / 2.0)

    x = np.tanh(x / 2.2)
    return x.astype(np.float64), (high_order_pairs if return_pairs else [])


def make_schemas(
    *,
    n_clients: int,
    n_views: int,
    view_dim: int,
    views_per_client: int,
    common_views: int,
    seed: int,
) -> list[SensorSchema]:
    rng = np.random.default_rng(seed)
    common = list(range(common_views))
    private_views = np.arange(common_views, n_views, dtype=np.int64)
    schemas = []
    for cid in range(n_clients):
        need = views_per_client - len(common)
        extra = rng.choice(private_views, size=need, replace=False)
        views = np.array(common + extra.tolist(), dtype=np.int64)
        coords = np.concatenate([np.arange(v * view_dim, (v + 1) * view_dim) for v in views])
        rng.shuffle(coords)
        schemas.append(SensorSchema(client_id=cid, coords=coords.astype(np.int64)))
    return schemas


def make_group_schemas(
    *,
    groups: list[np.ndarray],
    n_clients: int,
    views_per_client: int,
    common_views: int,
    seed: int,
) -> list[SensorSchema]:
    rng = np.random.default_rng(seed)
    common = list(range(common_views))
    private = np.arange(common_views, len(groups), dtype=np.int64)
    schemas = []
    for cid in range(n_clients):
        need = max(0, views_per_client - len(common))
        extra = rng.choice(private, size=min(need, len(private)), replace=False)
        chosen = np.array(common + extra.tolist(), dtype=np.int64)
        coords = np.concatenate([groups[int(v)] for v in chosen])
        rng.shuffle(coords)
        schemas.append(SensorSchema(client_id=cid, coords=coords.astype(np.int64)))
    return schemas


def dirichlet_partition(y: np.ndarray, n_clients: int, alpha: float, seed: int) -> list[np.ndarray]:
    rng = np.random.default_rng(seed)
    n_classes = int(y.max()) + 1
    buckets = [np.where(y == c)[0] for c in range(n_classes)]
    for b in buckets:
        rng.shuffle(b)
    parts = [[] for _ in range(n_clients)]
    for c, idxs in enumerate(buckets):
        props = rng.dirichlet(np.full(n_clients, alpha))
        counts = np.floor(props * len(idxs)).astype(int)
        while counts.sum() < len(idxs):
            counts[int(rng.integers(0, n_clients))] += 1
        start = 0
        for cid, cnt in enumerate(counts):
            if cnt > 0:
                parts[cid].extend(idxs[start : start + cnt].tolist())
            start += cnt
    out = []
    for cid, p in enumerate(parts):
        arr = np.array(p, dtype=np.int64)
        rng.shuffle(arr)
        out.append(arr)
    return out


def make_benchmark(args: argparse.Namespace, seed: int) -> BenchmarkData:
    if args.dataset == "uci_har":
        return make_uci_har_benchmark(args, seed)
    if args.dataset == "wdbc":
        return make_wdbc_benchmark(args, seed)
    if args.dataset == "gas_drift":
        return make_gas_drift_benchmark(args, seed)
    if args.dataset == "hydraulic":
        return make_hydraulic_benchmark(args, seed)
    if args.dataset == "mhealth":
        return make_mhealth_benchmark(args, seed)
    if args.dataset == "pamap2":
        return make_pamap2_benchmark(args, seed)
    if args.dataset == "mfeat":
        return make_mfeat_benchmark(args, seed)
    if args.dataset == "mfeat_interaction":
        return make_mfeat_interaction_benchmark(args, seed)

    rng = np.random.default_rng(seed)
    y_train = balanced_labels(args.n_train, args.n_classes, rng)
    y_test = balanced_labels(args.n_test, args.n_classes, rng)
    y_anchor = balanced_labels(args.anchor_size, args.n_classes, rng)
    x_train, pairs = generate_sensor_features(
        n=args.n_train,
        y=y_train,
        n_views=args.n_views,
        view_dim=args.view_dim,
        n_classes=args.n_classes,
        seed=seed + 11,
        return_pairs=True,
    )
    x_test, _ = generate_sensor_features(
        n=args.n_test,
        y=y_test,
        n_views=args.n_views,
        view_dim=args.view_dim,
        n_classes=args.n_classes,
        seed=seed + 17,
    )
    anchor, _ = generate_sensor_features(
        n=args.anchor_size,
        y=y_anchor,
        n_views=args.n_views,
        view_dim=args.view_dim,
        n_classes=args.n_classes,
        seed=seed + 23,
    )
    mean = x_train.mean(axis=0)
    std = x_train.std(axis=0) + 1e-6
    x_train = np.clip((x_train - mean) / (2.5 * std), -1.0, 1.0)
    x_test = np.clip((x_test - mean) / (2.5 * std), -1.0, 1.0)
    anchor = np.clip((anchor - mean) / (2.5 * std), -1.0, 1.0)
    schemas = make_schemas(
        n_clients=args.clients,
        n_views=args.n_views,
        view_dim=args.view_dim,
        views_per_client=args.views_per_client,
        common_views=args.common_views,
        seed=seed + 31,
    )
    parts = dirichlet_partition(y_train, args.clients, args.dirichlet_alpha, seed + 37)
    groups = [np.arange(v * args.view_dim, (v + 1) * args.view_dim, dtype=np.int64) for v in range(args.n_views)]
    return BenchmarkData(
        x_train=x_train,
        y_train=y_train,
        x_test=x_test,
        y_test=y_test,
        anchor=anchor,
        schemas=schemas,
        client_indices=parts,
        high_order_pairs=pairs,
        view_dim=args.view_dim,
        n_views=args.n_views,
        n_classes=args.n_classes,
        groups=groups,
    )


def load_uci_har(root: Path) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, list[np.ndarray]]:
    base = root / "UCI HAR Dataset"
    x_train = np.loadtxt(base / "train" / "X_train.txt", dtype=np.float64)
    y_train = np.loadtxt(base / "train" / "y_train.txt", dtype=np.int64) - 1
    x_test = np.loadtxt(base / "test" / "X_test.txt", dtype=np.float64)
    y_test = np.loadtxt(base / "test" / "y_test.txt", dtype=np.int64) - 1
    feature_lines = (base / "features.txt").read_text(encoding="utf-8").splitlines()
    group_map: dict[str, list[int]] = {}
    for line in feature_lines:
        idx_text, name = line.split(maxsplit=1)
        prefix = name.split("-", 1)[0]
        group_map.setdefault(prefix, []).append(int(idx_text) - 1)
    groups = [np.array(v, dtype=np.int64) for _, v in sorted(group_map.items(), key=lambda kv: kv[0])]
    return x_train, y_train, x_test, y_test, groups


def make_uci_har_benchmark(args: argparse.Namespace, seed: int) -> BenchmarkData:
    rng = np.random.default_rng(seed)
    x_train, y_train, x_test, y_test, groups = load_uci_har(Path(args.uci_har_root))
    if args.n_train > 0 and args.n_train < len(x_train):
        idx = rng.choice(len(x_train), size=args.n_train, replace=False)
        x_train, y_train = x_train[idx], y_train[idx]
    if args.n_test > 0 and args.n_test < len(x_test):
        idx = rng.choice(len(x_test), size=args.n_test, replace=False)
        x_test, y_test = x_test[idx], y_test[idx]
    x_train = np.clip(x_train, -1.0, 1.0)
    x_test = np.clip(x_test, -1.0, 1.0)
    anchor_idx = rng.choice(len(x_train), size=min(args.anchor_size, len(x_train)), replace=False)
    anchor = x_train[anchor_idx].copy()
    schemas = make_group_schemas(
        groups=groups,
        n_clients=args.clients,
        views_per_client=args.views_per_client,
        common_views=args.common_views,
        seed=seed + 31,
    )
    parts = dirichlet_partition(y_train, args.clients, args.dirichlet_alpha, seed + 37)
    return BenchmarkData(
        x_train=x_train,
        y_train=y_train,
        x_test=x_test,
        y_test=y_test,
        anchor=anchor,
        schemas=schemas,
        client_indices=parts,
        high_order_pairs=[],
        view_dim=0,
        n_views=len(groups),
        n_classes=int(max(y_train.max(), y_test.max())) + 1,
        groups=groups,
    )


def load_wdbc(path: Path) -> tuple[np.ndarray, np.ndarray, list[np.ndarray]]:
    rows = []
    labels = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        parts = line.split(",")
        labels.append(1 if parts[1] == "M" else 0)
        rows.append([float(x) for x in parts[2:]])
    x = np.asarray(rows, dtype=np.float64)
    y = np.asarray(labels, dtype=np.int64)
    # WDBC has ten measurement families, each observed through mean, standard
    # error, and worst-value statistics. Treat each family as a semantic view.
    groups = [np.array([j, 10 + j, 20 + j], dtype=np.int64) for j in range(10)]
    return x, y, groups


def stratified_split(y: np.ndarray, train_fraction: float, seed: int) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    train = []
    test = []
    for c in sorted(set(y.tolist())):
        idx = np.where(y == c)[0]
        rng.shuffle(idx)
        n_train = max(1, int(round(len(idx) * train_fraction)))
        train.extend(idx[:n_train].tolist())
        test.extend(idx[n_train:].tolist())
    train = np.asarray(train, dtype=np.int64)
    test = np.asarray(test, dtype=np.int64)
    rng.shuffle(train)
    rng.shuffle(test)
    return train, test


def make_wdbc_benchmark(args: argparse.Namespace, seed: int) -> BenchmarkData:
    rng = np.random.default_rng(seed)
    x, y, groups = load_wdbc(Path(args.wdbc_path))
    train_idx, test_idx = stratified_split(y, train_fraction=0.7, seed=seed + 19)
    x_train, y_train = x[train_idx], y[train_idx]
    x_test, y_test = x[test_idx], y[test_idx]
    mean = x_train.mean(axis=0)
    std = x_train.std(axis=0) + 1e-6
    x_train = np.clip((x_train - mean) / (3.0 * std), -1.0, 1.0)
    x_test = np.clip((x_test - mean) / (3.0 * std), -1.0, 1.0)
    anchor_idx = rng.choice(len(x_train), size=min(args.anchor_size, len(x_train)), replace=False)
    anchor = x_train[anchor_idx].copy()
    schemas = make_group_schemas(
        groups=groups,
        n_clients=args.clients,
        views_per_client=args.views_per_client,
        common_views=args.common_views,
        seed=seed + 31,
    )
    parts = dirichlet_partition(y_train, args.clients, args.dirichlet_alpha, seed + 37)
    return BenchmarkData(
        x_train=x_train,
        y_train=y_train,
        x_test=x_test,
        y_test=y_test,
        anchor=anchor,
        schemas=schemas,
        client_indices=parts,
        high_order_pairs=[],
        view_dim=0,
        n_views=len(groups),
        n_classes=2,
        groups=groups,
    )


def load_gas_drift(root: Path) -> tuple[np.ndarray, np.ndarray, np.ndarray, list[np.ndarray]]:
    rows = []
    labels = []
    batches = []
    dataset_dir = root / "Dataset"
    paths = sorted(dataset_dir.glob("batch*.dat"), key=lambda p: int(p.stem.replace("batch", "")))
    if not paths:
        raise FileNotFoundError(f"Could not find Gas Drift batch*.dat files under {dataset_dir}")
    for path in paths:
        batch = int(path.stem.replace("batch", ""))
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            parts = line.split()
            labels.append(int(parts[0]) - 1)
            x = np.zeros(128, dtype=np.float64)
            for token in parts[1:]:
                k, v = token.split(":", 1)
                x[int(k) - 1] = float(v)
            rows.append(x)
            batches.append(batch)
    x = np.asarray(rows, dtype=np.float64)
    # Signed log compression keeps the large steady-state features and the
    # smaller dynamic features on comparable numeric scales before z-scoring.
    x = np.sign(x) * np.log1p(np.abs(x))
    y = np.asarray(labels, dtype=np.int64)
    batch_arr = np.asarray(batches, dtype=np.int64)
    groups = [np.arange(8 * j, 8 * (j + 1), dtype=np.int64) for j in range(16)]
    return x, y, batch_arr, groups


def stratified_subsample(y: np.ndarray, max_n: int, seed: int) -> np.ndarray:
    if max_n <= 0 or max_n >= len(y):
        return np.arange(len(y), dtype=np.int64)
    rng = np.random.default_rng(seed)
    classes = sorted(set(y.tolist()))
    per_class = max(1, max_n // len(classes))
    chosen = []
    for c in classes:
        idx = np.where(y == c)[0]
        rng.shuffle(idx)
        chosen.extend(idx[: min(per_class, len(idx))].tolist())
    remaining = max_n - len(chosen)
    if remaining > 0:
        pool = np.setdiff1d(np.arange(len(y), dtype=np.int64), np.asarray(chosen, dtype=np.int64), assume_unique=False)
        if len(pool) > 0:
            extra = rng.choice(pool, size=min(remaining, len(pool)), replace=False)
            chosen.extend(extra.tolist())
    out = np.asarray(chosen, dtype=np.int64)
    rng.shuffle(out)
    return out


def make_gas_drift_benchmark(args: argparse.Namespace, seed: int) -> BenchmarkData:
    rng = np.random.default_rng(seed)
    x, y, batches, groups = load_gas_drift(Path(args.gas_drift_root))
    if args.gas_split == "temporal":
        train_idx = np.where(batches <= 6)[0]
        test_idx = np.where(batches >= 7)[0]
    else:
        train_idx, test_idx = stratified_split(y, train_fraction=0.7, seed=seed + 19)
    if args.n_train > 0 and args.n_train < len(train_idx):
        rel = stratified_subsample(y[train_idx], args.n_train, seed + 23)
        train_idx = train_idx[rel]
    if args.n_test > 0 and args.n_test < len(test_idx):
        rel = stratified_subsample(y[test_idx], args.n_test, seed + 29)
        test_idx = test_idx[rel]
    x_train, y_train = x[train_idx], y[train_idx]
    x_test, y_test = x[test_idx], y[test_idx]
    mean = x_train.mean(axis=0)
    std = x_train.std(axis=0) + 1e-6
    x_train = np.clip((x_train - mean) / (3.0 * std), -1.0, 1.0)
    x_test = np.clip((x_test - mean) / (3.0 * std), -1.0, 1.0)
    anchor_idx = rng.choice(len(x_train), size=min(args.anchor_size, len(x_train)), replace=False)
    anchor = x_train[anchor_idx].copy()
    schemas = make_group_schemas(
        groups=groups,
        n_clients=args.clients,
        views_per_client=args.views_per_client,
        common_views=args.common_views,
        seed=seed + 31,
    )
    parts = dirichlet_partition(y_train, args.clients, args.dirichlet_alpha, seed + 37)
    pairs = choose_cross_group_pairs(anchor, groups, n_pairs=8)
    return BenchmarkData(
        x_train=x_train,
        y_train=y_train,
        x_test=x_test,
        y_test=y_test,
        anchor=anchor,
        schemas=schemas,
        client_indices=parts,
        high_order_pairs=pairs,
        view_dim=8,
        n_views=len(groups),
        n_classes=int(max(y_train.max(), y_test.max())) + 1,
        groups=groups,
    )


HYDRAULIC_SENSORS = [
    "PS1",
    "PS2",
    "PS3",
    "PS4",
    "PS5",
    "PS6",
    "EPS1",
    "FS1",
    "FS2",
    "TS1",
    "TS2",
    "TS3",
    "TS4",
    "VS1",
    "CE",
    "CP",
    "SE",
]


HYDRAULIC_TARGETS = {
    "cooler": 0,
    "valve": 1,
    "pump": 2,
    "accumulator": 3,
    "stable": 4,
}


def summarize_cycle_matrix(x: np.ndarray) -> np.ndarray:
    if x.ndim == 1:
        x = x[:, None]
    n_steps = x.shape[1]
    first = max(1, n_steps // 10)
    last = max(1, n_steps // 10)
    t = np.linspace(-1.0, 1.0, n_steps, dtype=np.float64)
    centered_t = t - t.mean()
    denom = float(np.dot(centered_t, centered_t)) + 1e-12
    mean = x.mean(axis=1)
    centered_x = x - mean[:, None]
    slope = centered_x @ centered_t / denom
    features = np.column_stack(
        [
            mean,
            x.std(axis=1),
            x.min(axis=1),
            x.max(axis=1),
            np.quantile(x, 0.10, axis=1),
            np.quantile(x, 0.90, axis=1),
            x[:, :first].mean(axis=1),
            x[:, -last:].mean(axis=1),
            np.sqrt(np.mean(x * x, axis=1)),
            slope,
        ]
    )
    return features.astype(np.float64)


def load_hydraulic(root: Path, target: str) -> tuple[np.ndarray, np.ndarray, list[np.ndarray]]:
    if target not in HYDRAULIC_TARGETS:
        raise ValueError(f"Unknown hydraulic target {target!r}; expected one of {sorted(HYDRAULIC_TARGETS)}")
    profile_path = root / "profile.txt"
    if not profile_path.exists():
        raise FileNotFoundError(f"Could not find profile.txt under {root}")
    profile = np.loadtxt(profile_path, dtype=np.float64)
    y_raw = profile[:, HYDRAULIC_TARGETS[target]].astype(np.int64)
    classes = {v: i for i, v in enumerate(sorted(set(y_raw.tolist())))}
    y = np.asarray([classes[int(v)] for v in y_raw], dtype=np.int64)

    views = []
    groups = []
    offset = 0
    for sensor in HYDRAULIC_SENSORS:
        path = root / f"{sensor}.txt"
        if not path.exists():
            raise FileNotFoundError(f"Could not find hydraulic sensor file {path}")
        raw = np.loadtxt(path, dtype=np.float64)
        feats = summarize_cycle_matrix(raw)
        views.append(feats)
        groups.append(np.arange(offset, offset + feats.shape[1], dtype=np.int64))
        offset += feats.shape[1]
    x = np.concatenate(views, axis=1)
    if len(x) != len(y):
        raise ValueError(f"Hydraulic feature rows ({len(x)}) do not match profile rows ({len(y)})")
    return x, y, groups


def make_hydraulic_benchmark(args: argparse.Namespace, seed: int) -> BenchmarkData:
    rng = np.random.default_rng(seed)
    x, y, groups = load_hydraulic(Path(args.hydraulic_root), args.hydraulic_target)
    train_idx, test_idx = stratified_split(y, train_fraction=0.7, seed=seed + 19)
    if args.n_train > 0 and args.n_train < len(train_idx):
        rel = stratified_subsample(y[train_idx], args.n_train, seed + 23)
        train_idx = train_idx[rel]
    if args.n_test > 0 and args.n_test < len(test_idx):
        rel = stratified_subsample(y[test_idx], args.n_test, seed + 29)
        test_idx = test_idx[rel]
    x_train, y_train = x[train_idx], y[train_idx]
    x_test, y_test = x[test_idx], y[test_idx]
    mean = x_train.mean(axis=0)
    std = x_train.std(axis=0) + 1e-6
    x_train = np.clip((x_train - mean) / (3.0 * std), -1.0, 1.0)
    x_test = np.clip((x_test - mean) / (3.0 * std), -1.0, 1.0)
    anchor_idx = rng.choice(len(x_train), size=min(args.anchor_size, len(x_train)), replace=False)
    anchor = x_train[anchor_idx].copy()
    schemas = make_group_schemas(
        groups=groups,
        n_clients=args.clients,
        views_per_client=args.views_per_client,
        common_views=args.common_views,
        seed=seed + 31,
    )
    parts = dirichlet_partition(y_train, args.clients, args.dirichlet_alpha, seed + 37)
    pairs = choose_cross_group_pairs(anchor, groups, n_pairs=12)
    return BenchmarkData(
        x_train=x_train,
        y_train=y_train,
        x_test=x_test,
        y_test=y_test,
        anchor=anchor,
        schemas=schemas,
        client_indices=parts,
        high_order_pairs=pairs,
        view_dim=10,
        n_views=len(groups),
        n_classes=int(max(y_train.max(), y_test.max())) + 1,
        groups=groups,
    )


MHEALTH_GROUPS = [
    ("chest_accel", [0, 1, 2]),
    ("chest_ecg", [3, 4]),
    ("ankle_accel", [5, 6, 7]),
    ("ankle_gyro", [8, 9, 10]),
    ("ankle_mag", [11, 12, 13]),
    ("arm_accel", [14, 15, 16]),
    ("arm_gyro", [17, 18, 19]),
    ("arm_mag", [20, 21, 22]),
]


def featurize_mhealth_window(window: np.ndarray) -> tuple[np.ndarray, list[np.ndarray]]:
    feats = []
    groups = []
    offset = 0
    for _, cols in MHEALTH_GROUPS:
        group_feat = summarize_cycle_matrix(window[:, cols].T).reshape(-1)
        feats.append(group_feat)
        groups.append(np.arange(offset, offset + len(group_feat), dtype=np.int64))
        offset += len(group_feat)
    return np.concatenate(feats).astype(np.float64), groups


def load_mhealth(
    root: Path,
    *,
    window: int,
    stride: int,
    max_windows_per_subject: int,
    seed: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, list[np.ndarray]]:
    base = root / "MHEALTHDATASET"
    if not base.exists():
        base = root
    files = sorted(base.glob("mHealth_subject*.log"), key=lambda p: int(p.stem.replace("mHealth_subject", "")))
    if not files:
        raise FileNotFoundError(f"Could not find mHealth_subject*.log files under {base}")
    rng = np.random.default_rng(seed)
    rows = []
    labels = []
    subjects = []
    groups: list[np.ndarray] | None = None
    for path in files:
        subject = int(path.stem.replace("mHealth_subject", ""))
        raw = np.loadtxt(path, dtype=np.float64)
        x_raw = np.nan_to_num(raw[:, :23], nan=0.0, posinf=0.0, neginf=0.0)
        y_raw = raw[:, 23].astype(np.int64)
        candidate: list[tuple[np.ndarray, int]] = []
        start = 0
        while start < len(y_raw):
            label = int(y_raw[start])
            end = start + 1
            while end < len(y_raw) and int(y_raw[end]) == label:
                end += 1
            if label > 0 and end - start >= window:
                for s in range(start, end - window + 1, stride):
                    candidate.append((x_raw[s : s + window], label - 1))
            start = end
        if max_windows_per_subject > 0 and len(candidate) > max_windows_per_subject:
            chosen = rng.choice(len(candidate), size=max_windows_per_subject, replace=False)
            candidate = [candidate[int(i)] for i in chosen]
        for win, label in candidate:
            feat, maybe_groups = featurize_mhealth_window(win)
            groups = maybe_groups
            rows.append(feat)
            labels.append(label)
            subjects.append(subject)
    if not rows or groups is None:
        raise ValueError("MHEALTH loader produced no windows; reduce --mhealth-window or check the dataset path")
    x = np.vstack(rows).astype(np.float64)
    y = np.asarray(labels, dtype=np.int64)
    subject_arr = np.asarray(subjects, dtype=np.int64)
    return x, y, subject_arr, groups


def make_mhealth_benchmark(args: argparse.Namespace, seed: int) -> BenchmarkData:
    rng = np.random.default_rng(seed)
    x, y, subjects, groups = load_mhealth(
        Path(args.mhealth_root),
        window=args.mhealth_window,
        stride=args.mhealth_stride,
        max_windows_per_subject=args.mhealth_max_windows_per_subject,
        seed=seed + 13,
    )
    if args.mhealth_split == "subject":
        subject_ids = np.array(sorted(set(subjects.tolist())), dtype=np.int64)
        rng.shuffle(subject_ids)
        n_test_subjects = max(2, int(round(0.3 * len(subject_ids))))
        test_subjects = set(subject_ids[:n_test_subjects].tolist())
        train_idx = np.where([int(s) not in test_subjects for s in subjects])[0]
        test_idx = np.where([int(s) in test_subjects for s in subjects])[0]
    else:
        train_idx, test_idx = stratified_split(y, train_fraction=0.7, seed=seed + 19)
    if args.n_train > 0 and args.n_train < len(train_idx):
        rel = stratified_subsample(y[train_idx], args.n_train, seed + 23)
        train_idx = train_idx[rel]
    if args.n_test > 0 and args.n_test < len(test_idx):
        rel = stratified_subsample(y[test_idx], args.n_test, seed + 29)
        test_idx = test_idx[rel]
    x_train, y_train = x[train_idx], y[train_idx]
    x_test, y_test = x[test_idx], y[test_idx]
    mean = x_train.mean(axis=0)
    std = x_train.std(axis=0) + 1e-6
    x_train = np.clip((x_train - mean) / (3.0 * std), -1.0, 1.0)
    x_test = np.clip((x_test - mean) / (3.0 * std), -1.0, 1.0)
    anchor_idx = rng.choice(len(x_train), size=min(args.anchor_size, len(x_train)), replace=False)
    anchor = x_train[anchor_idx].copy()
    schemas = make_group_schemas(
        groups=groups,
        n_clients=args.clients,
        views_per_client=args.views_per_client,
        common_views=args.common_views,
        seed=seed + 31,
    )
    parts = dirichlet_partition(y_train, args.clients, args.dirichlet_alpha, seed + 37)
    pairs = choose_cross_group_pairs(anchor, groups, n_pairs=12)
    return BenchmarkData(
        x_train=x_train,
        y_train=y_train,
        x_test=x_test,
        y_test=y_test,
        anchor=anchor,
        schemas=schemas,
        client_indices=parts,
        high_order_pairs=pairs,
        view_dim=0,
        n_views=len(groups),
        n_classes=int(max(y_train.max(), y_test.max())) + 1,
        groups=groups,
    )


PAMAP2_GROUPS = [
    ("heart_rate", [2]),
    ("hand_accel", [4, 5, 6, 7, 8, 9]),
    ("hand_gyro", [10, 11, 12]),
    ("hand_mag", [13, 14, 15]),
    ("chest_accel", [21, 22, 23, 24, 25, 26]),
    ("chest_gyro", [27, 28, 29]),
    ("chest_mag", [30, 31, 32]),
    ("ankle_accel", [38, 39, 40, 41, 42, 43]),
    ("ankle_gyro", [44, 45, 46]),
    ("ankle_mag", [47, 48, 49]),
]


def fill_nan_columns(x: np.ndarray) -> np.ndarray:
    out = x.astype(np.float64, copy=True)
    t = np.arange(out.shape[0], dtype=np.float64)
    for j in range(out.shape[1]):
        col = out[:, j]
        good = np.isfinite(col)
        if not np.any(good):
            out[:, j] = 0.0
        elif not np.all(good):
            out[:, j] = np.interp(t, t[good], col[good])
    return out


def sample_window_candidates(
    candidates: list[tuple[int, int]],
    *,
    max_windows: int,
    rng: np.random.Generator,
) -> list[tuple[int, int]]:
    if max_windows <= 0 or len(candidates) <= max_windows:
        return candidates
    by_label: dict[int, list[int]] = {}
    for i, (_, label) in enumerate(candidates):
        by_label.setdefault(label, []).append(i)
    selected: list[int] = []
    per_label = max(1, max_windows // max(1, len(by_label)))
    for idxs in by_label.values():
        idx_arr = np.asarray(idxs, dtype=np.int64)
        rng.shuffle(idx_arr)
        selected.extend(idx_arr[: min(per_label, len(idx_arr))].tolist())
    if len(selected) < max_windows:
        rest = np.setdiff1d(np.arange(len(candidates), dtype=np.int64), np.asarray(selected, dtype=np.int64), assume_unique=False)
        rng.shuffle(rest)
        selected.extend(rest[: max_windows - len(selected)].tolist())
    if len(selected) > max_windows:
        selected = rng.choice(np.asarray(selected, dtype=np.int64), size=max_windows, replace=False).tolist()
    selected = [int(i) for i in selected]
    rng.shuffle(selected)
    return [candidates[i] for i in selected]


def featurize_pamap2_window(window: np.ndarray) -> tuple[np.ndarray, list[np.ndarray]]:
    feats = []
    groups = []
    offset = 0
    for _, cols in PAMAP2_GROUPS:
        group_feat = summarize_cycle_matrix(window[:, cols].T).reshape(-1)
        feats.append(group_feat)
        groups.append(np.arange(offset, offset + len(group_feat), dtype=np.int64))
        offset += len(group_feat)
    return np.concatenate(feats).astype(np.float64), groups


def load_pamap2(
    root: Path,
    *,
    window: int,
    stride: int,
    max_windows_per_subject: int,
    subject_spec: str,
    seed: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, list[np.ndarray]]:
    base = root / "PAMAP2_Dataset" / "Protocol"
    if not base.exists():
        base = root / "Protocol"
    if not base.exists():
        base = root
    files = sorted(base.glob("subject*.dat"), key=lambda p: int(p.stem.replace("subject", "")))
    if subject_spec.strip().lower() != "all":
        wanted = {int(x.strip()) for x in subject_spec.split(",") if x.strip()}
        files = [p for p in files if int(p.stem.replace("subject", "")) in wanted]
    if not files:
        raise FileNotFoundError(f"Could not find PAMAP2 subject*.dat files under {base}")

    rng = np.random.default_rng(seed)
    label_values: set[int] = set()
    raw_rows: list[tuple[np.ndarray, int, int]] = []
    groups: list[np.ndarray] | None = None
    for path in files:
        subject = int(path.stem.replace("subject", ""))
        raw = np.loadtxt(path, dtype=np.float64)
        y_raw = raw[:, 1].astype(np.int64)
        x_raw = fill_nan_columns(raw)
        candidates: list[tuple[int, int]] = []
        start = 0
        while start < len(y_raw):
            label = int(y_raw[start])
            end = start + 1
            while end < len(y_raw) and int(y_raw[end]) == label:
                end += 1
            if label > 0 and end - start >= window:
                for s in range(start, end - window + 1, stride):
                    candidates.append((s, label))
            start = end
        candidates = sample_window_candidates(candidates, max_windows=max_windows_per_subject, rng=rng)
        for s, label in candidates:
            feat, maybe_groups = featurize_pamap2_window(x_raw[s : s + window])
            groups = maybe_groups
            raw_rows.append((feat, label, subject))
            label_values.add(label)
    if not raw_rows or groups is None:
        raise ValueError("PAMAP2 loader produced no windows; reduce --pamap2-window or check the dataset path")
    label_map = {v: i for i, v in enumerate(sorted(label_values))}
    x = np.vstack([r[0] for r in raw_rows]).astype(np.float64)
    y = np.asarray([label_map[r[1]] for r in raw_rows], dtype=np.int64)
    subjects = np.asarray([r[2] for r in raw_rows], dtype=np.int64)
    return x, y, subjects, groups


def make_pamap2_benchmark(args: argparse.Namespace, seed: int) -> BenchmarkData:
    rng = np.random.default_rng(seed)
    x, y, subjects, groups = load_pamap2(
        Path(args.pamap2_root),
        window=args.pamap2_window,
        stride=args.pamap2_stride,
        max_windows_per_subject=args.pamap2_max_windows_per_subject,
        subject_spec=args.pamap2_subjects,
        seed=seed + 13,
    )
    if args.pamap2_split == "subject":
        subject_ids = np.array(sorted(set(subjects.tolist())), dtype=np.int64)
        rng.shuffle(subject_ids)
        n_test_subjects = max(2, int(round(0.3 * len(subject_ids))))
        test_subjects = set(subject_ids[:n_test_subjects].tolist())
        train_idx = np.where([int(s) not in test_subjects for s in subjects])[0]
        test_idx = np.where([int(s) in test_subjects for s in subjects])[0]
    else:
        train_idx, test_idx = stratified_split(y, train_fraction=0.7, seed=seed + 19)
    if args.n_train > 0 and args.n_train < len(train_idx):
        rel = stratified_subsample(y[train_idx], args.n_train, seed + 23)
        train_idx = train_idx[rel]
    if args.n_test > 0 and args.n_test < len(test_idx):
        rel = stratified_subsample(y[test_idx], args.n_test, seed + 29)
        test_idx = test_idx[rel]
    x_train, y_train = x[train_idx], y[train_idx]
    x_test, y_test = x[test_idx], y[test_idx]
    mean = x_train.mean(axis=0)
    std = x_train.std(axis=0) + 1e-6
    x_train = np.clip((x_train - mean) / (3.0 * std), -1.0, 1.0)
    x_test = np.clip((x_test - mean) / (3.0 * std), -1.0, 1.0)
    anchor_idx = rng.choice(len(x_train), size=min(args.anchor_size, len(x_train)), replace=False)
    anchor = x_train[anchor_idx].copy()
    schemas = make_group_schemas(
        groups=groups,
        n_clients=args.clients,
        views_per_client=args.views_per_client,
        common_views=args.common_views,
        seed=seed + 31,
    )
    parts = dirichlet_partition(y_train, args.clients, args.dirichlet_alpha, seed + 37)
    pairs = choose_cross_group_pairs(anchor, groups, n_pairs=12)
    return BenchmarkData(
        x_train=x_train,
        y_train=y_train,
        x_test=x_test,
        y_test=y_test,
        anchor=anchor,
        schemas=schemas,
        client_indices=parts,
        high_order_pairs=pairs,
        view_dim=0,
        n_views=len(groups),
        n_classes=int(max(y_train.max(), y_test.max())) + 1,
        groups=groups,
    )


def load_mfeat(root: Path) -> tuple[np.ndarray, np.ndarray, list[np.ndarray]]:
    # UCI Multiple Features contains six semantic feature sets for the same
    # 2,000 handwritten digits. The files are label-sorted: 200 samples per
    # digit class from 0 to 9.
    view_files = [
        ("morphological", "mfeat-mor"),
        ("zernike", "mfeat-zer"),
        ("fourier", "mfeat-fou"),
        ("karhunen", "mfeat-kar"),
        ("profile", "mfeat-fac"),
        ("pixel", "mfeat-pix"),
    ]
    views = []
    groups = []
    offset = 0
    for _, filename in view_files:
        path = root / filename
        view = np.loadtxt(path, dtype=np.float64)
        if view.ndim == 1:
            view = view[:, None]
        views.append(view)
        groups.append(np.arange(offset, offset + view.shape[1], dtype=np.int64))
        offset += view.shape[1]
    n = views[0].shape[0]
    if any(v.shape[0] != n for v in views):
        raise ValueError("MFeat view files have inconsistent row counts")
    x = np.concatenate(views, axis=1)
    y = np.repeat(np.arange(10, dtype=np.int64), n // 10)
    return x, y, groups


def make_mfeat_benchmark(args: argparse.Namespace, seed: int) -> BenchmarkData:
    rng = np.random.default_rng(seed)
    x, y, groups = load_mfeat(Path(args.mfeat_root))
    train_idx, test_idx = stratified_split(y, train_fraction=0.7, seed=seed + 19)
    x_train, y_train = x[train_idx], y[train_idx]
    x_test, y_test = x[test_idx], y[test_idx]
    mean = x_train.mean(axis=0)
    std = x_train.std(axis=0) + 1e-6
    x_train = np.clip((x_train - mean) / (3.0 * std), -1.0, 1.0)
    x_test = np.clip((x_test - mean) / (3.0 * std), -1.0, 1.0)
    anchor_idx = rng.choice(len(x_train), size=min(args.anchor_size, len(x_train)), replace=False)
    anchor = x_train[anchor_idx].copy()
    schemas = make_group_schemas(
        groups=groups,
        n_clients=args.clients,
        views_per_client=args.views_per_client,
        common_views=args.common_views,
        seed=seed + 31,
    )
    parts = dirichlet_partition(y_train, args.clients, args.dirichlet_alpha, seed + 37)
    return BenchmarkData(
        x_train=x_train,
        y_train=y_train,
        x_test=x_test,
        y_test=y_test,
        anchor=anchor,
        schemas=schemas,
        client_indices=parts,
        high_order_pairs=[],
        view_dim=0,
        n_views=len(groups),
        n_classes=10,
        groups=groups,
    )


def choose_cross_group_pairs(x: np.ndarray, groups: list[np.ndarray], n_pairs: int) -> list[tuple[int, int]]:
    group_id = {}
    for gid, group in enumerate(groups):
        for coord in group:
            group_id[int(coord)] = gid
    cov = np.abs(np.cov(x, rowvar=False))
    np.fill_diagonal(cov, -np.inf)
    tri = np.triu_indices(cov.shape[0], k=1)
    order = np.argsort(-cov[tri])
    pairs: list[tuple[int, int]] = []
    used: set[int] = set()
    for idx in order:
        a = int(tri[0][idx])
        b = int(tri[1][idx])
        if group_id.get(a) == group_id.get(b):
            continue
        if a in used or b in used:
            continue
        pairs.append((a, b))
        used.add(a)
        used.add(b)
        if len(pairs) >= n_pairs:
            break
    return pairs


def make_mfeat_interaction_benchmark(args: argparse.Namespace, seed: int) -> BenchmarkData:
    rng = np.random.default_rng(seed)
    x, _, groups = load_mfeat(Path(args.mfeat_root))
    z = (x - x.mean(axis=0)) / (x.std(axis=0) + 1e-6)
    pairs = choose_cross_group_pairs(z, groups, n_pairs=2)
    if len(pairs) < 2:
        raise ValueError("Could not find enough cross-source MFeat interaction pairs")
    s1 = z[:, pairs[0][0]] * z[:, pairs[0][1]]
    s2 = z[:, pairs[1][0]] * z[:, pairs[1][1]]
    y = (s1 > np.median(s1)).astype(np.int64) * 2 + (s2 > np.median(s2)).astype(np.int64)
    train_idx, test_idx = stratified_split(y, train_fraction=0.7, seed=seed + 19)
    x_train, y_train = x[train_idx], y[train_idx]
    x_test, y_test = x[test_idx], y[test_idx]
    mean = x_train.mean(axis=0)
    std = x_train.std(axis=0) + 1e-6
    x_train = np.clip((x_train - mean) / (3.0 * std), -1.0, 1.0)
    x_test = np.clip((x_test - mean) / (3.0 * std), -1.0, 1.0)
    anchor_idx = rng.choice(len(x_train), size=min(args.anchor_size, len(x_train)), replace=False)
    anchor = x_train[anchor_idx].copy()
    schemas = make_group_schemas(
        groups=groups,
        n_clients=args.clients,
        views_per_client=args.views_per_client,
        common_views=args.common_views,
        seed=seed + 31,
    )
    parts = dirichlet_partition(y_train, args.clients, args.dirichlet_alpha, seed + 37)
    return BenchmarkData(
        x_train=x_train,
        y_train=y_train,
        x_test=x_test,
        y_test=y_test,
        anchor=anchor,
        schemas=schemas,
        client_indices=parts,
        high_order_pairs=pairs,
        view_dim=0,
        n_views=len(groups),
        n_classes=4,
        groups=groups,
    )


def full_with_mask(x: np.ndarray, coords: np.ndarray, d: int) -> tuple[np.ndarray, np.ndarray]:
    values = np.zeros((len(x), d), dtype=np.float64)
    mask = np.zeros((len(x), d), dtype=np.float64)
    values[:, coords] = x[:, coords]
    mask[:, coords] = 1.0
    return values, mask


def class_prototypes(features: np.ndarray, y: np.ndarray, n_classes: int) -> np.ndarray:
    proto = np.zeros((n_classes, features.shape[1]), dtype=np.float64)
    for c in range(n_classes):
        m = y == c
        if np.any(m):
            proto[c] = features[m].mean(axis=0)
    return proto


def nearest_proto(features: np.ndarray, proto: np.ndarray) -> np.ndarray:
    dist = ((features[:, None, :] - proto[None, :, :]) ** 2).mean(axis=2)
    return np.argmin(dist, axis=1).astype(np.int64)


def accuracy(y: np.ndarray, pred: np.ndarray) -> float:
    return float(np.mean(y == pred))


def fit_value_stats(data: BenchmarkData) -> tuple[np.ndarray, np.ndarray]:
    d = data.x_train.shape[1]
    sums = np.zeros(d, dtype=np.float64)
    counts = np.zeros(d, dtype=np.float64)
    for schema, idx in zip(data.schemas, data.client_indices):
        x = data.x_train[idx]
        sums[schema.coords] += x[:, schema.coords].sum(axis=0)
        counts[schema.coords] += len(idx)
    means = np.zeros(d, dtype=np.float64)
    seen = counts > 0
    means[seen] = sums[seen] / counts[seen]
    return means, counts


def eval_feature_method(
    data: BenchmarkData,
    *,
    train_transform,
    test_transform,
    bytes_per_round: int,
) -> tuple[float, float]:
    start = time.perf_counter()
    feats = []
    labels = []
    for schema, idx in zip(data.schemas, data.client_indices):
        feats.append(train_transform(data.x_train[idx], schema.coords))
        labels.append(data.y_train[idx])
    xtr = np.concatenate(feats, axis=0)
    ytr = np.concatenate(labels, axis=0)
    proto = class_prototypes(xtr, ytr, data.n_classes)
    accs = []
    for schema in data.schemas:
        z = test_transform(data.x_test, schema.coords)
        accs.append(accuracy(data.y_test, nearest_proto(z, proto)))
    return float(np.mean(accs)), float(time.perf_counter() - start)


def rff_params(input_dim: int, sketch_dim: int, bandwidth: float, seed: int) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    w = rng.normal(0.0, 1.0 / max(bandwidth, 1e-6), size=(input_dim, sketch_dim))
    b = rng.uniform(0.0, 2.0 * np.pi, size=(sketch_dim,))
    return w, b


def rff_transform(x: np.ndarray, w: np.ndarray, b: np.ndarray) -> np.ndarray:
    return math.sqrt(2.0 / w.shape[1]) * np.cos(x @ w + b)


def pca_reconstruct(anchor: np.ndarray, values: np.ndarray, mask: np.ndarray, rank: int) -> np.ndarray:
    mu = anchor.mean(axis=0)
    centered = anchor - mu
    _, _, vh = np.linalg.svd(centered, full_matrices=False)
    comp = vh[:rank]
    out = np.zeros_like(values)
    for i in range(len(values)):
        obs = mask[i] > 0
        if obs.sum() <= 1:
            out[i] = mu
            continue
        a = comp[:, obs].T
        b = values[i, obs] - mu[obs]
        coef, *_ = np.linalg.lstsq(a, b, rcond=1e-4)
        out[i] = mu + coef @ comp
    return np.clip(out, -1.0, 1.0)


def fit_anchor_ridge_imputer(data: BenchmarkData, ridge_alpha: float) -> np.ndarray:
    d = data.x_train.shape[1]
    design = []
    target = []
    for schema in data.schemas:
        values, mask = full_with_mask(data.anchor, schema.coords, d)
        design.append(np.concatenate([values, mask], axis=1))
        target.append(data.anchor)
    x = np.concatenate(design, axis=0)
    y = np.concatenate(target, axis=0)
    x = np.concatenate([x, np.ones((len(x), 1), dtype=np.float64)], axis=1)
    gram = x.T @ x
    reg = ridge_alpha * np.eye(gram.shape[0], dtype=np.float64)
    reg[-1, -1] = 1e-8
    return np.linalg.solve(gram + reg, x.T @ y)


def apply_anchor_ridge_imputer(x: np.ndarray, coords: np.ndarray, d: int, weights: np.ndarray) -> np.ndarray:
    values, mask = full_with_mask(x, coords, d)
    design = np.concatenate([values, mask, np.ones((len(x), 1), dtype=np.float64)], axis=1)
    pred = design @ weights
    return np.clip(mask * values + (1.0 - mask) * pred, -1.0, 1.0)


def partial_design(x: np.ndarray, coords: np.ndarray, d: int) -> np.ndarray:
    values, mask = full_with_mask(x, coords, d)
    return np.concatenate([values, mask], axis=1)


def make_anchor_partial_dataset(data: BenchmarkData) -> tuple[np.ndarray, np.ndarray]:
    d = data.x_train.shape[1]
    design = []
    target = []
    for schema in data.schemas:
        design.append(partial_design(data.anchor, schema.coords, d))
        target.append(data.anchor)
    return np.concatenate(design, axis=0), np.concatenate(target, axis=0)


def fit_torch_anchor_autoencoder(data: BenchmarkData, args: argparse.Namespace, seed: int):
    if torch is None or nn is None:
        return None
    torch.manual_seed(seed)
    d = data.x_train.shape[1]
    x_np, y_np = make_anchor_partial_dataset(data)
    x = torch.tensor(x_np, dtype=torch.float32)
    y = torch.tensor(y_np, dtype=torch.float32)
    model = nn.Sequential(
        nn.Linear(2 * d, args.torch_hidden),
        nn.ReLU(),
        nn.Linear(args.torch_hidden, args.torch_hidden),
        nn.ReLU(),
        nn.Linear(args.torch_hidden, d),
        nn.Tanh(),
    )
    opt = torch.optim.Adam(model.parameters(), lr=args.torch_lr, weight_decay=args.torch_weight_decay)
    loss_fn = nn.MSELoss()
    n = len(x)
    batch = min(args.torch_batch_size, n)
    for epoch in range(args.torch_epochs):
        perm = torch.randperm(n)
        for start in range(0, n, batch):
            idx = perm[start : start + batch]
            pred = model(x[idx])
            loss = loss_fn(pred, y[idx])
            opt.zero_grad()
            loss.backward()
            opt.step()
    model.eval()
    return model


def apply_torch_autoencoder(x: np.ndarray, coords: np.ndarray, d: int, model) -> np.ndarray:
    values, mask = full_with_mask(x, coords, d)
    if model is None:
        return values
    design = np.concatenate([values, mask], axis=1)
    with torch.no_grad():
        pred = model(torch.tensor(design, dtype=torch.float32)).cpu().numpy()
    return np.clip(mask * values + (1.0 - mask) * pred, -1.0, 1.0)


def make_client_partial_dataset(data: BenchmarkData) -> tuple[np.ndarray, np.ndarray]:
    d = data.x_train.shape[1]
    xs = []
    ys = []
    for schema, idx in zip(data.schemas, data.client_indices):
        if idx.size == 0:
            continue
        xs.append(partial_design(data.x_train[idx], schema.coords, d))
        ys.append(data.y_train[idx])
    return np.concatenate(xs, axis=0), np.concatenate(ys, axis=0)


def eval_mask_aware_mlp(data: BenchmarkData, args: argparse.Namespace, seed: int) -> tuple[float, float]:
    if torch is None or nn is None:
        return float("nan"), 0.0
    start_time = time.perf_counter()
    torch.manual_seed(seed)
    d = data.x_train.shape[1]
    x_np, y_np = make_client_partial_dataset(data)
    x = torch.tensor(x_np, dtype=torch.float32)
    y = torch.tensor(y_np, dtype=torch.long)
    model = nn.Sequential(
        nn.Linear(2 * d, args.torch_hidden),
        nn.ReLU(),
        nn.Dropout(args.torch_dropout),
        nn.Linear(args.torch_hidden, args.torch_hidden),
        nn.ReLU(),
        nn.Linear(args.torch_hidden, data.n_classes),
    )
    opt = torch.optim.Adam(model.parameters(), lr=args.torch_lr, weight_decay=args.torch_weight_decay)
    loss_fn = nn.CrossEntropyLoss()
    n = len(x)
    batch = min(args.torch_batch_size, n)
    for epoch in range(args.torch_epochs):
        perm = torch.randperm(n)
        for start in range(0, n, batch):
            idx = perm[start : start + batch]
            logits = model(x[idx])
            loss = loss_fn(logits, y[idx])
            opt.zero_grad()
            loss.backward()
            opt.step()
    model.eval()
    accs = []
    with torch.no_grad():
        for schema in data.schemas:
            z = torch.tensor(partial_design(data.x_test, schema.coords, d), dtype=torch.float32)
            pred = model(z).argmax(dim=1).cpu().numpy()
            accs.append(accuracy(data.y_test, pred))
    return float(np.mean(accs)), float(time.perf_counter() - start_time)


class HeMISModalityDropout(nn.Module if nn is not None else object):
    """HeMIS-style missing-modality fusion with training-time view dropout.

    Each semantic source/view has its own small encoder. The classifier receives
    the mean and variance of embeddings over the views available under the
    client schema. During training, observed views are randomly dropped while
    keeping at least one view, matching the missing-modality evaluation setting
    without using test-time source coverage.
    """

    def __init__(self, groups: list[np.ndarray], hidden_dim: int, n_classes: int, dropout: float):
        super().__init__()
        self.group_indices = [torch.tensor(g, dtype=torch.long) for g in groups]
        self.encoders = nn.ModuleList(
            [
                nn.Sequential(
                    nn.Linear(len(g), hidden_dim),
                    nn.ReLU(),
                    nn.Dropout(dropout),
                    nn.Linear(hidden_dim, hidden_dim),
                    nn.ReLU(),
                )
                for g in groups
            ]
        )
        self.classifier = nn.Sequential(
            nn.Linear(2 * hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, n_classes),
        )

    def forward(self, x, view_mask, modality_dropout: float = 0.0):
        embeds = []
        for idx, encoder in zip(self.group_indices, self.encoders):
            embeds.append(encoder(x.index_select(1, idx)))
        z = torch.stack(embeds, dim=1)
        keep = view_mask.float()
        if self.training and modality_dropout > 0:
            sampled = (torch.rand_like(keep) > modality_dropout).float()
            keep = keep * sampled
            empty = keep.sum(dim=1) <= 0.5
            if torch.any(empty):
                avail = view_mask[empty].float()
                probs = avail / avail.sum(dim=1, keepdim=True).clamp_min(1.0)
                chosen = torch.multinomial(probs, 1).squeeze(1)
                keep[empty] = 0.0
                keep[empty, chosen] = 1.0
        denom = keep.sum(dim=1, keepdim=True).clamp_min(1.0)
        mean = (z * keep.unsqueeze(-1)).sum(dim=1) / denom
        var = ((z - mean.unsqueeze(1)) ** 2 * keep.unsqueeze(-1)).sum(dim=1) / denom
        return self.classifier(torch.cat([mean, var], dim=1))


def schema_group_mask(schema: SensorSchema, groups: list[np.ndarray]) -> np.ndarray:
    coords = set(schema.coords.tolist())
    return np.asarray([float(set(g.tolist()).issubset(coords)) for g in groups], dtype=np.float32)


def make_client_view_dataset(data: BenchmarkData) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    xs = []
    masks = []
    ys = []
    for schema, idx in zip(data.schemas, data.client_indices):
        if idx.size == 0:
            continue
        view_mask = schema_group_mask(schema, data.groups)
        xs.append(data.x_train[idx])
        masks.append(np.repeat(view_mask.reshape(1, -1), len(idx), axis=0))
        ys.append(data.y_train[idx])
    return np.concatenate(xs, axis=0), np.concatenate(masks, axis=0), np.concatenate(ys, axis=0)


def eval_hemis_modality_dropout(data: BenchmarkData, args: argparse.Namespace, seed: int) -> tuple[float, float]:
    if torch is None or nn is None:
        return float("nan"), 0.0
    start_time = time.perf_counter()
    torch.manual_seed(seed)
    x_np, mask_np, y_np = make_client_view_dataset(data)
    x = torch.tensor(x_np, dtype=torch.float32)
    view_mask = torch.tensor(mask_np, dtype=torch.float32)
    y = torch.tensor(y_np, dtype=torch.long)
    model = HeMISModalityDropout(data.groups, args.torch_hidden, data.n_classes, args.torch_dropout)
    opt = torch.optim.Adam(model.parameters(), lr=args.torch_lr, weight_decay=args.torch_weight_decay)
    loss_fn = nn.CrossEntropyLoss()
    n = len(x)
    batch = min(args.torch_batch_size, n)
    for _ in range(args.torch_epochs):
        perm = torch.randperm(n)
        model.train()
        for start in range(0, n, batch):
            idx = perm[start : start + batch]
            logits = model(x[idx], view_mask[idx], modality_dropout=args.modality_dropout_prob)
            loss = loss_fn(logits, y[idx])
            opt.zero_grad()
            loss.backward()
            opt.step()
    model.eval()
    accs = []
    with torch.no_grad():
        x_test = torch.tensor(data.x_test, dtype=torch.float32)
        for schema in data.schemas:
            mask = schema_group_mask(schema, data.groups)
            mask_t = torch.tensor(np.repeat(mask.reshape(1, -1), len(data.x_test), axis=0), dtype=torch.float32)
            pred = model(x_test, mask_t, modality_dropout=0.0).argmax(dim=1).cpu().numpy()
            accs.append(accuracy(data.y_test, pred))
    return float(np.mean(accs)), float(time.perf_counter() - start_time)


def fit_late_fusion_prototypes(data: BenchmarkData) -> tuple[list[np.ndarray], list[bool]]:
    protos: list[np.ndarray] = []
    available: list[bool] = []
    schema_sets = [set(schema.coords.tolist()) for schema in data.schemas]
    for group in data.groups:
        group_set = set(group.tolist())
        feats = []
        labels = []
        for schema_set, idx in zip(schema_sets, data.client_indices):
            if idx.size == 0 or not group_set.issubset(schema_set):
                continue
            feats.append(data.x_train[idx][:, group])
            labels.append(data.y_train[idx])
        if feats:
            protos.append(class_prototypes(np.concatenate(feats, axis=0), np.concatenate(labels, axis=0), data.n_classes))
            available.append(True)
        else:
            protos.append(np.zeros((data.n_classes, len(group)), dtype=np.float64))
            available.append(False)
    return protos, available


def eval_late_fusion_method(data: BenchmarkData, *, bytes_per_round: int) -> tuple[float, float]:
    start = time.perf_counter()
    protos, available = fit_late_fusion_prototypes(data)
    accs = []
    for schema in data.schemas:
        schema_set = set(schema.coords.tolist())
        dist_sum = np.zeros((len(data.x_test), data.n_classes), dtype=np.float64)
        n_used = 0
        for group, proto, has_proto in zip(data.groups, protos, available):
            if not has_proto or not set(group.tolist()).issubset(schema_set):
                continue
            xg = data.x_test[:, group]
            dist_sum += ((xg[:, None, :] - proto[None, :, :]) ** 2).mean(axis=2)
            n_used += 1
        if n_used == 0:
            pred = np.zeros(len(data.y_test), dtype=np.int64)
        else:
            pred = np.argmin(dist_sum / n_used, axis=1).astype(np.int64)
        accs.append(accuracy(data.y_test, pred))
    return float(np.mean(accs)), float(time.perf_counter() - start)


def coverage_predict(values: np.ndarray, mask: np.ndarray, proto: np.ndarray, counts: np.ndarray) -> np.ndarray:
    dist = coverage_distances(values, mask, proto, counts)
    return np.argmin(dist, axis=1).astype(np.int64)


def coverage_distances(values: np.ndarray, mask: np.ndarray, proto: np.ndarray, counts: np.ndarray) -> np.ndarray:
    has = (counts > 1e-8).astype(np.float64)
    weights = np.sqrt(np.maximum(counts, 0.0))
    weights /= np.max(weights, axis=1, keepdims=True) + 1e-12
    valid = mask[:, None, :] * has[None, :, :]
    w = valid * weights[None, :, :]
    denom = w.sum(axis=2)
    dist = (w * (values[:, None, :] - proto[None, :, :]) ** 2).sum(axis=2) / (denom + 1e-12)
    dist[denom <= 1e-8] = np.inf
    return dist


def chop_predict(
    values: np.ndarray,
    mask: np.ndarray,
    proto: np.ndarray,
    counts: np.ndarray,
    hop_proto: np.ndarray,
    hop_counts: np.ndarray,
    pair_a: np.ndarray,
    pair_b: np.ndarray,
    hop_weight: float,
) -> np.ndarray:
    low_dist, hdist = chop_distance_parts(values, mask, proto, counts, hop_proto, hop_counts, pair_a, pair_b)
    dist = low_dist + hop_weight * hdist
    return np.argmin(dist, axis=1).astype(np.int64)


def chop_distance_parts(
    values: np.ndarray,
    mask: np.ndarray,
    proto: np.ndarray,
    counts: np.ndarray,
    hop_proto: np.ndarray,
    hop_counts: np.ndarray,
    pair_a: np.ndarray,
    pair_b: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    low_dist = coverage_distances(values, mask, proto, counts)
    hv, hm = hop_values(values, mask, pair_a, pair_b)
    hvalid = hm[:, None, :] * (hop_counts[None, :, :] > 1e-8)
    hden = hvalid.sum(axis=2)
    hdist = (hvalid * (hv[:, None, :] - hop_proto[None, :, :]) ** 2).sum(axis=2) / (hden + 1e-12)
    hdist[hden <= 1e-8] = np.inf
    return low_dist, hdist


def chop_mixture_predict(
    values: np.ndarray,
    mask: np.ndarray,
    proto: np.ndarray,
    counts: np.ndarray,
    hop_proto: np.ndarray,
    hop_counts: np.ndarray,
    pair_a: np.ndarray,
    pair_b: np.ndarray,
    *,
    alpha: float,
    hop_weight: float,
) -> np.ndarray:
    low_dist, hdist = chop_distance_parts(values, mask, proto, counts, hop_proto, hop_counts, pair_a, pair_b)
    if alpha >= 1.0:
        dist = low_dist
    elif alpha <= 0.0:
        dist = hop_weight * hdist
    else:
        dist = alpha * low_dist + (1.0 - alpha) * hop_weight * hdist
    return np.argmin(dist, axis=1).astype(np.int64)


def fit_coverage(data: BenchmarkData, keys: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    sums = np.zeros((data.n_classes, len(keys)), dtype=np.float64)
    counts = np.zeros_like(sums)
    key_lookup = {int(k): j for j, k in enumerate(keys)}
    for schema, idx in zip(data.schemas, data.client_indices):
        local_cols = [key_lookup[int(k)] for k in schema.coords if int(k) in key_lookup]
        global_cols = [int(k) for k in schema.coords if int(k) in key_lookup]
        if not local_cols:
            continue
        y = data.y_train[idx]
        x = data.x_train[idx][:, global_cols]
        for c in range(data.n_classes):
            m = y == c
            if np.any(m):
                sums[c, local_cols] += x[m].sum(axis=0)
                counts[c, local_cols] += m.sum()
    proto = np.zeros_like(sums)
    seen = counts > 0
    proto[seen] = sums[seen] / counts[seen]
    return proto, counts


def selected_values(x: np.ndarray, coords: np.ndarray, keys: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    key_lookup = {int(k): j for j, k in enumerate(keys)}
    values = np.zeros((len(x), len(keys)), dtype=np.float64)
    mask = np.zeros_like(values)
    for k in coords:
        j = key_lookup.get(int(k))
        if j is not None:
            values[:, j] = x[:, int(k)]
            mask[:, j] = 1.0
    return values, mask


def select_keys_by_variance(data: BenchmarkData, k: int) -> np.ndarray:
    d = data.x_train.shape[1]
    sums = np.zeros(d, dtype=np.float64)
    sqs = np.zeros(d, dtype=np.float64)
    counts = np.zeros(d, dtype=np.float64)
    for schema, idx in zip(data.schemas, data.client_indices):
        x = data.x_train[idx][:, schema.coords]
        sums[schema.coords] += x.sum(axis=0)
        sqs[schema.coords] += (x * x).sum(axis=0)
        counts[schema.coords] += len(idx)
    mean = np.divide(sums, counts + 1e-12)
    var = np.divide(sqs, counts + 1e-12) - mean * mean
    score = var * np.sqrt(np.maximum(counts, 0.0))
    return np.sort(np.argsort(-score)[:k]).astype(np.int64)


def select_keys_by_anchor_covariance(data: BenchmarkData, k: int) -> np.ndarray:
    cov = np.abs(np.cov(data.anchor, rowvar=False))
    np.fill_diagonal(cov, 0.0)
    score = cov.sum(axis=0)
    return np.sort(np.argsort(-score)[:k]).astype(np.int64)


def make_pair_indices(k: int, hop_dim: int, seed: int) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    a = rng.integers(0, k, size=hop_dim)
    b = rng.integers(0, k, size=hop_dim)
    same = a == b
    b[same] = (b[same] + 1) % k
    return a.astype(np.int64), b.astype(np.int64)


def make_anchor_pair_indices(anchor_values: np.ndarray, hop_dim: int) -> tuple[np.ndarray, np.ndarray]:
    cov = np.cov(anchor_values, rowvar=False)
    score = np.abs(cov)
    np.fill_diagonal(score, -np.inf)
    tri = np.triu_indices(score.shape[0], k=1)
    order = np.argsort(-score[tri])
    chosen = order[:hop_dim]
    a = tri[0][chosen]
    b = tri[1][chosen]
    if len(a) < hop_dim:
        pad = hop_dim - len(a)
        a = np.concatenate([a, np.arange(pad) % score.shape[0]])
        b = np.concatenate([b, (np.arange(pad) + 1) % score.shape[0]])
    return a.astype(np.int64), b.astype(np.int64)


def make_cross_group_pair_indices(
    anchor_values: np.ndarray,
    keys: np.ndarray,
    groups: list[np.ndarray],
    hop_dim: int,
) -> tuple[np.ndarray, np.ndarray]:
    key_count = len(keys)
    if key_count < 2:
        return np.zeros(hop_dim, dtype=np.int64), np.zeros(hop_dim, dtype=np.int64)

    group_id: dict[int, int] = {}
    for gid, group in enumerate(groups):
        for coord in group:
            group_id[int(coord)] = gid
    selected_groups = np.array([group_id.get(int(k), -1) for k in keys], dtype=np.int64)

    cov = np.cov(anchor_values, rowvar=False)
    score = np.abs(cov)
    np.fill_diagonal(score, -np.inf)
    tri = np.triu_indices(score.shape[0], k=1)
    cross = selected_groups[tri[0]] != selected_groups[tri[1]]
    valid = cross & np.isfinite(score[tri])
    chosen = np.argsort(-score[tri][valid])[:hop_dim]
    base_a = tri[0][valid][chosen].astype(np.int64)
    base_b = tri[1][valid][chosen].astype(np.int64)

    if len(base_a) >= hop_dim:
        return base_a, base_b

    # If the selected key budget leaves too few cross-source pairs, complete the
    # sketch with the strongest remaining anchor pairs so the payload is fixed.
    fallback_a, fallback_b = make_anchor_pair_indices(anchor_values, hop_dim)
    seen = {(int(a), int(b)) for a, b in zip(base_a, base_b)}
    extra_a: list[int] = []
    extra_b: list[int] = []
    for a, b in zip(fallback_a, fallback_b):
        pair = (int(a), int(b))
        if pair in seen:
            continue
        extra_a.append(pair[0])
        extra_b.append(pair[1])
        seen.add(pair)
        if len(base_a) + len(extra_a) >= hop_dim:
            break
    a = np.concatenate([base_a, np.asarray(extra_a, dtype=np.int64)])
    b = np.concatenate([base_b, np.asarray(extra_b, dtype=np.int64)])
    if len(a) < hop_dim:
        pad = hop_dim - len(a)
        a = np.concatenate([a, fallback_a[:pad]])
        b = np.concatenate([b, fallback_b[:pad]])
    return a[:hop_dim].astype(np.int64), b[:hop_dim].astype(np.int64)


def hop_values(values: np.ndarray, mask: np.ndarray, pair_a: np.ndarray, pair_b: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    hm = mask[:, pair_a] * mask[:, pair_b]
    hv = values[:, pair_a] * values[:, pair_b] * hm
    return hv, hm


def fit_chop(
    data: BenchmarkData,
    *,
    keys: np.ndarray,
    hop_dim: int,
    seed: int,
    anchor_pairs: bool,
    pair_policy: str | None = None,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    proto, counts = fit_coverage(data, keys)
    if pair_policy is None:
        pair_policy = "anchor_covariance" if anchor_pairs else "random"
    if pair_policy == "cross_group_covariance":
        pair_a, pair_b = make_cross_group_pair_indices(data.anchor[:, keys], keys, data.groups, hop_dim)
    elif pair_policy == "anchor_covariance":
        pair_a, pair_b = make_anchor_pair_indices(data.anchor[:, keys], hop_dim)
    else:
        pair_a, pair_b = make_pair_indices(len(keys), hop_dim, seed)
    hop_sums = np.zeros((data.n_classes, hop_dim), dtype=np.float64)
    hop_counts = np.zeros_like(hop_sums)
    for schema, idx in zip(data.schemas, data.client_indices):
        values, mask = selected_values(data.x_train[idx], schema.coords, keys)
        hv, hm = hop_values(values, mask, pair_a, pair_b)
        y = data.y_train[idx]
        for c in range(data.n_classes):
            m = y == c
            if np.any(m):
                hop_sums[c] += hv[m].sum(axis=0)
                hop_counts[c] += hm[m].sum(axis=0)
    hop_proto = np.zeros_like(hop_sums)
    seen = hop_counts > 0
    hop_proto[seen] = hop_sums[seen] / hop_counts[seen]
    return proto, counts, hop_proto, hop_counts, pair_a, pair_b


def eval_coverage_method(data: BenchmarkData, *, keys: np.ndarray, bytes_per_round: int) -> tuple[float, float]:
    start = time.perf_counter()
    proto, counts = fit_coverage(data, keys)
    accs = []
    for schema in data.schemas:
        values, mask = selected_values(data.x_test, schema.coords, keys)
        pred = coverage_predict(values, mask, proto, counts)
        accs.append(accuracy(data.y_test, pred))
    return float(np.mean(accs)), float(time.perf_counter() - start)


def eval_group_coverage_method(data: BenchmarkData, *, keys: np.ndarray, bytes_per_round: int) -> tuple[float, float]:
    start = time.perf_counter()
    proto, counts = fit_coverage(data, keys)
    key_lookup = {int(k): j for j, k in enumerate(keys)}
    group_positions: list[np.ndarray] = []
    for group in data.groups:
        pos = [key_lookup[int(k)] for k in group if int(k) in key_lookup]
        if pos:
            group_positions.append(np.array(pos, dtype=np.int64))
    accs = []
    for schema in data.schemas:
        values, mask = selected_values(data.x_test, schema.coords, keys)
        dist_sum = np.zeros((len(data.x_test), data.n_classes), dtype=np.float64)
        used = np.zeros_like(dist_sum)
        for pos in group_positions:
            gmask = mask[:, pos]
            gproto = proto[:, pos]
            gcounts = counts[:, pos]
            has = (gcounts > 1e-8).astype(np.float64)
            weights = np.sqrt(np.maximum(gcounts, 0.0))
            weights /= np.max(weights, axis=1, keepdims=True) + 1e-12
            valid = gmask[:, None, :] * has[None, :, :]
            w = valid * weights[None, :, :]
            denom = w.sum(axis=2)
            gdist = (w * (values[:, None, pos] - gproto[None, :, :]) ** 2).sum(axis=2) / (denom + 1e-12)
            ok = denom > 1e-8
            dist_sum += np.where(ok, gdist, 0.0)
            used += ok.astype(np.float64)
        dist = dist_sum / (used + 1e-12)
        dist[used <= 1e-8] = np.inf
        pred = np.argmin(dist, axis=1).astype(np.int64)
        accs.append(accuracy(data.y_test, pred))
    return float(np.mean(accs)), float(time.perf_counter() - start)


def eval_chop_method(
    data: BenchmarkData,
    *,
    keys: np.ndarray,
    hop_dim: int,
    hop_weight: float,
    seed: int,
    bytes_per_round: int,
    anchor_pairs: bool = True,
    pair_policy: str | None = None,
) -> tuple[float, float]:
    start = time.perf_counter()
    proto, counts, hop_proto, hop_counts, pair_a, pair_b = fit_chop(
        data,
        keys=keys,
        hop_dim=hop_dim,
        seed=seed,
        anchor_pairs=anchor_pairs,
        pair_policy=pair_policy,
    )
    accs = []
    for schema in data.schemas:
        values, mask = selected_values(data.x_test, schema.coords, keys)
        pred = chop_predict(values, mask, proto, counts, hop_proto, hop_counts, pair_a, pair_b, hop_weight)
        accs.append(accuracy(data.y_test, pred))
    return float(np.mean(accs)), float(time.perf_counter() - start)


def train_calibration_split(
    data: BenchmarkData,
    *,
    calib_frac: float,
    seed: int,
) -> tuple[BenchmarkData, list[np.ndarray]]:
    rng = np.random.default_rng(seed)
    fit_indices: list[np.ndarray] = []
    cal_indices: list[np.ndarray] = []
    frac = min(max(float(calib_frac), 0.0), 0.8)
    for idx in data.client_indices:
        idx = np.asarray(idx, dtype=np.int64)
        if len(idx) < 3 or frac <= 0.0:
            fit_indices.append(np.sort(idx))
            cal_indices.append(np.array([], dtype=np.int64))
            continue
        perm = rng.permutation(idx)
        n_cal = int(round(frac * len(idx)))
        n_cal = max(1, min(n_cal, len(idx) - 1))
        cal_indices.append(np.sort(perm[:n_cal]).astype(np.int64))
        fit_indices.append(np.sort(perm[n_cal:]).astype(np.int64))
    fit_data = BenchmarkData(
        x_train=data.x_train,
        y_train=data.y_train,
        x_test=data.x_test,
        y_test=data.y_test,
        anchor=data.anchor,
        schemas=data.schemas,
        client_indices=fit_indices,
        high_order_pairs=data.high_order_pairs,
        view_dim=data.view_dim,
        n_views=data.n_views,
        n_classes=data.n_classes,
        groups=data.groups,
    )
    return fit_data, cal_indices


def calibration_accuracy_coverage(
    data: BenchmarkData,
    cal_indices: list[np.ndarray],
    *,
    keys: np.ndarray,
    proto: np.ndarray,
    counts: np.ndarray,
) -> float:
    accs = []
    for schema, idx in zip(data.schemas, cal_indices):
        if len(idx) == 0:
            continue
        values, mask = selected_values(data.x_train[idx], schema.coords, keys)
        pred = coverage_predict(values, mask, proto, counts)
        accs.append(accuracy(data.y_train[idx], pred))
    return float(np.mean(accs)) if accs else 0.0


def calibration_accuracy_chop(
    data: BenchmarkData,
    cal_indices: list[np.ndarray],
    *,
    keys: np.ndarray,
    proto: np.ndarray,
    counts: np.ndarray,
    hop_proto: np.ndarray,
    hop_counts: np.ndarray,
    pair_a: np.ndarray,
    pair_b: np.ndarray,
    hop_weight: float,
    alpha: float | None = None,
) -> float:
    accs = []
    for schema, idx in zip(data.schemas, cal_indices):
        if len(idx) == 0:
            continue
        values, mask = selected_values(data.x_train[idx], schema.coords, keys)
        if alpha is None:
            pred = chop_predict(values, mask, proto, counts, hop_proto, hop_counts, pair_a, pair_b, hop_weight)
        else:
            pred = chop_mixture_predict(
                values,
                mask,
                proto,
                counts,
                hop_proto,
                hop_counts,
                pair_a,
                pair_b,
                alpha=alpha,
                hop_weight=hop_weight,
            )
        accs.append(accuracy(data.y_train[idx], pred))
    return float(np.mean(accs)) if accs else 0.0


def eval_adaptive_chop_method(
    data: BenchmarkData,
    *,
    low_keys: np.ndarray,
    chop_keys: np.ndarray,
    hop_dim: int,
    hop_weight: float,
    seed: int,
    bytes_per_round: int,
    calib_frac: float,
    adaptive_margin: float,
    anchor_pairs: bool = True,
    pair_policy: str | None = None,
    alpha_grid: list[float] | None = None,
) -> tuple[float, float]:
    start = time.perf_counter()
    fit_data, cal_indices = train_calibration_split(data, calib_frac=calib_frac, seed=seed + 991)

    low_proto, low_counts = fit_coverage(fit_data, low_keys)
    low_cal = calibration_accuracy_coverage(
        data,
        cal_indices,
        keys=low_keys,
        proto=low_proto,
        counts=low_counts,
    )

    chop_proto, chop_counts, hop_proto, hop_counts, pair_a, pair_b = fit_chop(
        fit_data,
        keys=chop_keys,
        hop_dim=hop_dim,
        seed=seed + 997,
        anchor_pairs=anchor_pairs,
        pair_policy=pair_policy,
    )
    alpha_grid = [float(a) for a in (alpha_grid or [0.0, 0.25, 0.5, 0.75, 1.0])]
    candidate_scores: list[tuple[float, str, float | None]] = [(low_cal, "cproto", None)]
    for alpha in alpha_grid:
        mix_cal = calibration_accuracy_chop(
            data,
            cal_indices,
            keys=chop_keys,
            proto=chop_proto,
            counts=chop_counts,
            hop_proto=hop_proto,
            hop_counts=hop_counts,
            pair_a=pair_a,
            pair_b=pair_b,
            hop_weight=hop_weight,
            alpha=alpha,
        )
        candidate_scores.append((mix_cal, "mixture", alpha))

    best_score, best_kind, best_alpha = max(candidate_scores, key=lambda x: (x[0], -1.0 if x[1] == "cproto" else float(x[2] or 0.0)))
    if best_kind == "cproto" or best_score - low_cal <= adaptive_margin:
        acc, _ = eval_coverage_method(data, keys=low_keys, bytes_per_round=bytes_per_round)
    else:
        proto_full, counts_full, hop_proto_full, hop_counts_full, pair_a_full, pair_b_full = fit_chop(
            data,
            keys=chop_keys,
            hop_dim=hop_dim,
            seed=seed + 1009,
            anchor_pairs=anchor_pairs,
            pair_policy=pair_policy,
        )
        accs = []
        for schema in data.schemas:
            values, mask = selected_values(data.x_test, schema.coords, chop_keys)
            pred = chop_mixture_predict(
                values,
                mask,
                proto_full,
                counts_full,
                hop_proto_full,
                hop_counts_full,
                pair_a_full,
                pair_b_full,
                alpha=float(best_alpha),
                hop_weight=hop_weight,
            )
            accs.append(accuracy(data.y_test, pred))
        acc = float(np.mean(accs))
    return float(acc), float(time.perf_counter() - start)


def fit_diag_chop(data: BenchmarkData, *, keys: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    proto, counts = fit_coverage(data, keys)
    diag_sums = np.zeros((data.n_classes, len(keys)), dtype=np.float64)
    diag_counts = np.zeros_like(diag_sums)
    for schema, idx in zip(data.schemas, data.client_indices):
        values, mask = selected_values(data.x_train[idx], schema.coords, keys)
        sq = values * values * mask
        y = data.y_train[idx]
        for c in range(data.n_classes):
            m = y == c
            if np.any(m):
                diag_sums[c] += sq[m].sum(axis=0)
                diag_counts[c] += mask[m].sum(axis=0)
    diag_proto = np.zeros_like(diag_sums)
    seen = diag_counts > 0
    diag_proto[seen] = diag_sums[seen] / diag_counts[seen]
    return proto, counts, diag_proto, diag_counts


def eval_diag_chop_method(
    data: BenchmarkData,
    *,
    keys: np.ndarray,
    hop_weight: float,
    bytes_per_round: int,
) -> tuple[float, float]:
    start = time.perf_counter()
    proto, counts, diag_proto, diag_counts = fit_diag_chop(data, keys=keys)
    accs = []
    for schema in data.schemas:
        values, mask = selected_values(data.x_test, schema.coords, keys)
        has = (counts > 1e-8).astype(np.float64)
        weights = np.sqrt(np.maximum(counts, 0.0))
        weights /= np.max(weights, axis=1, keepdims=True) + 1e-12
        valid = mask[:, None, :] * has[None, :, :]
        w = valid * weights[None, :, :]
        denom = w.sum(axis=2)
        low_dist = (w * (values[:, None, :] - proto[None, :, :]) ** 2).sum(axis=2) / (denom + 1e-12)
        low_dist[denom <= 1e-8] = np.inf

        sq = values * values * mask
        dvalid = mask[:, None, :] * (diag_counts[None, :, :] > 1e-8)
        dden = dvalid.sum(axis=2)
        ddist = (dvalid * (sq[:, None, :] - diag_proto[None, :, :]) ** 2).sum(axis=2) / (dden + 1e-12)
        ddist[dden <= 1e-8] = np.inf

        dist = low_dist + hop_weight * ddist
        pred = np.argmin(dist, axis=1).astype(np.int64)
        accs.append(accuracy(data.y_test, pred))
    return float(np.mean(accs)), float(time.perf_counter() - start)


def common_keys(data: BenchmarkData) -> np.ndarray:
    sets = [set(s.coords.tolist()) for s in data.schemas]
    inter = set.intersection(*sets)
    return np.array(sorted(inter), dtype=np.int64)


def bytes_proto(n_classes: int, dim: int) -> int:
    return int((n_classes * (dim + 1) + 1) * 4)


def bytes_cproto(n_classes: int, k: int, hop_dim: int = 0) -> int:
    return int((n_classes * (2 * k + hop_dim + 1) + 1) * 4)


def run_seed(args: argparse.Namespace, seed: int) -> list[dict[str, object]]:
    data = make_benchmark(args, seed)
    d = data.x_train.shape[1]
    observed_mean, _ = fit_value_stats(data)
    shared = common_keys(data)
    key_selector = select_keys_by_anchor_covariance if args.key_policy == "anchor_covariance" else select_keys_by_variance
    chop_keys = key_selector(data, args.chop_keys)
    rng = np.random.default_rng(seed + 503)
    random_keys = np.sort(rng.choice(d, size=args.chop_keys, replace=False)).astype(np.int64)
    budget_bytes = bytes_cproto(data.n_classes, args.chop_keys, args.hop_dim)
    if args.equal_cproto_keys <= 0:
        equal_k = int(math.floor(((budget_bytes / 4.0 - 1.0) / data.n_classes - 1.0) / 2.0))
        equal_k = max(1, min(d, equal_k))
    else:
        equal_k = min(d, args.equal_cproto_keys)
    equal_cproto_keys = key_selector(data, equal_k)
    rff_dim = int((budget_bytes / 4 - 1) / data.n_classes - 1)

    results: list[dict[str, object]] = []

    def add(method: str, acc: float, elapsed: float, bytes_: int, family: str) -> None:
        results.append(
            {
                "run": f"if_nonquantum_sensor_seed{seed}",
                "seed": seed,
                "method": method,
                "family": family,
                "final_acc": acc,
                "final_balanced_acc": acc,
                "bytes_per_client_round": bytes_,
                "elapsed_sec": elapsed,
            }
        )

    acc, elapsed = eval_feature_method(
        data,
        train_transform=lambda x, coords: full_with_mask(x, coords, d)[1],
        test_transform=lambda x, coords: full_with_mask(x, coords, d)[1],
        bytes_per_round=bytes_proto(data.n_classes, d),
    )
    add("mask_only_metadata", acc, elapsed, bytes_proto(data.n_classes, d), "missing-view")

    acc, elapsed = eval_feature_method(
        data,
        train_transform=lambda x, coords: full_with_mask(x, coords, d)[0],
        test_transform=lambda x, coords: full_with_mask(x, coords, d)[0],
        bytes_per_round=bytes_proto(data.n_classes, d),
    )
    add("zero_fill_proto", acc, elapsed, bytes_proto(data.n_classes, d), "missing-view")

    acc, elapsed = eval_feature_method(
        data,
        train_transform=lambda x, coords: np.where(full_with_mask(x, coords, d)[1] > 0, full_with_mask(x, coords, d)[0], observed_mean),
        test_transform=lambda x, coords: np.where(full_with_mask(x, coords, d)[1] > 0, full_with_mask(x, coords, d)[0], observed_mean),
        bytes_per_round=bytes_proto(data.n_classes, d),
    )
    add("mean_impute_proto", acc, elapsed, bytes_proto(data.n_classes, d), "missing-view")

    acc, elapsed = eval_feature_method(
        data,
        train_transform=lambda x, coords: np.concatenate(full_with_mask(x, coords, d), axis=1),
        test_transform=lambda x, coords: np.concatenate(full_with_mask(x, coords, d), axis=1),
        bytes_per_round=bytes_proto(data.n_classes, 2 * d),
    )
    add("value_mask_proto", acc, elapsed, bytes_proto(data.n_classes, 2 * d), "missing-view")

    def pca_transform(x: np.ndarray, coords: np.ndarray) -> np.ndarray:
        values, mask = full_with_mask(x, coords, d)
        return pca_reconstruct(data.anchor, values, mask, args.pca_rank)

    acc, elapsed = eval_feature_method(
        data,
        train_transform=pca_transform,
        test_transform=pca_transform,
        bytes_per_round=bytes_proto(data.n_classes, d),
    )
    add("anchor_pca_impute", acc, elapsed, bytes_proto(data.n_classes, d), "missing-view")

    ridge_start = time.perf_counter()
    ridge_weights = fit_anchor_ridge_imputer(data, args.ridge_alpha)
    ridge_fit_elapsed = time.perf_counter() - ridge_start

    def ridge_transform(x: np.ndarray, coords: np.ndarray) -> np.ndarray:
        return apply_anchor_ridge_imputer(x, coords, d, ridge_weights)

    acc, elapsed = eval_feature_method(
        data,
        train_transform=ridge_transform,
        test_transform=ridge_transform,
        bytes_per_round=bytes_proto(data.n_classes, d),
    )
    add("anchor_ridge_impute", acc, elapsed + ridge_fit_elapsed, bytes_proto(data.n_classes, d), "missing-view")

    if not args.skip_torch_baselines and torch is not None and nn is not None:
        ae_start = time.perf_counter()
        ae_model = fit_torch_anchor_autoencoder(data, args, seed + 809)
        ae_fit_elapsed = time.perf_counter() - ae_start

        def ae_transform(x: np.ndarray, coords: np.ndarray) -> np.ndarray:
            return apply_torch_autoencoder(x, coords, d, ae_model)

        acc, elapsed = eval_feature_method(
            data,
            train_transform=ae_transform,
            test_transform=ae_transform,
            bytes_per_round=bytes_proto(data.n_classes, d),
        )
        add("anchor_ae_impute", acc, elapsed + ae_fit_elapsed, bytes_proto(data.n_classes, d), "deep-missing-view")

        acc, elapsed = eval_mask_aware_mlp(data, args, seed + 811)
        add("mask_aware_mlp_pooled", acc, elapsed, bytes_proto(data.n_classes, 2 * d), "deep-missing-view")

        acc, elapsed = eval_hemis_modality_dropout(data, args, seed + 821)
        add("hemis_modality_dropout", acc, elapsed, bytes_proto(data.n_classes, 2 * d), "deep-missing-view")
    elif not args.skip_torch_baselines:
        print("Torch is unavailable; skipping anchor autoencoder, mask-aware pooled MLP, and HeMIS baselines.", flush=True)

    acc, elapsed = eval_late_fusion_method(data, bytes_per_round=bytes_proto(data.n_classes, d))
    add("late_fusion_proto", acc, elapsed, bytes_proto(data.n_classes, d), "missing-view")

    if len(shared) > 0:
        acc, elapsed = eval_feature_method(
            data,
            train_transform=lambda x, coords: x[:, shared],
            test_transform=lambda x, coords: x[:, shared],
            bytes_per_round=bytes_proto(data.n_classes, len(shared)),
        )
        add("shared_view_proto", acc, elapsed, bytes_proto(data.n_classes, len(shared)), "shared-view")

        w_s, b_s = rff_params(len(shared), rff_dim, args.rff_bandwidth, seed + 607)
        acc, elapsed = eval_feature_method(
            data,
            train_transform=lambda x, coords: rff_transform(x[:, shared], w_s, b_s),
            test_transform=lambda x, coords: rff_transform(x[:, shared], w_s, b_s),
            bytes_per_round=budget_bytes,
        )
        add("shared_view_rff_equal_bytes", acc, elapsed, budget_bytes, "strict-budget")

    w_z, b_z = rff_params(d, rff_dim, args.rff_bandwidth, seed + 613)
    acc, elapsed = eval_feature_method(
        data,
        train_transform=lambda x, coords: rff_transform(full_with_mask(x, coords, d)[0], w_z, b_z),
        test_transform=lambda x, coords: rff_transform(full_with_mask(x, coords, d)[0], w_z, b_z),
        bytes_per_round=budget_bytes,
    )
    add("zero_fill_rff_equal_bytes", acc, elapsed, budget_bytes, "strict-budget")

    acc, elapsed = eval_coverage_method(data, keys=np.arange(d, dtype=np.int64), bytes_per_round=bytes_cproto(data.n_classes, d))
    add("coverage_proto_all", acc, elapsed, bytes_cproto(data.n_classes, d), "qproto")

    acc, elapsed = eval_group_coverage_method(data, keys=np.arange(d, dtype=np.int64), bytes_per_round=bytes_cproto(data.n_classes, d))
    add("group_cproto_all", acc, elapsed, bytes_cproto(data.n_classes, d), "qproto")

    acc, elapsed = eval_coverage_method(data, keys=equal_cproto_keys, bytes_per_round=budget_bytes)
    add("cproto_equal_bytes", acc, elapsed, budget_bytes, "strict-budget")

    acc, elapsed = eval_group_coverage_method(data, keys=equal_cproto_keys, bytes_per_round=budget_bytes)
    add("group_cproto_equal_bytes", acc, elapsed, budget_bytes, "strict-budget")

    acc, elapsed = eval_coverage_method(data, keys=random_keys, bytes_per_round=budget_bytes)
    add("random_key_cproto_equal_bytes", acc, elapsed, budget_bytes, "strict-budget")

    acc, elapsed = eval_chop_method(
        data,
        keys=random_keys,
        hop_dim=args.hop_dim,
        hop_weight=args.hop_weight,
        seed=seed + 701,
        bytes_per_round=budget_bytes,
        anchor_pairs=False,
        pair_policy="random",
    )
    add("random_key_hop_equal_bytes", acc, elapsed, budget_bytes, "strict-budget")

    acc, elapsed = eval_chop_method(
        data,
        keys=chop_keys,
        hop_dim=args.hop_dim,
        hop_weight=args.hop_weight,
        seed=seed + 709,
        bytes_per_round=budget_bytes,
        anchor_pairs=True,
        pair_policy=args.hop_pair_policy,
    )
    add("chop_equal_bytes", acc, elapsed, budget_bytes, "qproto")

    if args.include_adaptive_chop:
        acc, elapsed = eval_adaptive_chop_method(
            data,
            low_keys=equal_cproto_keys,
            chop_keys=chop_keys,
            hop_dim=args.hop_dim,
            hop_weight=args.hop_weight,
            seed=seed + 719,
            bytes_per_round=budget_bytes,
            calib_frac=args.adaptive_calib_frac,
            adaptive_margin=args.adaptive_margin,
            anchor_pairs=True,
            pair_policy=args.hop_pair_policy,
            alpha_grid=[float(x) for x in args.adaptive_alpha_grid.split(",") if x.strip()],
        )
        add("adaptive_chop_equal_bytes", acc, elapsed, budget_bytes, "qproto")

    if args.include_diag_hop:
        diag_budget = bytes_cproto(data.n_classes, len(chop_keys), len(chop_keys))
        acc, elapsed = eval_diag_chop_method(
            data,
            keys=chop_keys,
            hop_weight=args.diag_hop_weight,
            bytes_per_round=diag_budget,
        )
        add("diag_chop_equal_bytes", acc, elapsed, diag_budget, "qproto")

    return results


def ci95(xs: list[float]) -> float:
    vals = [float(x) for x in xs]
    if len(vals) <= 1:
        return 0.0
    return float(T_CRIT_95.get(len(vals) - 1, 1.96) * np.std(vals, ddof=1) / math.sqrt(len(vals)))


def normal_one_sided_p(deltas: list[float]) -> float:
    vals = np.array([float(x) for x in deltas], dtype=np.float64)
    if len(vals) <= 1:
        return 1.0
    sd = float(np.std(vals, ddof=1))
    if sd <= 1e-12:
        return 0.0 if float(np.mean(vals)) > 0 else 1.0
    z = float(np.mean(vals)) / (sd / math.sqrt(len(vals)))
    return float(0.5 * math.erfc(z / math.sqrt(2.0)))


LABELS = {
    "mask_only_metadata": "Mask-only metadata",
    "zero_fill_proto": "Zero-fill prototype",
    "mean_impute_proto": "Mean-impute prototype",
    "value_mask_proto": "Value+mask prototype",
    "anchor_pca_impute": "Anchor PCA imputation",
    "anchor_ridge_impute": "Learned ridge imputation",
    "anchor_ae_impute": "Anchor autoencoder imputation",
    "mask_aware_mlp_pooled": "Mask-aware pooled MLP",
    "hemis_modality_dropout": "HeMIS modality-dropout fusion",
    "late_fusion_proto": "View-wise late fusion",
    "shared_view_proto": "Shared-view prototype",
    "shared_view_rff_equal_bytes": "Shared-view RFF equal bytes",
    "zero_fill_rff_equal_bytes": "Zero-fill RFF equal bytes",
    "coverage_proto_all": "Coverage prototype all",
    "group_cproto_all": "Group-balanced CProto all",
    "cproto_equal_bytes": "CProto equal bytes",
    "group_cproto_equal_bytes": "Group-balanced CProto equal bytes",
    "random_key_cproto_equal_bytes": "Random-key CProto equal bytes",
    "random_key_hop_equal_bytes": "Random-key HOP equal bytes",
    "chop_equal_bytes": "CHOP equal bytes",
    "adaptive_chop_equal_bytes": "Adaptive CHOP equal bytes",
    "diag_chop_equal_bytes": "CHOP-Diag equal bytes",
}

ORDER = {
    "mask_only_metadata": 0,
    "zero_fill_proto": 1,
    "mean_impute_proto": 2,
    "value_mask_proto": 3,
    "anchor_pca_impute": 4,
    "anchor_ridge_impute": 5,
    "anchor_ae_impute": 6,
    "mask_aware_mlp_pooled": 7,
    "hemis_modality_dropout": 8,
    "late_fusion_proto": 9,
    "shared_view_proto": 10,
    "shared_view_rff_equal_bytes": 11,
    "zero_fill_rff_equal_bytes": 12,
    "coverage_proto_all": 13,
    "group_cproto_all": 14,
    "cproto_equal_bytes": 15,
    "group_cproto_equal_bytes": 16,
    "random_key_cproto_equal_bytes": 17,
    "random_key_hop_equal_bytes": 18,
    "chop_equal_bytes": 19,
    "adaptive_chop_equal_bytes": 20,
    "diag_chop_equal_bytes": 21,
}


def write_reports(rows: list[dict[str, object]], args: argparse.Namespace) -> None:
    out_csv = Path(args.out_csv)
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    fields = ["run", "seed", "method", "family", "final_acc", "final_balanced_acc", "bytes_per_client_round", "elapsed_sec"]
    with out_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    by_method: dict[str, list[dict[str, object]]] = {}
    for row in rows:
        by_method.setdefault(str(row["method"]), []).append(row)

    summary = []
    for method, vals in by_method.items():
        acc = [float(v["final_acc"]) for v in vals]
        elapsed = [float(v["elapsed_sec"]) for v in vals]
        bytes_ = [float(v["bytes_per_client_round"]) for v in vals]
        summary.append(
            {
                "method": method,
                "n": len(vals),
                "acc_mean": float(np.mean(acc)),
                "acc_ci95": ci95(acc),
                "bytes": float(np.mean(bytes_)),
                "elapsed": float(np.mean(elapsed)),
            }
        )
    summary.sort(key=lambda r: ORDER.get(str(r["method"]), 99))

    if args.dataset == "uci_har":
        title = "Real UCI HAR Missing-View Sensor Fusion Benchmark"
        desc = (
            "The task uses the real UCI HAR smartphone-sensor feature dataset. "
            "Feature groups are treated as semantic sensor views, and each federated client observes only a subset of groups."
        )
        tex_caption = (
            "Real non-quantum missing-view fusion benchmark on UCI HAR smartphone-sensor features. "
            "Feature-name groups are treated as semantic sensor views; each client observes a heterogeneous subset. "
            "Equal-byte rows use the same per-client per-round payload as CHOP."
        )
        table_label = "tab:if-nonquantum-fusion"
        equal_label = "tab:strict-equal-byte"
        equal_caption = "Strict equal-byte controls on the UCI HAR missing-view sensor benchmark. All rows use the same payload as CHOP."
    elif args.dataset == "wdbc":
        title = "Real WDBC Biomedical Missing-View Fusion Benchmark"
        desc = (
            "The task uses the real Wisconsin Diagnostic Breast Cancer dataset. "
            "Ten measurement families are treated as semantic biomedical views, and each federated client observes only a subset of families."
        )
        tex_caption = (
            "Real non-quantum missing-view fusion benchmark on the WDBC biomedical diagnosis dataset. "
            "Measurement families are treated as semantic views; each client observes a heterogeneous subset. "
            "Equal-byte rows use the same per-client per-round payload as CHOP."
        )
        table_label = "tab:if-wdbc-fusion"
        equal_label = "tab:strict-equal-byte-wdbc"
        equal_caption = "Strict equal-byte controls on the WDBC biomedical missing-view benchmark. All rows use the same payload as CHOP."
    elif args.dataset == "gas_drift":
        title = "Real Gas Sensor Array Drift Missing-View Fusion Benchmark"
        desc = (
            "The task uses the real UCI Gas Sensor Array Drift dataset. "
            "Six gas identities are classified from a 16-sensor chemical array; each federated client observes only a subset of sensor sources."
        )
        split_note = "temporal drift split" if args.gas_split == "temporal" else "stratified random split"
        tex_caption = (
            f"Real gas-sensor array missing-view fusion benchmark under a {split_note}. "
            "The 16 chemical sensors are treated as semantic sources; each client observes a heterogeneous sensor subset. "
            "Equal-byte rows use the same per-client per-round payload as CHOP."
        )
        table_label = f"tab:if-gas-drift-{args.gas_split}-fusion"
        equal_label = f"tab:strict-equal-byte-gas-drift-{args.gas_split}"
        equal_caption = "Strict equal-byte controls on the real Gas Sensor Array Drift benchmark. All rows use the same payload as CHOP."
    elif args.dataset == "hydraulic":
        title = "Real Hydraulic Condition Monitoring Multi-Source Fusion Benchmark"
        desc = (
            "The task uses the real UCI Hydraulic Systems condition-monitoring dataset. "
            f"The target is the {args.hydraulic_target} state; pressure, flow, temperature, vibration, power, and efficiency sensors are treated as semantic sources."
        )
        tex_caption = (
            f"Real industrial multi-source missing-view fusion benchmark on UCI Hydraulic Systems condition monitoring ({args.hydraulic_target} target). "
            "Each sensor time series is summarized into cycle-level readout statistics, and each client observes a heterogeneous sensor subset. "
            "Equal-byte rows use the same per-client per-round payload as CHOP."
        )
        table_label = "tab:if-hydraulic-fusion"
        equal_label = "tab:strict-equal-byte-hydraulic"
        equal_caption = "Strict equal-byte controls on the real UCI Hydraulic Systems benchmark. All rows use the same payload as CHOP."
    elif args.dataset == "mhealth":
        title = "Real MHEALTH Wearable Multi-Source Fusion Benchmark"
        desc = (
            "The task uses the real UCI MHEALTH wearable activity-recognition dataset. "
            "Chest, ECG, ankle, and arm sensor modalities are treated as semantic sources; each client observes only a heterogeneous subset."
        )
        split_note = "subject-held-out split" if args.mhealth_split == "subject" else "stratified random window split"
        tex_caption = (
            f"Real wearable multi-source missing-view fusion benchmark on UCI MHEALTH under a {split_note}. "
            "Windowed readout statistics are built from chest accelerometer, chest ECG, ankle IMU, and arm IMU sources. "
            "Equal-byte rows use the same per-client per-round payload as CHOP."
        )
        table_label = "tab:if-mhealth-fusion"
        equal_label = "tab:strict-equal-byte-mhealth"
        equal_caption = "Strict equal-byte controls on the real UCI MHEALTH wearable multi-source benchmark. All rows use the same payload as CHOP."
    elif args.dataset == "pamap2":
        title = "Real PAMAP2 Wearable Multi-Source Fusion Benchmark"
        desc = (
            "The task uses the real UCI PAMAP2 wearable activity-recognition dataset. "
            "Heart-rate, hand, chest, and ankle IMU modalities are treated as semantic sources; each client observes only a heterogeneous subset."
        )
        split_note = "subject-held-out split" if args.pamap2_split == "subject" else "stratified random window split"
        tex_caption = (
            f"Real wearable multi-source missing-view fusion benchmark on UCI PAMAP2 under a {split_note}. "
            "Windowed readout statistics are built from heart-rate, hand IMU, chest IMU, and ankle IMU sources. "
            "Equal-byte rows use the same per-client per-round payload as CHOP."
        )
        table_label = "tab:if-pamap2-fusion"
        equal_label = "tab:strict-equal-byte-pamap2"
        equal_caption = "Strict equal-byte controls on the real UCI PAMAP2 wearable multi-source benchmark. All rows use the same payload as CHOP."
    elif args.dataset == "mfeat":
        title = "Real UCI Multiple Features Missing-View Fusion Benchmark"
        desc = (
            "The task uses the real UCI Multiple Features handwritten-digit dataset. "
            "Six feature families are treated as semantic views, and each federated client observes only a subset of families."
        )
        tex_caption = (
            "Real multi-view missing-view fusion benchmark on the UCI Multiple Features handwritten-digit dataset. "
            "Six feature families are treated as semantic views; each client observes a heterogeneous subset. "
            "Equal-byte rows use the same per-client per-round payload as CHOP."
        )
        table_label = "tab:if-mfeat-fusion"
        equal_label = "tab:strict-equal-byte-mfeat"
        equal_caption = "Strict equal-byte controls on the UCI Multiple Features multi-view benchmark. All rows use the same payload as CHOP."
    elif args.dataset == "mfeat_interaction":
        title = "Semi-Real MFeat Cross-Source Interaction Benchmark"
        desc = (
            "The task uses real UCI Multiple Features source vectors but defines labels by cross-source interaction signs. "
            "It is a semi-real stress test for high-order source fusion rather than a standard digit-recognition benchmark."
        )
        tex_caption = (
            "Semi-real high-order fusion benchmark using UCI Multiple Features source vectors with cross-source interaction labels. "
            "Equal-byte rows use the same per-client per-round payload as CHOP."
        )
        table_label = "tab:if-mfeat-interaction"
        equal_label = "tab:strict-equal-byte-mfeat-interaction"
        equal_caption = "Strict equal-byte controls on the semi-real MFeat cross-source interaction benchmark. All rows use the same payload as CHOP."
    else:
        title = "Non-Quantum IF Missing-View Sensor Fusion Benchmark"
        desc = (
            "The task is a multi-source sensor classification problem with partial client views. "
            "Class means are weak; the main signal is covariance between non-shared sensor sources. "
            "This tests whether the semantic schema/value-mask/CHOP idea is broader than quantum readout."
        )
        tex_caption = (
            "Non-quantum multi-source missing-view fusion benchmark. The task uses heterogeneous sensor-source subsets rather than quantum readout, "
            "with weak class means and covariance-dominated non-shared source interactions. Equal-byte rows use the same per-client per-round payload as CHOP."
        )
        table_label = "tab:if-synthetic-sensor-fusion"
        equal_label = "tab:strict-equal-byte-synthetic"
        equal_caption = "Strict equal-byte controls on the non-quantum sensor-fusion benchmark. All rows use the same payload as CHOP."

    md = [
        f"# {title}",
        "",
        desc,
        "",
        "| Method | n | Acc. | 95% CI | Bytes | Runtime s |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for r in summary:
        md.append(
            f"| {LABELS.get(str(r['method']), str(r['method']))} | {r['n']} | "
            f"{float(r['acc_mean']):.4f} | {float(r['acc_ci95']):.4f} | "
            f"{float(r['bytes']):.0f} | {float(r['elapsed']):.3f} |"
        )

    paired_controls = [
        ("cproto_equal_bytes", "zero_fill_rff_equal_bytes", "CProto - zero-fill RFF equal bytes"),
        ("cproto_equal_bytes", "shared_view_rff_equal_bytes", "CProto - shared-view RFF equal bytes"),
        ("cproto_equal_bytes", "random_key_hop_equal_bytes", "CProto - random-key HOP equal bytes"),
        ("random_key_hop_equal_bytes", "random_key_cproto_equal_bytes", "Random HOP - random CProto equal bytes"),
        ("group_cproto_equal_bytes", "zero_fill_rff_equal_bytes", "Group CProto - zero-fill RFF equal bytes"),
        ("group_cproto_equal_bytes", "shared_view_rff_equal_bytes", "Group CProto - shared-view RFF equal bytes"),
        ("group_cproto_all", "coverage_proto_all", "Group all - coverage all"),
        ("coverage_proto_all", "anchor_pca_impute", "Coverage all - anchor PCA imputation"),
        ("coverage_proto_all", "anchor_ridge_impute", "Coverage all - learned ridge imputation"),
        ("coverage_proto_all", "anchor_ae_impute", "Coverage all - anchor autoencoder imputation"),
        ("coverage_proto_all", "mask_aware_mlp_pooled", "Coverage all - mask-aware pooled MLP"),
        ("coverage_proto_all", "hemis_modality_dropout", "Coverage all - HeMIS modality dropout"),
        ("coverage_proto_all", "late_fusion_proto", "Coverage all - view-wise late fusion"),
        ("group_cproto_all", "hemis_modality_dropout", "Group all - HeMIS modality dropout"),
        ("chop_equal_bytes", "cproto_equal_bytes", "CHOP - CProto equal bytes"),
        ("chop_equal_bytes", "zero_fill_rff_equal_bytes", "CHOP - zero-fill RFF equal bytes"),
        ("chop_equal_bytes", "shared_view_rff_equal_bytes", "CHOP - shared-view RFF equal bytes"),
        ("chop_equal_bytes", "random_key_hop_equal_bytes", "CHOP - random-key HOP equal bytes"),
        ("chop_equal_bytes", "anchor_pca_impute", "CHOP - anchor PCA imputation"),
        ("chop_equal_bytes", "anchor_ridge_impute", "CHOP - learned ridge imputation"),
        ("chop_equal_bytes", "anchor_ae_impute", "CHOP - anchor autoencoder imputation"),
        ("chop_equal_bytes", "mask_aware_mlp_pooled", "CHOP - mask-aware pooled MLP"),
        ("chop_equal_bytes", "hemis_modality_dropout", "CHOP - HeMIS modality dropout"),
        ("chop_equal_bytes", "late_fusion_proto", "CHOP - view-wise late fusion"),
        ("adaptive_chop_equal_bytes", "cproto_equal_bytes", "Adaptive CHOP - CProto equal bytes"),
        ("adaptive_chop_equal_bytes", "chop_equal_bytes", "Adaptive CHOP - CHOP equal bytes"),
        ("adaptive_chop_equal_bytes", "zero_fill_rff_equal_bytes", "Adaptive CHOP - zero-fill RFF equal bytes"),
        ("adaptive_chop_equal_bytes", "shared_view_rff_equal_bytes", "Adaptive CHOP - shared-view RFF equal bytes"),
        ("adaptive_chop_equal_bytes", "random_key_hop_equal_bytes", "Adaptive CHOP - random-key HOP equal bytes"),
        ("adaptive_chop_equal_bytes", "hemis_modality_dropout", "Adaptive CHOP - HeMIS modality dropout"),
        ("diag_chop_equal_bytes", "cproto_equal_bytes", "CHOP-Diag - CProto equal bytes"),
        ("diag_chop_equal_bytes", "chop_equal_bytes", "CHOP-Diag - CHOP equal bytes"),
        ("diag_chop_equal_bytes", "zero_fill_rff_equal_bytes", "CHOP-Diag - zero-fill RFF equal bytes"),
        ("diag_chop_equal_bytes", "shared_view_rff_equal_bytes", "CHOP-Diag - shared-view RFF equal bytes"),
        ("diag_chop_equal_bytes", "mask_aware_mlp_pooled", "CHOP-Diag - mask-aware pooled MLP"),
    ]
    md.extend(["", "## Paired Seed Deltas", "", "| Comparison | Mean delta | Wins | Normal approx. p |", "|---|---:|---:|---:|"])
    by_seed_method = {(int(r["seed"]), str(r["method"])): float(r["final_acc"]) for r in rows}
    for a, b, label in paired_controls:
        deltas = []
        for seed in sorted({int(r["seed"]) for r in rows}):
            if (seed, a) in by_seed_method and (seed, b) in by_seed_method:
                deltas.append(by_seed_method[(seed, a)] - by_seed_method[(seed, b)])
        if deltas:
            md.append(f"| {label} | {float(np.mean(deltas)):.4f} | {sum(d > 0 for d in deltas)}/{len(deltas)} | {normal_one_sided_p(deltas):.4f} |")
    Path(args.out_md).write_text("\n".join(md), encoding="utf-8")

    tex = [
        "\\begin{table*}[t]",
        "\\centering",
        f"\\caption{{{tex_caption}}}",
        f"\\label{{{table_label}}}",
        "\\scriptsize",
        "\\setlength{\\tabcolsep}{3pt}",
        "\\renewcommand{\\arraystretch}{0.94}",
        "\\begin{tabular}{lcccc}",
        "\\toprule",
        "Method & Acc. & 95\\% CI & Bytes & Runtime (s) \\\\",
        "\\midrule",
    ]
    for r in summary:
        tex.append(
            f"{LABELS.get(str(r['method']), str(r['method']))} & "
            f"{float(r['acc_mean']):.3f} & {float(r['acc_ci95']):.3f} & "
            f"{float(r['bytes']):.0f} & {float(r['elapsed']):.3f} \\\\"
        )
    tex.extend(["\\bottomrule", "\\end{tabular}", "\\end{table*}", ""])
    Path(args.out_tex).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out_tex).write_text("\n".join(tex), encoding="utf-8")

    tex2 = [
        "\\begin{table}[t]",
        "\\centering",
        f"\\caption{{{equal_caption}}}",
        f"\\label{{{equal_label}}}",
        "\\begin{tabular}{lcc}",
        "\\toprule",
        "Method & Acc. & Bytes \\\\",
        "\\midrule",
    ]
    strict = [r for r in summary if str(r["method"]) in {"shared_view_rff_equal_bytes", "zero_fill_rff_equal_bytes", "cproto_equal_bytes", "group_cproto_equal_bytes", "random_key_cproto_equal_bytes", "random_key_hop_equal_bytes", "chop_equal_bytes", "adaptive_chop_equal_bytes", "diag_chop_equal_bytes"}]
    for r in strict:
        tex2.append(f"{LABELS.get(str(r['method']), str(r['method']))} & {float(r['acc_mean']):.3f} & {float(r['bytes']):.0f} \\\\")
    tex2.extend(["\\bottomrule", "\\end{tabular}", "\\end{table}", ""])
    Path(args.out_equal_tex).write_text("\n".join(tex2), encoding="utf-8")

    print(f"Wrote {args.out_csv}, {args.out_md}, {args.out_tex}, and {args.out_equal_tex}")


def build_argparser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser("Non-quantum IF missing-view sensor fusion benchmark")
    p.add_argument("--dataset", type=str, default="synthetic_sensor", choices=["synthetic_sensor", "uci_har", "wdbc", "gas_drift", "hydraulic", "mhealth", "pamap2", "mfeat", "mfeat_interaction"])
    p.add_argument("--uci-har-root", type=str, default="data/uci_har")
    p.add_argument("--wdbc-path", type=str, default="data/wdbc/wdbc.data")
    p.add_argument("--gas-drift-root", type=str, default="data/gas_drift")
    p.add_argument("--gas-split", type=str, default="temporal", choices=["temporal", "random"])
    p.add_argument("--hydraulic-root", type=str, default="data/hydraulic")
    p.add_argument("--hydraulic-target", type=str, default="accumulator", choices=sorted(HYDRAULIC_TARGETS))
    p.add_argument("--mhealth-root", type=str, default="data/mhealth")
    p.add_argument("--mhealth-window", type=int, default=128)
    p.add_argument("--mhealth-stride", type=int, default=64)
    p.add_argument("--mhealth-split", type=str, default="subject", choices=["subject", "random"])
    p.add_argument("--mhealth-max-windows-per-subject", type=int, default=900)
    p.add_argument("--pamap2-root", type=str, default="data/pamap2")
    p.add_argument("--pamap2-window", type=int, default=128)
    p.add_argument("--pamap2-stride", type=int, default=64)
    p.add_argument("--pamap2-split", type=str, default="subject", choices=["subject", "random"])
    p.add_argument("--pamap2-max-windows-per-subject", type=int, default=1200)
    p.add_argument("--pamap2-subjects", type=str, default="all")
    p.add_argument("--mfeat-root", type=str, default="data/mfeat")
    p.add_argument("--seeds", type=str, default="0,1,2,3,4")
    p.add_argument("--n-train", type=int, default=7000)
    p.add_argument("--n-test", type=int, default=2500)
    p.add_argument("--anchor-size", type=int, default=512)
    p.add_argument("--n-classes", type=int, default=5)
    p.add_argument("--n-views", type=int, default=12)
    p.add_argument("--view-dim", type=int, default=8)
    p.add_argument("--clients", type=int, default=20)
    p.add_argument("--views-per-client", type=int, default=8)
    p.add_argument("--common-views", type=int, default=1)
    p.add_argument("--dirichlet-alpha", type=float, default=0.7)
    p.add_argument("--chop-keys", type=int, default=64)
    p.add_argument("--equal-cproto-keys", type=int, default=0, help="Low-order CProto key count for equal-byte controls; 0 derives the largest count that fits the CHOP payload.")
    p.add_argument("--hop-dim", type=int, default=64)
    p.add_argument("--hop-weight", type=float, default=1.5)
    p.add_argument("--include-adaptive-chop", action="store_true", help="Add a train-calibrated equal-byte gate that chooses CProto or CHOP without using test labels.")
    p.add_argument("--adaptive-calib-frac", type=float, default=0.25, help="Per-client training fraction used only for the Adaptive CHOP gate.")
    p.add_argument("--adaptive-margin", type=float, default=0.0, help="Minimum calibration accuracy gain required before Adaptive CHOP chooses CHOP over low-order CProto.")
    p.add_argument("--adaptive-alpha-grid", type=str, default="0,0.25,0.5,0.75,1", help="Comma-separated mixture weights for Adaptive CHOP candidates: alpha*d_low + (1-alpha)*d_hop.")
    p.add_argument("--include-diag-hop", action="store_true")
    p.add_argument("--diag-hop-weight", type=float, default=0.5)
    p.add_argument("--pca-rank", type=int, default=16)
    p.add_argument("--ridge-alpha", type=float, default=1e-2)
    p.add_argument("--skip-torch-baselines", action="store_true")
    p.add_argument("--torch-epochs", type=int, default=35)
    p.add_argument("--torch-hidden", type=int, default=128)
    p.add_argument("--torch-lr", type=float, default=1e-3)
    p.add_argument("--torch-weight-decay", type=float, default=1e-4)
    p.add_argument("--torch-dropout", type=float, default=0.05)
    p.add_argument("--torch-batch-size", type=int, default=256)
    p.add_argument("--modality-dropout-prob", type=float, default=0.35, help="Training-time observed-view dropout probability for the HeMIS missing-modality baseline.")
    p.add_argument("--rff-bandwidth", type=float, default=3.5)
    p.add_argument("--key-policy", type=str, default="anchor_covariance", choices=["anchor_covariance", "variance"])
    p.add_argument(
        "--hop-pair-policy",
        type=str,
        default="anchor_covariance",
        choices=["anchor_covariance", "cross_group_covariance", "random"],
        help="Pair selection for CHOP sketches. cross_group_covariance keeps HOP pairs across source groups when possible.",
    )
    p.add_argument("--out-csv", type=str, default="runs/if_nonquantum_sensor_fusion.csv")
    p.add_argument("--out-md", type=str, default="runs/if_nonquantum_sensor_fusion_report.md")
    p.add_argument("--out-tex", type=str, default="latex_qproto_hop_IF/tables/table_if_nonquantum_fusion.tex")
    p.add_argument("--out-equal-tex", type=str, default="latex_qproto_hop_IF/tables/table_strict_equal_byte_controls.tex")
    return p


def main() -> None:
    args = build_argparser().parse_args()
    seeds = [int(x.strip()) for x in args.seeds.split(",") if x.strip()]
    rows: list[dict[str, object]] = []
    for seed in seeds:
        print(f"Running non-quantum IF sensor fusion seed {seed}", flush=True)
        rows.extend(run_seed(args, seed))
    write_reports(rows, args)


if __name__ == "__main__":
    main()

