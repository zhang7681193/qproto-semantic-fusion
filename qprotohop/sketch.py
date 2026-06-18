from __future__ import annotations

from dataclasses import dataclass
import numpy as np


@dataclass
class RFFSketch:
    input_dim: int
    sketch_dim: int
    bandwidth: float
    seed: int
    anchor_z: np.ndarray | None = None
    anchor_scale: np.ndarray | None = None
    input_normalize: bool = False

    def __post_init__(self) -> None:
        rng = np.random.default_rng(self.seed)
        self.omega = rng.normal(0.0, 1.0 / max(self.bandwidth, 1e-8), size=(self.input_dim, self.sketch_dim))
        self.phase = rng.uniform(0.0, 2.0 * np.pi, size=(self.sketch_dim,))
        if self.input_normalize:
            self.center = (
                np.zeros((self.input_dim,), dtype=np.float64)
                if self.anchor_z is None
                else np.asarray(self.anchor_z, dtype=np.float64).reshape(-1)
            )
            anchor_feat_input = np.zeros((1, self.input_dim), dtype=np.float64)
        else:
            self.center = np.zeros((self.input_dim,), dtype=np.float64)
            anchor_feat_input = (
                np.zeros((1, self.input_dim), dtype=np.float64)
                if self.anchor_z is None
                else np.asarray(self.anchor_z, dtype=np.float64).reshape(1, -1)
            )
        self.scale = (
            np.ones((self.input_dim,), dtype=np.float64)
            if (self.anchor_scale is None or not self.input_normalize)
            else np.asarray(self.anchor_scale, dtype=np.float64).reshape(-1)
        )
        self.scale = np.where(np.abs(self.scale) < 1e-6, 1.0, self.scale)
        self.anchor_feat = self._raw_transform(anchor_feat_input)[0]

    def normalize_input(self, z: np.ndarray) -> np.ndarray:
        z = np.asarray(z, dtype=np.float64)
        return (z - self.center.reshape(1, -1)) / self.scale.reshape(1, -1)

    def _raw_transform(self, z: np.ndarray) -> np.ndarray:
        return np.sqrt(2.0 / self.sketch_dim) * np.cos(z @ self.omega + self.phase)

    def transform(self, z: np.ndarray) -> np.ndarray:
        return self._raw_transform(self.normalize_input(z)) - self.anchor_feat.reshape(1, -1)

    def rbf_distance(self, z_a: np.ndarray, z_b: np.ndarray) -> np.ndarray:
        diff2 = np.sum((z_a - z_b) ** 2, axis=1)
        k = np.exp(-diff2 / (2.0 * self.bandwidth * self.bandwidth))
        return np.sqrt(np.maximum(0.0, 2.0 - 2.0 * k))


@dataclass
class HopSketch:
    feature_dim: int
    hop_dim: int
    seed: int

    def __post_init__(self) -> None:
        rng = np.random.default_rng(self.seed)
        proj = rng.normal(0.0, 1.0, size=(self.feature_dim, self.hop_dim))
        proj /= np.linalg.norm(proj, axis=0, keepdims=True) + 1e-12
        self.proj = proj

    def transform(self, u: np.ndarray) -> np.ndarray:
        return (u @ self.proj) ** 2

    def transform_masked_values(self, z: np.ndarray, n_observables: int) -> np.ndarray:
        values = z[:, :n_observables]
        mask = z[:, n_observables : 2 * n_observables]
        proj = self.proj[:n_observables]
        numerator = (values * mask) @ proj
        visible_energy = mask @ (proj * proj)
        normalized = numerator / np.sqrt(np.maximum(visible_energy, 1e-12))
        return normalized * normalized


