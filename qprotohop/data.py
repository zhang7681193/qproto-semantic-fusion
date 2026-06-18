from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import numpy as np


@dataclass(frozen=True)
class DatasetBundle:
    x_train: np.ndarray
    y_train: np.ndarray
    x_test: np.ndarray
    y_test: np.ndarray
    n_classes: int


def _flatten_x(x: np.ndarray) -> np.ndarray:
    x = np.asarray(x, dtype=np.float64)
    if x.ndim > 2:
        x = x.reshape(x.shape[0], -1)
    return x


def _remap_and_filter_classes(
    x: np.ndarray,
    y: np.ndarray,
    *,
    n_classes: int | None,
) -> tuple[np.ndarray, np.ndarray, int]:
    y = np.asarray(y).astype(np.int64).reshape(-1)
    classes = np.array(sorted(np.unique(y).tolist()), dtype=np.int64)
    if n_classes is not None and n_classes > 0:
        classes = classes[: min(n_classes, len(classes))]
    keep = np.isin(y, classes)
    x = x[keep]
    y = y[keep]
    mapping = {int(c): i for i, c in enumerate(classes.tolist())}
    y = np.array([mapping[int(v)] for v in y], dtype=np.int64)
    return x, y, int(len(classes))


def _stratified_split(
    x: np.ndarray,
    y: np.ndarray,
    *,
    test_fraction: float,
    seed: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    train_parts = []
    test_parts = []
    for c in sorted(np.unique(y).tolist()):
        idx = np.where(y == c)[0]
        rng.shuffle(idx)
        n_test = max(1, int(round(len(idx) * test_fraction)))
        test_parts.append(idx[:n_test])
        train_parts.append(idx[n_test:])
    train_idx = np.concatenate(train_parts)
    test_idx = np.concatenate(test_parts)
    rng.shuffle(train_idx)
    rng.shuffle(test_idx)
    return x[train_idx], y[train_idx], x[test_idx], y[test_idx]


def _limit_samples(
    x: np.ndarray,
    y: np.ndarray,
    *,
    n: int,
    seed: int,
) -> tuple[np.ndarray, np.ndarray]:
    if n <= 0 or n >= len(y):
        return x, y
    rng = np.random.default_rng(seed)
    idx = rng.choice(len(y), size=n, replace=False)
    return x[idx], y[idx]


def _standardize_split(
    x_train: np.ndarray,
    x_test: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    train_mean = x_train.mean(axis=0, keepdims=True)
    train_std = x_train.std(axis=0, keepdims=True) + 1e-8
    return (x_train - train_mean) / train_std, (x_test - train_mean) / train_std


def make_synthetic_classification(
    *,
    n_train: int = 2400,
    n_test: int = 1000,
    input_dim: int = 12,
    n_classes: int = 4,
    class_sep: float = 2.2,
    structure: str = "mean",
    cov_boost: float = 2.5,
    seed: int = 0,
) -> DatasetBundle:
    """Generate a small non-linear classification dataset.

    The first milestone for QProto-HOP is not dataset heroics; it is whether
    schema-defined comparability wins under controlled readout mismatch. This
    generator gives stable class structure without external downloads.

    `structure="covariance"` makes classes differ mostly by covariance and
    higher-order shape instead of mean. That setting is useful for testing the
    high-order prototype path, because first-order prototypes become weaker.
    """
    rng = np.random.default_rng(seed)
    structure = structure.lower().strip()
    if structure not in {"mean", "covariance", "hybrid"}:
        raise ValueError("structure must be one of: mean, covariance, hybrid")

    centers = rng.normal(0.0, class_sep, size=(n_classes, input_dim))
    warp = rng.normal(0.0, 0.7, size=(input_dim, input_dim))
    q, _ = np.linalg.qr(rng.normal(size=(input_dim, input_dim)))
    basis = q.T
    dirs = basis[np.arange(n_classes) % input_dim]
    dirs2 = basis[(np.arange(n_classes) * 3 + 1) % input_dim]

    def sample_raw(n: int) -> tuple[np.ndarray, np.ndarray]:
        y = rng.integers(0, n_classes, size=n)
        eps = rng.normal(0.0, 1.0, size=(n, input_dim))

        if structure == "mean":
            x = centers[y] + eps
        else:
            radial = rng.normal(0.0, 1.0, size=n)
            kurt = rng.normal(0.0, 1.0, size=n)
            cov_part = (
                0.65 * eps
                + cov_boost * radial[:, None] * dirs[y]
                + 0.45 * cov_boost * (kurt[:, None] ** 2 - 1.0) * dirs2[y]
            )
            if structure == "covariance":
                x = cov_part + 0.05 * centers[y]
            else:
                x = cov_part + 0.45 * centers[y]

        x = x + 0.25 * np.sin(x @ warp / np.sqrt(input_dim))
        return x, y.astype(np.int64)

    x_train, y_train = sample_raw(n_train)
    x_test, y_test = sample_raw(n_test)
    train_mean = x_train.mean(axis=0, keepdims=True)
    train_std = x_train.std(axis=0, keepdims=True) + 1e-8
    x_train = (x_train - train_mean) / train_std
    x_test = (x_test - train_mean) / train_std
    return DatasetBundle(x_train=x_train, y_train=y_train, x_test=x_test, y_test=y_test, n_classes=n_classes)


def load_npz_dataset(
    path: str | Path,
    *,
    n_train: int,
    n_test: int,
    n_classes: int | None,
    test_fraction: float,
    seed: int,
) -> DatasetBundle:
    """Load a local npz dataset.

    Supported formats:
    - `x_train`, `y_train`, `x_test`, `y_test`;
    - `xtr`, `ytr`, `xte`, `yte`, used by several cached CIFAR feature dumps;
    - or `x`, `y`, in which case a stratified train/test split is used.
    """
    path = Path(path)
    with np.load(path) as obj:
        keys = set(obj.files)
        split_key_options = [
            ("x_train", "y_train", "x_test", "y_test"),
            ("xtr", "ytr", "xte", "yte"),
        ]
        split_keys = next((ks for ks in split_key_options if set(ks).issubset(keys)), None)
        if split_keys is not None:
            x_train_key, y_train_key, x_test_key, y_test_key = split_keys
            x_train = _flatten_x(obj[x_train_key])
            y_train = np.asarray(obj[y_train_key], dtype=np.int64).reshape(-1)
            x_test = _flatten_x(obj[x_test_key])
            y_test = np.asarray(obj[y_test_key], dtype=np.int64).reshape(-1)
            y_all = np.concatenate([y_train, y_test], axis=0)
            classes = np.array(sorted(np.unique(y_all).tolist()), dtype=np.int64)
            if n_classes is not None and n_classes > 0:
                classes = classes[: min(n_classes, len(classes))]
            mapping = {int(c): i for i, c in enumerate(classes.tolist())}

            def map_split(x_part: np.ndarray, y_part: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
                keep = np.isin(y_part, classes)
                y_mapped = np.array([mapping[int(v)] for v in y_part[keep]], dtype=np.int64)
                return x_part[keep], y_mapped

            x_train, y_train = map_split(x_train, y_train)
            x_test, y_test = map_split(x_test, y_test)
            n_out = int(len(classes))
        elif {"x", "y"}.issubset(keys):
            x = _flatten_x(obj["x"])
            y = np.asarray(obj["y"], dtype=np.int64).reshape(-1)
            x, y, n_out = _remap_and_filter_classes(x, y, n_classes=n_classes)
            x_train, y_train, x_test, y_test = _stratified_split(x, y, test_fraction=test_fraction, seed=seed)
        else:
            raise ValueError("npz must contain x/y, x_train/y_train/x_test/y_test, or xtr/ytr/xte/yte arrays")

    x_train, y_train = _limit_samples(x_train, y_train, n=n_train, seed=seed + 1)
    x_test, y_test = _limit_samples(x_test, y_test, n=n_test, seed=seed + 2)
    x_train, x_test = _standardize_split(x_train, x_test)
    return DatasetBundle(x_train=x_train, y_train=y_train, x_test=x_test, y_test=y_test, n_classes=n_out)


def load_digits_dataset(
    *,
    n_train: int,
    n_test: int,
    n_classes: int | None,
    test_fraction: float,
    seed: int,
) -> DatasetBundle:
    """Load sklearn's built-in 8x8 digits dataset when sklearn is available."""
    try:
        from sklearn.datasets import load_digits
    except Exception as exc:  # pragma: no cover - depends on optional package
        raise RuntimeError("dataset=digits requires scikit-learn to be installed") from exc

    digits = load_digits()
    x = _flatten_x(digits.data)
    y = np.asarray(digits.target, dtype=np.int64)
    x, y, n_out = _remap_and_filter_classes(x, y, n_classes=n_classes)
    x_train, y_train, x_test, y_test = _stratified_split(x, y, test_fraction=test_fraction, seed=seed)
    x_train, y_train = _limit_samples(x_train, y_train, n=n_train, seed=seed + 1)
    x_test, y_test = _limit_samples(x_test, y_test, n=n_test, seed=seed + 2)
    x_train, x_test = _standardize_split(x_train, x_test)
    return DatasetBundle(x_train=x_train, y_train=y_train, x_test=x_test, y_test=y_test, n_classes=n_out)


def dirichlet_partition(
    y: np.ndarray,
    *,
    n_clients: int,
    alpha: float,
    seed: int,
    min_size: int = 4,
) -> list[np.ndarray]:
    """Label-skew partition with a small non-empty repair."""
    rng = np.random.default_rng(seed)
    classes = np.unique(y)
    client_indices: list[list[int]] = [[] for _ in range(n_clients)]

    for c in classes:
        idx = np.where(y == c)[0]
        rng.shuffle(idx)
        props = rng.dirichlet(np.full(n_clients, alpha, dtype=np.float64))
        cuts = (np.cumsum(props)[:-1] * len(idx)).astype(int)
        splits = np.split(idx, cuts)
        for cid, part in enumerate(splits):
            client_indices[cid].extend(part.tolist())

    all_idx = np.arange(len(y))
    for cid in range(n_clients):
        if len(client_indices[cid]) < min_size:
            need = min_size - len(client_indices[cid])
            donor = rng.choice(all_idx, size=need, replace=False)
            client_indices[cid].extend(donor.tolist())

    out = []
    for cid in range(n_clients):
        arr = np.array(sorted(set(client_indices[cid])), dtype=np.int64)
        rng.shuffle(arr)
        out.append(arr)
    return out


def make_public_anchor_set(x_train: np.ndarray, n_anchor: int, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    n_anchor = int(max(0, min(n_anchor, len(x_train))))
    if n_anchor == 0:
        return np.zeros((0, x_train.shape[1]), dtype=np.float64)
    idx = rng.choice(len(x_train), size=n_anchor, replace=False)
    return x_train[idx].copy()


