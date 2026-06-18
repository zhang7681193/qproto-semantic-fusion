from __future__ import annotations

from dataclasses import dataclass
import numpy as np


@dataclass
class LocalStats:
    counts: np.ndarray
    prototypes: np.ndarray
    hop: np.ndarray | None
    shot_scalar: float = 0.0


@dataclass
class MaskedLocalStats:
    class_counts: np.ndarray
    value_sums: np.ndarray
    obs_counts: np.ndarray
    hop_sums: np.ndarray | None = None
    hop_counts: np.ndarray | None = None
    shot_scalar: float = 0.0


class MomentServer:
    def __init__(self, n_classes: int, feature_dim: int, hop_dim: int = 0, beta: float = 0.7, hop_weight: float = 0.15):
        self.n_classes = int(n_classes)
        self.feature_dim = int(feature_dim)
        self.hop_dim = int(hop_dim)
        self.beta = float(beta)
        self.hop_weight = float(hop_weight)
        self.prototypes = np.zeros((n_classes, feature_dim), dtype=np.float64)
        self.hop = np.zeros((n_classes, hop_dim), dtype=np.float64) if hop_dim > 0 else None
        self.counts = np.zeros((n_classes,), dtype=np.float64)
        self.initialized = False

    def update(self, locals_: list[LocalStats], shrinkage: bool = False, c_shot: float = 1.0) -> dict:
        agg_counts = np.zeros_like(self.counts)
        agg_proto = np.zeros_like(self.prototypes)
        agg_hop = np.zeros_like(self.hop) if self.hop is not None else None
        shrink_factors = []

        for ls in locals_:
            reliability = 1.0
            if shrinkage:
                reliability = 1.0 / (1.0 + c_shot * max(ls.shot_scalar, 0.0))
            shrink_factors.append(float(reliability))
            w_counts = ls.counts.astype(np.float64)
            proto = ls.prototypes
            hop = ls.hop
            if shrinkage and self.initialized:
                proto = ls.prototypes.copy()
                prior_mask = self.counts > 1e-8
                proto[prior_mask] = reliability * proto[prior_mask] + (1.0 - reliability) * self.prototypes[prior_mask]
                if self.hop is not None and ls.hop is not None:
                    hop = ls.hop.copy()
                    hop[prior_mask] = reliability * hop[prior_mask] + (1.0 - reliability) * self.hop[prior_mask]
            agg_counts += w_counts
            agg_proto += w_counts[:, None] * proto
            if agg_hop is not None and hop is not None:
                agg_hop += w_counts[:, None] * hop

        mask = agg_counts > 0
        round_proto = np.zeros_like(self.prototypes)
        round_proto[mask] = agg_proto[mask] / agg_counts[mask, None]

        round_hop = None
        if agg_hop is not None:
            round_hop = np.zeros_like(agg_hop)
            round_hop[mask] = agg_hop[mask] / agg_counts[mask, None]

        if not self.initialized:
            self.prototypes[mask] = round_proto[mask]
            if self.hop is not None and round_hop is not None:
                self.hop[mask] = round_hop[mask]
            self.initialized = True
        else:
            self.prototypes[mask] = self.beta * self.prototypes[mask] + (1.0 - self.beta) * round_proto[mask]
            if self.hop is not None and round_hop is not None:
                self.hop[mask] = self.beta * self.hop[mask] + (1.0 - self.beta) * round_hop[mask]

        self.counts = self.beta * self.counts + (1.0 - self.beta) * agg_counts
        drift = float(np.linalg.norm(round_proto[mask] - self.prototypes[mask])) if np.any(mask) else 0.0
        return {
            "active_classes": int(mask.sum()),
            "mean_shrink": float(np.mean(shrink_factors)) if shrink_factors else 1.0,
            "drift_proxy": drift,
        }

    def predict(self, u: np.ndarray, hop_u: np.ndarray | None = None) -> np.ndarray:
        d_proto = ((u[:, None, :] - self.prototypes[None, :, :]) ** 2).sum(axis=2)
        if self.hop is not None and hop_u is not None:
            d_hop = ((hop_u[:, None, :] - self.hop[None, :, :]) ** 2).sum(axis=2)
            d_proto = d_proto + self.hop_weight * d_hop / max(self.hop_dim, 1)
        return np.argmin(d_proto, axis=1).astype(np.int64)


def compute_local_stats(
    u: np.ndarray,
    y: np.ndarray,
    *,
    n_classes: int,
    hop_u: np.ndarray | None = None,
    shot_scalar: float = 0.0,
) -> LocalStats:
    feature_dim = u.shape[1]
    counts = np.zeros((n_classes,), dtype=np.float64)
    proto = np.zeros((n_classes, feature_dim), dtype=np.float64)
    hop = np.zeros((n_classes, hop_u.shape[1]), dtype=np.float64) if hop_u is not None else None

    for c in range(n_classes):
        mask = y == c
        counts[c] = float(mask.sum())
        if counts[c] > 0:
            proto[c] = u[mask].mean(axis=0)
            if hop is not None:
                hop[c] = hop_u[mask].mean(axis=0)
    return LocalStats(counts=counts, prototypes=proto, hop=hop, shot_scalar=shot_scalar)


class MaskedPrototypeServer:
    """Coverage-aware prototype server over semantic observable coordinates."""

    def __init__(
        self,
        n_classes: int,
        n_observables: int,
        beta: float = 0.7,
        coverage_power: float = 0.5,
        hop_dim: int = 0,
        hop_weight: float = 0.12,
    ):
        self.n_classes = int(n_classes)
        self.n_observables = int(n_observables)
        self.beta = float(beta)
        self.coverage_power = float(coverage_power)
        self.hop_dim = int(hop_dim)
        self.hop_weight = float(hop_weight)
        self.values = np.zeros((n_classes, n_observables), dtype=np.float64)
        self.obs_counts = np.zeros((n_classes, n_observables), dtype=np.float64)
        self.hop = np.zeros((n_classes, self.hop_dim), dtype=np.float64) if self.hop_dim > 0 else None
        self.hop_counts = np.zeros((n_classes,), dtype=np.float64) if self.hop_dim > 0 else None
        self.class_counts = np.zeros((n_classes,), dtype=np.float64)
        self.initialized = False

    def update(self, locals_: list[MaskedLocalStats], shrinkage: bool = False, c_shot: float = 1.0) -> dict:
        agg_class = np.zeros_like(self.class_counts)
        agg_sums = np.zeros_like(self.values)
        agg_obs = np.zeros_like(self.obs_counts)
        agg_hop = np.zeros_like(self.hop) if self.hop is not None else None
        agg_hop_counts = np.zeros_like(self.class_counts) if self.hop is not None else None
        shrink_factors = []

        for ls in locals_:
            reliability = 1.0
            if shrinkage:
                reliability = 1.0 / (1.0 + c_shot * max(ls.shot_scalar, 0.0))
            shrink_factors.append(float(reliability))
            agg_class += ls.class_counts
            if shrinkage and self.initialized:
                local_mean = np.zeros_like(ls.value_sums)
                m = ls.obs_counts > 0
                local_mean[m] = ls.value_sums[m] / ls.obs_counts[m]
                blended = local_mean.copy()
                blended[m] = reliability * local_mean[m] + (1.0 - reliability) * self.values[m]
                agg_sums += blended * ls.obs_counts
            else:
                agg_sums += ls.value_sums
            agg_obs += ls.obs_counts
            if self.hop is not None and ls.hop_sums is not None and ls.hop_counts is not None:
                hop_sums = ls.hop_sums
                if shrinkage and self.initialized:
                    local_hop = np.zeros_like(hop_sums)
                    hm = ls.hop_counts > 0
                    local_hop[hm] = hop_sums[hm] / ls.hop_counts[hm, None]
                    blended_hop = local_hop.copy()
                    blended_hop[hm] = reliability * local_hop[hm] + (1.0 - reliability) * self.hop[hm]
                    hop_sums = blended_hop * ls.hop_counts[:, None]
                agg_hop += hop_sums
                agg_hop_counts += ls.hop_counts

        observed = agg_obs > 0
        round_values = np.zeros_like(self.values)
        round_values[observed] = agg_sums[observed] / agg_obs[observed]

        round_hop = None
        hop_observed = None
        if self.hop is not None and agg_hop is not None and agg_hop_counts is not None:
            hop_observed = agg_hop_counts > 0
            round_hop = np.zeros_like(self.hop)
            round_hop[hop_observed] = agg_hop[hop_observed] / agg_hop_counts[hop_observed, None]

        if not self.initialized:
            self.values[observed] = round_values[observed]
            self.obs_counts[observed] = agg_obs[observed]
            if self.hop is not None and round_hop is not None and hop_observed is not None:
                self.hop[hop_observed] = round_hop[hop_observed]
                self.hop_counts = agg_hop_counts
            self.class_counts = agg_class
            self.initialized = True
        else:
            self.values[observed] = self.beta * self.values[observed] + (1.0 - self.beta) * round_values[observed]
            self.obs_counts = self.beta * self.obs_counts + (1.0 - self.beta) * agg_obs
            if self.hop is not None and round_hop is not None and hop_observed is not None:
                self.hop[hop_observed] = self.beta * self.hop[hop_observed] + (1.0 - self.beta) * round_hop[hop_observed]
                self.hop_counts = self.beta * self.hop_counts + (1.0 - self.beta) * agg_hop_counts
            self.class_counts = self.beta * self.class_counts + (1.0 - self.beta) * agg_class

        drift = float(np.linalg.norm(round_values[observed] - self.values[observed])) if np.any(observed) else 0.0
        coverage = float(np.mean(self.obs_counts > 1e-8))
        hop_gap = class_gap_proxy(self.hop, self.hop_counts) if self.hop is not None and self.hop_counts is not None else 0.0
        return {
            "active_classes": int((self.class_counts > 1e-8).sum()),
            "mean_shrink": float(np.mean(shrink_factors)) if shrink_factors else 1.0,
            "drift_proxy": drift,
            "coverage_proxy": coverage,
            "hop_gap_proxy": float(hop_gap),
        }

    def predict(self, z: np.ndarray, hop_z: np.ndarray | None = None) -> np.ndarray:
        values = z[:, : self.n_observables]
        sample_mask = z[:, self.n_observables : 2 * self.n_observables]
        has_proto = (self.obs_counts > 1e-8).astype(np.float64)
        weights = np.power(np.maximum(self.obs_counts, 0.0), self.coverage_power)
        weights = weights / (np.max(weights, axis=1, keepdims=True) + 1e-12)
        valid = sample_mask[:, None, :] * has_proto[None, :, :]
        w = valid * weights[None, :, :]
        denom = w.sum(axis=2)
        diff = values[:, None, :] - self.values[None, :, :]
        dist = (w * diff * diff).sum(axis=2) / (denom + 1e-12)
        dist[denom <= 1e-8] = np.inf
        empty = ~np.isfinite(dist).any(axis=1)
        if np.any(empty):
            dist[empty] = ((values[empty, None, :] - self.values[None, :, :]) ** 2).mean(axis=2)
        if self.hop is not None and hop_z is not None:
            hop_active = (self.hop_counts > 1e-8).astype(np.float64)
            hop_dist = ((hop_z[:, None, :] - self.hop[None, :, :]) ** 2).mean(axis=2)
            hop_dist[:, hop_active <= 0] = np.inf
            dist = dist + self.hop_weight * hop_dist
        return np.argmin(dist, axis=1).astype(np.int64)


def compute_local_masked_stats(
    z: np.ndarray,
    y: np.ndarray,
    *,
    n_classes: int,
    n_observables: int,
    hop_z: np.ndarray | None = None,
    shot_scalar: float = 0.0,
) -> MaskedLocalStats:
    values = z[:, :n_observables]
    obs_mask = z[:, n_observables : 2 * n_observables]
    class_counts = np.zeros((n_classes,), dtype=np.float64)
    value_sums = np.zeros((n_classes, n_observables), dtype=np.float64)
    obs_counts = np.zeros((n_classes, n_observables), dtype=np.float64)
    hop_sums = np.zeros((n_classes, hop_z.shape[1]), dtype=np.float64) if hop_z is not None else None
    hop_counts = np.zeros((n_classes,), dtype=np.float64) if hop_z is not None else None
    for c in range(n_classes):
        m = y == c
        class_counts[c] = float(m.sum())
        if class_counts[c] > 0:
            value_sums[c] = (values[m] * obs_mask[m]).sum(axis=0)
            obs_counts[c] = obs_mask[m].sum(axis=0)
            if hop_sums is not None and hop_counts is not None:
                hop_sums[c] = hop_z[m].sum(axis=0)
                hop_counts[c] = class_counts[c]
    return MaskedLocalStats(
        class_counts=class_counts,
        value_sums=value_sums,
        obs_counts=obs_counts,
        hop_sums=hop_sums,
        hop_counts=hop_counts,
        shot_scalar=shot_scalar,
    )


def class_gap_proxy(prototypes: np.ndarray, counts: np.ndarray) -> float:
    active = np.where(counts > 1e-8)[0]
    if len(active) <= 1:
        return 0.0
    p = prototypes[active]
    dists = []
    for i in range(len(active)):
        for j in range(i + 1, len(active)):
            dists.append(np.linalg.norm(p[i] - p[j]))
    return float(np.mean(dists)) if dists else 0.0


