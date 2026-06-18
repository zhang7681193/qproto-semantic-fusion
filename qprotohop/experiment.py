from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from pathlib import Path
import time
import numpy as np

from .data import (
    dirichlet_partition,
    load_digits_dataset,
    load_npz_dataset,
    make_public_anchor_set,
    make_synthetic_classification,
)
from .metrics import accuracy, append_jsonl, balanced_accuracy, nll_from_logits, save_json
from .readout import (
    ClientReadoutSchema,
    PrecomputedReadoutSimulator,
    QuantumReadoutSimulator,
    adapt_readout,
    make_client_schemas,
    shot_variance_scalar,
)
from .sketch import HopSketch, RFFSketch
from .stats import MaskedPrototypeServer, MomentServer, class_gap_proxy, compute_local_masked_stats, compute_local_stats


@dataclass(frozen=True)
class MethodSpec:
    name: str
    adapter_mode: str
    use_hop: bool = False
    shrinkage: bool = False
    shared_only: bool = False
    compressed: bool = False
    kind: str = "stats"  # stats | masked | local | fedavg | fedprox | fedadam | scaffold | feddyn | fedproto | classical | centralized


@dataclass
class MethodContext:
    spec: MethodSpec
    sketch: RFFSketch
    hop: HopSketch | None
    input_dim: int
    hop_input_dim: int = 0
    wrong_shift: int = 7
    shared_keys: np.ndarray | None = None
    masked_keys: np.ndarray | None = None


METHODS: dict[str, MethodSpec] = {
    "local_only": MethodSpec("local_only", "correct", kind="local"),
    "fedavg_forced": MethodSpec("fedavg_forced", "forced_canonical", kind="fedavg"),
    "fedprox_forced": MethodSpec("fedprox_forced", "forced_canonical", kind="fedprox"),
    "fedadam_forced": MethodSpec("fedadam_forced", "forced_canonical", kind="fedadam"),
    "scaffold_forced": MethodSpec("scaffold_forced", "forced_canonical", kind="scaffold"),
    "feddyn_forced": MethodSpec("feddyn_forced", "forced_canonical", kind="feddyn"),
    "fedavg_schema": MethodSpec("fedavg_schema", "correct", kind="fedavg"),
    "fedprox_schema": MethodSpec("fedprox_schema", "correct", kind="fedprox"),
    "fedadam_schema": MethodSpec("fedadam_schema", "correct", kind="fedadam"),
    "scaffold_schema": MethodSpec("scaffold_schema", "correct", kind="scaffold"),
    "feddyn_schema": MethodSpec("feddyn_schema", "correct", kind="feddyn"),
    "fedproto_forced": MethodSpec("fedproto_forced", "forced_canonical", kind="fedproto"),
    "fedproto_schema": MethodSpec("fedproto_schema", "correct", kind="fedproto"),
    "no_schema": MethodSpec("no_schema", "no_schema"),
    "forced_canonical": MethodSpec("forced_canonical", "forced_canonical"),
    "schema_zero_fill": MethodSpec("schema_zero_fill", "correct_values"),
    "schema_mask_only": MethodSpec("schema_mask_only", "correct_mask"),
    "shared_observable": MethodSpec("shared_observable", "correct", shared_only=True),
    "qproto_masked": MethodSpec("qproto_masked", "correct", kind="masked"),
    "qproto_masked_hop": MethodSpec("qproto_masked_hop", "correct", use_hop=True, kind="masked"),
    "qproto_masked_full": MethodSpec("qproto_masked_full", "correct", use_hop=True, shrinkage=True, kind="masked"),
    "qproto_cproto": MethodSpec("qproto_cproto", "correct", compressed=True, kind="masked"),
    "qproto_chop": MethodSpec("qproto_chop", "correct", use_hop=True, compressed=True, kind="masked"),
    "qproto_chop_full": MethodSpec(
        "qproto_chop_full",
        "correct",
        use_hop=True,
        shrinkage=True,
        compressed=True,
        kind="masked",
    ),
    "wrong_schema": MethodSpec("wrong_schema", "wrong_schema", use_hop=True),
    "qproto_proto": MethodSpec("qproto_proto", "correct"),
    "qproto_hop": MethodSpec("qproto_hop", "correct", use_hop=True),
    "qproto_full": MethodSpec("qproto_full", "correct", use_hop=True, shrinkage=True),
    "centralized_qproto": MethodSpec(
        "centralized_qproto",
        "correct",
        use_hop=True,
        shrinkage=True,
        kind="quantum_centralized",
    ),
    "classical_kernel": MethodSpec("classical_kernel", "classical", kind="classical"),
    "centralized_kernel": MethodSpec("centralized_kernel", "classical", kind="centralized"),
}

DEFAULT_METHODS = [
    "local_only",
    "fedavg_forced",
    "fedprox_forced",
    "fedadam_forced",
    "scaffold_forced",
    "feddyn_forced",
    "fedavg_schema",
    "fedprox_schema",
    "fedadam_schema",
    "scaffold_schema",
    "feddyn_schema",
    "fedproto_forced",
    "fedproto_schema",
    "no_schema",
    "forced_canonical",
    "schema_zero_fill",
    "schema_mask_only",
    "shared_observable",
    "qproto_masked",
    "qproto_masked_hop",
    "qproto_masked_full",
    "qproto_cproto",
    "qproto_chop",
    "qproto_chop_full",
    "wrong_schema",
    "qproto_proto",
    "qproto_hop",
    "qproto_full",
    "centralized_qproto",
    "classical_kernel",
    "centralized_kernel",
]


def parse_int_list(text: str) -> list[int]:
    return [int(x.strip()) for x in text.split(",") if x.strip()]


def _input_dim_for_mode(mode: str, n_observables: int, max_raw_dim: int) -> int:
    if mode == "no_schema":
        return 2 * max_raw_dim
    if mode in {"correct_values", "correct_mask"}:
        return n_observables
    return 2 * n_observables


def _filter_shared_readout(
    raw: np.ndarray,
    out_var: np.ndarray,
    schema: ClientReadoutSchema,
    shared_keys: np.ndarray | None,
) -> tuple[np.ndarray, np.ndarray, ClientReadoutSchema]:
    if shared_keys is None:
        return raw, out_var, schema
    keep = np.isin(schema.local_to_global, shared_keys)
    filtered_schema = ClientReadoutSchema(
        client_id=schema.client_id,
        local_to_global=schema.local_to_global[keep],
        readout_p=schema.readout_p,
        depol_p=schema.depol_p,
        depth=schema.depth,
        shots=schema.shots,
    )
    return raw[:, keep], out_var[:, keep], filtered_schema


def _measure_adapt_transform(
    *,
    x: np.ndarray,
    schema: ClientReadoutSchema,
    simulator: QuantumReadoutSimulator,
    ctx: MethodContext,
    n_observables: int,
    max_raw_dim: int,
    seed: int,
    shots: int | None = None,
) -> tuple[np.ndarray, np.ndarray | None, np.ndarray, float]:
    raw, out_var = simulator.measure(x, schema, shots=shots, seed=seed)
    raw, out_var, schema = _filter_shared_readout(raw, out_var, schema, ctx.shared_keys)
    z = adapt_readout(
        raw,
        schema,
        mode=ctx.spec.adapter_mode,
        n_observables=n_observables,
        max_raw_dim=max_raw_dim,
        wrong_shift=ctx.wrong_shift,
    )
    u = ctx.sketch.transform(z)
    z_norm = ctx.sketch.normalize_input(z)
    hop_u = ctx.hop.transform(z_norm[:, : ctx.hop_input_dim]) if ctx.hop is not None else None
    sig = shot_variance_scalar(out_var, int(schema.shots if shots is None else shots))
    return u, hop_u, z, sig


def _compress_masked_z(z: np.ndarray, keys: np.ndarray | None, n_observables: int) -> np.ndarray:
    if keys is None:
        return z
    values = z[:, keys]
    masks = z[:, n_observables + keys]
    return np.concatenate([values, masks], axis=1)


def _select_compressed_keys(
    *,
    zs: list[np.ndarray],
    n_observables: int,
    k: int,
    policy: str,
    seed: int,
) -> np.ndarray | None:
    k = int(k)
    if k <= 0 or k >= n_observables:
        return None
    if policy == "prefix":
        return np.arange(k, dtype=np.int64)
    if policy == "suffix":
        return np.arange(n_observables - k, n_observables, dtype=np.int64)
    if policy == "random":
        rng = np.random.default_rng(seed)
        return np.sort(rng.choice(n_observables, size=k, replace=False)).astype(np.int64)
    if not zs:
        return np.arange(k, dtype=np.int64)
    z_all = np.concatenate(zs, axis=0)
    values = z_all[:, :n_observables]
    masks = z_all[:, n_observables : 2 * n_observables]
    coverage = masks.mean(axis=0)
    means = np.divide(
        (values * masks).sum(axis=0),
        masks.sum(axis=0) + 1e-12,
    )
    centered = (values - means.reshape(1, -1)) * masks
    var = np.divide((centered * centered).sum(axis=0), masks.sum(axis=0) + 1e-12)
    if policy == "coverage":
        score = coverage
    elif policy == "variance":
        score = var * np.sqrt(np.maximum(coverage, 1e-12))
    else:
        raise ValueError("compressed_key_policy must be one of: variance, coverage, random, prefix, suffix")
    order = np.argsort(-score)
    return np.sort(order[:k]).astype(np.int64)


def _build_context(
    *,
    spec: MethodSpec,
    anchor_x: np.ndarray,
    schemas: list[ClientReadoutSchema],
    simulator: QuantumReadoutSimulator,
    n_observables: int,
    max_raw_dim: int,
    sketch_dim: int,
    hop_dim: int,
    bandwidth: float,
    anchor_normalize: bool,
    wrong_shift: int,
    shared_keys: np.ndarray | None,
    compressed_observables: int,
    compressed_key_policy: str,
    seed: int,
) -> MethodContext:
    input_dim = _input_dim_for_mode(spec.adapter_mode, n_observables, max_raw_dim)
    anchor_z = np.zeros((input_dim,), dtype=np.float64)
    anchor_scale = np.ones((input_dim,), dtype=np.float64)
    anchor_zs: list[np.ndarray] = []
    if len(anchor_x) > 0:
        zs = []
        for schema in schemas:
            raw, _ = simulator.measure(anchor_x, schema, shots=2048, seed=seed + 7000 + schema.client_id)
            raw, _, schema_for_anchor = _filter_shared_readout(
                raw,
                np.zeros_like(raw),
                schema,
                shared_keys if spec.shared_only else None,
            )
            zs.append(
                adapt_readout(
                    raw,
                    schema_for_anchor,
                    mode=spec.adapter_mode,
                    n_observables=n_observables,
                    max_raw_dim=max_raw_dim,
                    wrong_shift=wrong_shift,
                )
            )
        anchor_zs = zs
        anchor_z = np.concatenate(zs, axis=0).mean(axis=0)
        anchor_scale = np.concatenate(zs, axis=0).std(axis=0) + 1e-3
    masked_keys = None
    if spec.compressed:
        masked_keys = _select_compressed_keys(
            zs=anchor_zs,
            n_observables=n_observables,
            k=compressed_observables,
            policy=compressed_key_policy,
            seed=seed + 53,
        )
    sketch = RFFSketch(
        input_dim=input_dim,
        sketch_dim=sketch_dim,
        bandwidth=bandwidth,
        seed=seed + 17,
        anchor_z=anchor_z,
        anchor_scale=anchor_scale,
        input_normalize=anchor_normalize,
    )
    hop_input_dim = (
        len(masked_keys)
        if masked_keys is not None
        else (max_raw_dim if spec.adapter_mode == "no_schema" else n_observables)
    )
    hop = HopSketch(feature_dim=hop_input_dim, hop_dim=hop_dim, seed=seed + 29) if spec.use_hop else None
    return MethodContext(
        spec=spec,
        sketch=sketch,
        hop=hop,
        input_dim=input_dim,
        hop_input_dim=hop_input_dim,
        wrong_shift=wrong_shift,
        shared_keys=(shared_keys if spec.shared_only else None),
        masked_keys=masked_keys,
    )


def _build_classical_context(
    *,
    spec: MethodSpec,
    anchor_x: np.ndarray,
    input_dim: int,
    sketch_dim: int,
    bandwidth: float,
    anchor_normalize: bool,
    seed: int,
) -> MethodContext:
    anchor_z = anchor_x.mean(axis=0) if len(anchor_x) > 0 else np.zeros((input_dim,), dtype=np.float64)
    anchor_scale = anchor_x.std(axis=0) + 1e-3 if len(anchor_x) > 0 else np.ones((input_dim,), dtype=np.float64)
    sketch = RFFSketch(
        input_dim=input_dim,
        sketch_dim=sketch_dim,
        bandwidth=bandwidth,
        seed=seed + 17,
        anchor_z=anchor_z,
        anchor_scale=anchor_scale,
        input_normalize=anchor_normalize,
    )
    return MethodContext(spec=spec, sketch=sketch, hop=None, input_dim=input_dim)


def communication_bytes(spec: MethodSpec, *, n_classes: int, sketch_dim: int, hop_dim: int, scalar_bytes: int = 4) -> int:
    scalars_per_class = sketch_dim + 1  # prototype + count
    if spec.use_hop:
        scalars_per_class += hop_dim
    scalars = n_classes * scalars_per_class
    scalars += 1  # schema/hash or method metadata placeholder
    if spec.shrinkage:
        scalars += 1
    return int(scalars * scalar_bytes)


def evaluate_server(
    *,
    server: MomentServer,
    ctx: MethodContext,
    x_test: np.ndarray,
    y_test: np.ndarray,
    schemas: list[ClientReadoutSchema],
    simulator: QuantumReadoutSimulator,
    n_observables: int,
    max_raw_dim: int,
    n_classes: int,
    seed: int,
    eval_shots: int,
) -> dict:
    accs = []
    bals = []
    for schema in schemas:
        u, hop_u, _, _ = _measure_adapt_transform(
            x=x_test,
            schema=schema,
            simulator=simulator,
            ctx=ctx,
            n_observables=n_observables,
            max_raw_dim=max_raw_dim,
            seed=seed + 100000 + schema.client_id,
            shots=eval_shots,
        )
        pred = server.predict(u, hop_u)
        accs.append(accuracy(y_test, pred))
        bals.append(balanced_accuracy(y_test, pred, n_classes))
    return {"acc": float(np.mean(accs)), "balanced_acc": float(np.mean(bals))}


def distortion_proxy(
    *,
    ctx: MethodContext,
    correct_ctx: MethodContext,
    probe_x: np.ndarray,
    schemas: list[ClientReadoutSchema],
    simulator: QuantumReadoutSimulator,
    n_observables: int,
    max_raw_dim: int,
    seed: int,
) -> float:
    """Cross-client same-sample disagreement relative to correct schema.

    Wrong or forced schemas may preserve within-client pairwise distances, so a
    useful failure detector must compare how the same anchor sample lands across
    different clients.
    """
    if len(probe_x) == 0:
        return 0.0
    rng = np.random.default_rng(seed)
    chosen = rng.choice(len(schemas), size=min(6, len(schemas)), replace=False)
    method_us = []
    correct_us = []
    for cid in chosen:
        schema = schemas[int(cid)]
        u_m, _, _, _ = _measure_adapt_transform(
            x=probe_x,
            schema=schema,
            simulator=simulator,
            ctx=ctx,
            n_observables=n_observables,
            max_raw_dim=max_raw_dim,
            seed=seed + 20000 + int(cid),
            shots=2048,
        )
        u_c, _, _, _ = _measure_adapt_transform(
            x=probe_x,
            schema=schema,
            simulator=simulator,
            ctx=correct_ctx,
            n_observables=n_observables,
            max_raw_dim=max_raw_dim,
            seed=seed + 20000 + int(cid),
            shots=2048,
        )
        method_us.append(u_m)
        correct_us.append(u_c)

    vals = []
    for a in range(len(chosen)):
        for b in range(a + 1, len(chosen)):
            dm = np.linalg.norm(method_us[a] - method_us[b], axis=1)
            dc = np.linalg.norm(correct_us[a] - correct_us[b], axis=1)
            vals.append(np.mean(np.abs(dm - dc)))
    return float(np.mean(vals)) if vals else 0.0


def run_stats_method(
    *,
    ctx: MethodContext,
    correct_ctx: MethodContext,
    x_train: np.ndarray,
    y_train: np.ndarray,
    x_test: np.ndarray,
    y_test: np.ndarray,
    client_indices: list[np.ndarray],
    schemas: list[ClientReadoutSchema],
    simulator: QuantumReadoutSimulator,
    n_observables: int,
    max_raw_dim: int,
    n_classes: int,
    rounds: int,
    participation: float,
    beta: float,
    hop_weight: float,
    c_shot: float,
    eval_every: int,
    eval_shots: int,
    probe_x: np.ndarray,
    seed: int,
    out_dir: Path,
) -> dict:
    rng = np.random.default_rng(seed)
    server = MomentServer(
        n_classes=n_classes,
        feature_dim=ctx.sketch.sketch_dim,
        hop_dim=(ctx.hop.hop_dim if ctx.hop is not None else 0),
        beta=beta,
        hop_weight=hop_weight,
    )
    history = []
    n_part = max(1, int(round(len(schemas) * participation)))
    start = time.time()

    for rnd in range(1, rounds + 1):
        participants = rng.choice(len(schemas), size=n_part, replace=False)
        locals_ = []
        for cid in participants:
            schema = schemas[int(cid)]
            idx = client_indices[int(cid)]
            u, hop_u, _, sig = _measure_adapt_transform(
                x=x_train[idx],
                schema=schema,
                simulator=simulator,
                ctx=ctx,
                n_observables=n_observables,
                max_raw_dim=max_raw_dim,
                seed=seed + rnd * 1000 + int(cid),
            )
            locals_.append(
                compute_local_stats(
                    u,
                    y_train[idx],
                    n_classes=n_classes,
                    hop_u=hop_u,
                    shot_scalar=sig,
                )
            )
        info = server.update(locals_, shrinkage=ctx.spec.shrinkage, c_shot=c_shot)

        if rnd == 1 or rnd % eval_every == 0 or rnd == rounds:
            ev = evaluate_server(
                server=server,
                ctx=ctx,
                x_test=x_test,
                y_test=y_test,
                schemas=schemas,
                simulator=simulator,
                n_observables=n_observables,
                max_raw_dim=max_raw_dim,
                n_classes=n_classes,
                seed=seed + rnd * 333,
                eval_shots=eval_shots,
            )
            rec = {
                "method": ctx.spec.name,
                "round": rnd,
                "acc": ev["acc"],
                "balanced_acc": ev["balanced_acc"],
                "class_gap_proxy": class_gap_proxy(server.prototypes, server.counts),
                "distortion_proxy": distortion_proxy(
                    ctx=ctx,
                    correct_ctx=correct_ctx,
                    probe_x=probe_x,
                    schemas=schemas,
                    simulator=simulator,
                    n_observables=n_observables,
                    max_raw_dim=max_raw_dim,
                    seed=seed + rnd * 777,
                ),
                **info,
            }
            history.append(rec)
            append_jsonl(out_dir / "history.jsonl", rec)

    final = history[-1] if history else {}
    return {
        "method": ctx.spec.name,
        "final_acc": float(final.get("acc", 0.0)),
        "final_balanced_acc": float(final.get("balanced_acc", 0.0)),
        "distortion_proxy": float(final.get("distortion_proxy", 0.0)),
        "class_gap_proxy": float(final.get("class_gap_proxy", 0.0)),
        "bytes_per_client_round": communication_bytes(
            ctx.spec,
            n_classes=n_classes,
            sketch_dim=ctx.sketch.sketch_dim,
            hop_dim=(ctx.hop.hop_dim if ctx.hop is not None else 0),
        ),
        "elapsed_sec": float(time.time() - start),
    }


def evaluate_masked_server(
    *,
    server: MaskedPrototypeServer,
    ctx: MethodContext,
    x_test: np.ndarray,
    y_test: np.ndarray,
    schemas: list[ClientReadoutSchema],
    simulator: QuantumReadoutSimulator,
    n_observables: int,
    max_raw_dim: int,
    n_classes: int,
    seed: int,
    eval_shots: int,
) -> dict:
    accs = []
    bals = []
    n_masked_observables = len(ctx.masked_keys) if ctx.masked_keys is not None else n_observables
    for schema in schemas:
        _, _, z, _ = _measure_adapt_transform(
            x=x_test,
            schema=schema,
            simulator=simulator,
            ctx=ctx,
            n_observables=n_observables,
            max_raw_dim=max_raw_dim,
            seed=seed + 100000 + schema.client_id,
            shots=eval_shots,
        )
        z = _compress_masked_z(z, ctx.masked_keys, n_observables)
        hop_z = ctx.hop.transform_masked_values(z, n_masked_observables) if ctx.hop is not None else None
        pred = server.predict(z, hop_z=hop_z)
        accs.append(accuracy(y_test, pred))
        bals.append(balanced_accuracy(y_test, pred, n_classes))
    return {"acc": float(np.mean(accs)), "balanced_acc": float(np.mean(bals))}


def masked_communication_bytes(
    *,
    n_classes: int,
    n_observables: int,
    hop_dim: int = 0,
    scalar_bytes: int = 4,
) -> int:
    return int((n_classes * (2 * n_observables + hop_dim + 1) + 1) * scalar_bytes)


def run_masked_method(
    *,
    ctx: MethodContext,
    x_train: np.ndarray,
    y_train: np.ndarray,
    x_test: np.ndarray,
    y_test: np.ndarray,
    client_indices: list[np.ndarray],
    schemas: list[ClientReadoutSchema],
    simulator: QuantumReadoutSimulator,
    n_observables: int,
    max_raw_dim: int,
    n_classes: int,
    rounds: int,
    participation: float,
    beta: float,
    hop_weight: float,
    c_shot: float,
    eval_every: int,
    eval_shots: int,
    seed: int,
    out_dir: Path,
) -> dict:
    rng = np.random.default_rng(seed)
    n_masked_observables = len(ctx.masked_keys) if ctx.masked_keys is not None else n_observables
    server = MaskedPrototypeServer(
        n_classes=n_classes,
        n_observables=n_masked_observables,
        beta=beta,
        hop_dim=(ctx.hop.hop_dim if ctx.hop is not None else 0),
        hop_weight=hop_weight,
    )
    history = []
    n_part = max(1, int(round(len(schemas) * participation)))
    start = time.time()

    for rnd in range(1, rounds + 1):
        participants = rng.choice(len(schemas), size=n_part, replace=False)
        locals_ = []
        for cid in participants:
            schema = schemas[int(cid)]
            idx = client_indices[int(cid)]
            _, _, z, sig = _measure_adapt_transform(
                x=x_train[idx],
                schema=schema,
                simulator=simulator,
                ctx=ctx,
                n_observables=n_observables,
                max_raw_dim=max_raw_dim,
                seed=seed + rnd * 7100 + int(cid),
            )
            z = _compress_masked_z(z, ctx.masked_keys, n_observables)
            hop_z = ctx.hop.transform_masked_values(z, n_masked_observables) if ctx.hop is not None else None
            locals_.append(
                compute_local_masked_stats(
                    z,
                    y_train[idx],
                    n_classes=n_classes,
                    n_observables=n_masked_observables,
                    hop_z=hop_z,
                    shot_scalar=sig,
                )
            )
        info = server.update(locals_, shrinkage=ctx.spec.shrinkage, c_shot=c_shot)
        if rnd == 1 or rnd % eval_every == 0 or rnd == rounds:
            ev = evaluate_masked_server(
                server=server,
                ctx=ctx,
                x_test=x_test,
                y_test=y_test,
                schemas=schemas,
                simulator=simulator,
                n_observables=n_observables,
                max_raw_dim=max_raw_dim,
                n_classes=n_classes,
                seed=seed + rnd * 733,
                eval_shots=eval_shots,
            )
            rec = {
                "method": ctx.spec.name,
                "round": rnd,
                "acc": ev["acc"],
                "balanced_acc": ev["balanced_acc"],
                "class_gap_proxy": class_gap_proxy(server.values, server.class_counts),
                "distortion_proxy": 0.0,
                **info,
            }
            history.append(rec)
            append_jsonl(out_dir / "history.jsonl", rec)

    final = history[-1] if history else {}
    return {
        "method": ctx.spec.name,
        "final_acc": float(final.get("acc", 0.0)),
        "final_balanced_acc": float(final.get("balanced_acc", 0.0)),
        "distortion_proxy": 0.0,
        "class_gap_proxy": float(final.get("class_gap_proxy", 0.0)),
        "bytes_per_client_round": masked_communication_bytes(
            n_classes=n_classes,
            n_observables=n_masked_observables,
            hop_dim=(ctx.hop.hop_dim if ctx.hop is not None else 0),
        ),
        "elapsed_sec": float(time.time() - start),
    }


def run_local_only(
    *,
    ctx: MethodContext,
    x_train: np.ndarray,
    y_train: np.ndarray,
    x_test: np.ndarray,
    y_test: np.ndarray,
    client_indices: list[np.ndarray],
    schemas: list[ClientReadoutSchema],
    simulator: QuantumReadoutSimulator,
    n_observables: int,
    max_raw_dim: int,
    n_classes: int,
    eval_shots: int,
    seed: int,
) -> dict:
    accs = []
    bals = []
    for schema in schemas:
        idx = client_indices[schema.client_id]
        u, hop_u, _, sig = _measure_adapt_transform(
            x=x_train[idx],
            schema=schema,
            simulator=simulator,
            ctx=ctx,
            n_observables=n_observables,
            max_raw_dim=max_raw_dim,
            seed=seed + 41000 + schema.client_id,
        )
        ls = compute_local_stats(u, y_train[idx], n_classes=n_classes, hop_u=hop_u, shot_scalar=sig)
        server = MomentServer(n_classes=n_classes, feature_dim=ctx.sketch.sketch_dim, beta=0.0)
        server.update([ls])
        ev = evaluate_server(
            server=server,
            ctx=ctx,
            x_test=x_test,
            y_test=y_test,
            schemas=[schema],
            simulator=simulator,
            n_observables=n_observables,
            max_raw_dim=max_raw_dim,
            n_classes=n_classes,
            seed=seed + 42000 + schema.client_id,
            eval_shots=eval_shots,
        )
        accs.append(ev["acc"])
        bals.append(ev["balanced_acc"])
    return {
        "method": ctx.spec.name,
        "final_acc": float(np.mean(accs)),
        "final_balanced_acc": float(np.mean(bals)),
        "distortion_proxy": 0.0,
        "class_gap_proxy": 0.0,
        "bytes_per_client_round": 0,
        "elapsed_sec": 0.0,
    }


def run_centralized_qproto(
    *,
    ctx: MethodContext,
    x_train: np.ndarray,
    y_train: np.ndarray,
    x_test: np.ndarray,
    y_test: np.ndarray,
    client_indices: list[np.ndarray],
    schemas: list[ClientReadoutSchema],
    simulator: QuantumReadoutSimulator,
    n_observables: int,
    max_raw_dim: int,
    n_classes: int,
    hop_weight: float,
    rounds: int,
    beta: float,
    c_shot: float,
    eval_shots: int,
    seed: int,
) -> dict:
    """Full-participation quantum-readout reference with repeated measurements."""
    start = time.time()
    server = MomentServer(
        n_classes=n_classes,
        feature_dim=ctx.sketch.sketch_dim,
        hop_dim=(ctx.hop.hop_dim if ctx.hop is not None else 0),
        beta=beta,
        hop_weight=hop_weight,
    )
    for rnd in range(1, rounds + 1):
        locals_ = []
        for schema in schemas:
            idx = client_indices[schema.client_id]
            u, hop_u, _, sig = _measure_adapt_transform(
                x=x_train[idx],
                schema=schema,
                simulator=simulator,
                ctx=ctx,
                n_observables=n_observables,
                max_raw_dim=max_raw_dim,
                seed=seed + rnd * 51000 + schema.client_id,
            )
            locals_.append(compute_local_stats(u, y_train[idx], n_classes=n_classes, hop_u=hop_u, shot_scalar=sig))
        server.update(locals_, shrinkage=ctx.spec.shrinkage, c_shot=c_shot)
    ev = evaluate_server(
        server=server,
        ctx=ctx,
        x_test=x_test,
        y_test=y_test,
        schemas=schemas,
        simulator=simulator,
        n_observables=n_observables,
        max_raw_dim=max_raw_dim,
        n_classes=n_classes,
        seed=seed + 52000,
        eval_shots=eval_shots,
    )
    return {
        "method": ctx.spec.name,
        "final_acc": float(ev["acc"]),
        "final_balanced_acc": float(ev["balanced_acc"]),
        "distortion_proxy": 0.0,
        "class_gap_proxy": class_gap_proxy(server.prototypes, server.counts),
        "bytes_per_client_round": 0,
        "elapsed_sec": float(time.time() - start),
    }


def _softmax_logits(u: np.ndarray, w: np.ndarray, b: np.ndarray) -> np.ndarray:
    return u @ w.T + b.reshape(1, -1)


def _train_softmax(
    u: np.ndarray,
    y: np.ndarray,
    w: np.ndarray,
    b: np.ndarray,
    *,
    lr: float,
    epochs: int,
    reg: float,
    prox_mu: float = 0.0,
    w_ref: np.ndarray | None = None,
    b_ref: np.ndarray | None = None,
    control_w: np.ndarray | None = None,
    control_b: np.ndarray | None = None,
    dyn_h_w: np.ndarray | None = None,
    dyn_h_b: np.ndarray | None = None,
    dyn_alpha: float = 0.0,
) -> tuple[np.ndarray, np.ndarray]:
    w = w.copy()
    b = b.copy()
    w_ref = w.copy() if w_ref is None else w_ref
    b_ref = b.copy() if b_ref is None else b_ref
    n = max(1, len(y))
    n_classes = w.shape[0]
    for _ in range(epochs):
        logits = _softmax_logits(u, w, b)
        logits -= logits.max(axis=1, keepdims=True)
        probs = np.exp(logits)
        probs /= probs.sum(axis=1, keepdims=True) + 1e-12
        probs[np.arange(len(y)), y] -= 1.0
        grad_w = probs.T @ u / n + reg * w + prox_mu * (w - w_ref)
        grad_b = probs.mean(axis=0) + prox_mu * (b - b_ref)
        if control_w is not None and control_b is not None:
            grad_w += control_w
            grad_b += control_b
        if dyn_h_w is not None and dyn_h_b is not None:
            grad_w += dyn_alpha * (w - w_ref) - dyn_h_w
            grad_b += dyn_alpha * (b - b_ref) - dyn_h_b
        w -= lr * grad_w
        b -= lr * grad_b
    return w, b


def run_fedavg_head(
    *,
    ctx: MethodContext,
    x_train: np.ndarray,
    y_train: np.ndarray,
    x_test: np.ndarray,
    y_test: np.ndarray,
    client_indices: list[np.ndarray],
    schemas: list[ClientReadoutSchema],
    simulator: QuantumReadoutSimulator,
    n_observables: int,
    max_raw_dim: int,
    n_classes: int,
    rounds: int,
    participation: float,
    local_epochs: int,
    lr: float,
    reg: float,
    prox_mu: float,
    server_opt: str,
    server_lr: float,
    server_beta1: float,
    server_beta2: float,
    server_tau: float,
    feddyn_alpha: float,
    eval_shots: int,
    eval_every: int,
    seed: int,
    out_dir: Path,
) -> dict:
    rng = np.random.default_rng(seed)
    n_part = max(1, int(round(len(schemas) * participation)))
    w = np.zeros((n_classes, ctx.sketch.sketch_dim), dtype=np.float64)
    b = np.zeros((n_classes,), dtype=np.float64)
    m_w = np.zeros_like(w)
    m_b = np.zeros_like(b)
    v_w = np.zeros_like(w)
    v_b = np.zeros_like(b)
    scaffold_c_w = np.zeros_like(w)
    scaffold_c_b = np.zeros_like(b)
    scaffold_ci_w = np.zeros((len(schemas),) + w.shape, dtype=np.float64)
    scaffold_ci_b = np.zeros((len(schemas),) + b.shape, dtype=np.float64)
    dyn_h_w = np.zeros((len(schemas),) + w.shape, dtype=np.float64)
    dyn_h_b = np.zeros((len(schemas),) + b.shape, dtype=np.float64)
    client_sizes = np.asarray([max(1, len(idx)) for idx in client_indices], dtype=np.float64)
    client_alpha_all = client_sizes / (client_sizes.sum() + 1e-12)
    history = []
    start = time.time()

    for rnd in range(1, rounds + 1):
        participants = rng.choice(len(schemas), size=n_part, replace=False)
        ws = []
        bs = []
        weights = []
        scaffold_delta_c_w = []
        scaffold_delta_c_b = []
        for cid in participants:
            schema = schemas[int(cid)]
            idx = client_indices[int(cid)]
            u, _, _, _ = _measure_adapt_transform(
                x=x_train[idx],
                schema=schema,
                simulator=simulator,
                ctx=ctx,
                n_observables=n_observables,
                max_raw_dim=max_raw_dim,
                seed=seed + rnd * 5000 + int(cid),
            )
            control_w = None
            control_b = None
            local_dyn_h_w = None
            local_dyn_h_b = None
            if server_opt == "scaffold":
                control_w = scaffold_c_w - scaffold_ci_w[int(cid)]
                control_b = scaffold_c_b - scaffold_ci_b[int(cid)]
            elif server_opt == "feddyn":
                local_dyn_h_w = dyn_h_w[int(cid)]
                local_dyn_h_b = dyn_h_b[int(cid)]
            wi, bi = _train_softmax(
                u,
                y_train[idx],
                w,
                b,
                lr=lr,
                epochs=local_epochs,
                reg=reg,
                prox_mu=prox_mu,
                w_ref=w,
                b_ref=b,
                control_w=control_w,
                control_b=control_b,
                dyn_h_w=local_dyn_h_w,
                dyn_h_b=local_dyn_h_b,
                dyn_alpha=(feddyn_alpha if server_opt == "feddyn" else 0.0),
            )
            ws.append(wi)
            bs.append(bi)
            weights.append(float(len(idx)))
            if server_opt == "scaffold":
                step_scale = max(1.0, float(local_epochs) * float(lr))
                ci_w_new = scaffold_ci_w[int(cid)] - scaffold_c_w + (w - wi) / step_scale
                ci_b_new = scaffold_ci_b[int(cid)] - scaffold_c_b + (b - bi) / step_scale
                scaffold_delta_c_w.append(ci_w_new - scaffold_ci_w[int(cid)])
                scaffold_delta_c_b.append(ci_b_new - scaffold_ci_b[int(cid)])
                scaffold_ci_w[int(cid)] = ci_w_new
                scaffold_ci_b[int(cid)] = ci_b_new
        alpha = np.asarray(weights, dtype=np.float64)
        alpha = alpha / (alpha.sum() + 1e-12)
        avg_w = np.sum(np.stack(ws, axis=0) * alpha[:, None, None], axis=0)
        avg_b = np.sum(np.stack(bs, axis=0) * alpha[:, None], axis=0)
        if server_opt == "adam":
            delta_w = avg_w - w
            delta_b = avg_b - b
            m_w = server_beta1 * m_w + (1.0 - server_beta1) * delta_w
            m_b = server_beta1 * m_b + (1.0 - server_beta1) * delta_b
            v_w = server_beta2 * v_w + (1.0 - server_beta2) * delta_w * delta_w
            v_b = server_beta2 * v_b + (1.0 - server_beta2) * delta_b * delta_b
            mhat_w = m_w / (1.0 - server_beta1**rnd)
            mhat_b = m_b / (1.0 - server_beta1**rnd)
            vhat_w = v_w / (1.0 - server_beta2**rnd)
            vhat_b = v_b / (1.0 - server_beta2**rnd)
            w = w + server_lr * mhat_w / (np.sqrt(vhat_w) + server_tau)
            b = b + server_lr * mhat_b / (np.sqrt(vhat_b) + server_tau)
        elif server_opt == "scaffold":
            w = avg_w
            b = avg_b
            if scaffold_delta_c_w:
                scaffold_c_w += np.sum(np.stack(scaffold_delta_c_w, axis=0), axis=0) / max(1, len(schemas))
                scaffold_c_b += np.sum(np.stack(scaffold_delta_c_b, axis=0), axis=0) / max(1, len(schemas))
        elif server_opt == "feddyn":
            dyn_alpha_safe = max(float(feddyn_alpha), 1e-12)
            global_h_w = np.sum(dyn_h_w * client_alpha_all[:, None, None], axis=0)
            global_h_b = np.sum(dyn_h_b * client_alpha_all[:, None], axis=0)
            new_w = avg_w - global_h_w / dyn_alpha_safe
            new_b = avg_b - global_h_b / dyn_alpha_safe
            for j, cid in enumerate(participants):
                dyn_h_w[int(cid)] = dyn_h_w[int(cid)] - dyn_alpha_safe * (ws[j] - new_w)
                dyn_h_b[int(cid)] = dyn_h_b[int(cid)] - dyn_alpha_safe * (bs[j] - new_b)
            w = new_w
            b = new_b
        else:
            w = avg_w
            b = avg_b

        if rnd == 1 or rnd % eval_every == 0 or rnd == rounds:
            accs = []
            bals = []
            nlls = []
            for schema in schemas:
                u, _, _, _ = _measure_adapt_transform(
                    x=x_test,
                    schema=schema,
                    simulator=simulator,
                    ctx=ctx,
                    n_observables=n_observables,
                    max_raw_dim=max_raw_dim,
                    seed=seed + rnd * 6000 + schema.client_id,
                    shots=eval_shots,
                )
                logits = _softmax_logits(u, w, b)
                pred = np.argmax(logits, axis=1)
                accs.append(accuracy(y_test, pred))
                bals.append(balanced_accuracy(y_test, pred, n_classes))
                nlls.append(nll_from_logits(logits, y_test))
            rec = {
                "method": ctx.spec.name,
                "round": rnd,
                "acc": float(np.mean(accs)),
                "balanced_acc": float(np.mean(bals)),
                "nll": float(np.mean(nlls)),
            }
            history.append(rec)
            append_jsonl(out_dir / "history.jsonl", rec)

    final = history[-1]
    param_scalars = ctx.sketch.sketch_dim * n_classes + n_classes
    comm_multiplier = 2 if server_opt == "scaffold" else 1
    return {
        "method": ctx.spec.name,
        "final_acc": float(final["acc"]),
        "final_balanced_acc": float(final["balanced_acc"]),
        "distortion_proxy": 0.0,
        "class_gap_proxy": 0.0,
        "bytes_per_client_round": int(param_scalars * comm_multiplier * 4),
        "elapsed_sec": float(time.time() - start),
    }


def run_fedproto(
    *,
    ctx: MethodContext,
    x_train: np.ndarray,
    y_train: np.ndarray,
    x_test: np.ndarray,
    y_test: np.ndarray,
    client_indices: list[np.ndarray],
    schemas: list[ClientReadoutSchema],
    simulator: QuantumReadoutSimulator,
    n_observables: int,
    max_raw_dim: int,
    n_classes: int,
    rounds: int,
    participation: float,
    beta: float,
    proto_mu: float,
    eval_shots: int,
    eval_every: int,
    seed: int,
    out_dir: Path,
) -> dict:
    """FedProto-style low-order prototype aggregation on readout features.

    This baseline receives the same schema/RFF feature interface as QProto, but
    it does not transmit per-observable coverage counts or high-order sketches.
    The optional proto_mu term mimics FedProto's global-prototype regularizer by
    pulling local class prototypes toward the current global prototype.
    """
    rng = np.random.default_rng(seed)
    server = MomentServer(n_classes=n_classes, feature_dim=ctx.sketch.sketch_dim, beta=beta)
    history = []
    n_part = max(1, int(round(len(schemas) * participation)))
    start = time.time()

    for rnd in range(1, rounds + 1):
        participants = rng.choice(len(schemas), size=n_part, replace=False)
        locals_ = []
        for cid in participants:
            schema = schemas[int(cid)]
            idx = client_indices[int(cid)]
            u, _, _, sig = _measure_adapt_transform(
                x=x_train[idx],
                schema=schema,
                simulator=simulator,
                ctx=ctx,
                n_observables=n_observables,
                max_raw_dim=max_raw_dim,
                seed=seed + rnd * 8100 + int(cid),
            )
            ls = compute_local_stats(u, y_train[idx], n_classes=n_classes, shot_scalar=sig)
            if proto_mu > 0.0 and server.initialized:
                blend = float(np.clip(proto_mu, 0.0, 1.0))
                seen = (ls.counts > 0) & (server.counts > 1e-8)
                if np.any(seen):
                    proto = ls.prototypes.copy()
                    proto[seen] = (1.0 - blend) * proto[seen] + blend * server.prototypes[seen]
                    ls = type(ls)(counts=ls.counts, prototypes=proto, hop=ls.hop, shot_scalar=ls.shot_scalar)
            locals_.append(ls)
        info = server.update(locals_)

        if rnd == 1 or rnd % eval_every == 0 or rnd == rounds:
            ev = evaluate_server(
                server=server,
                ctx=ctx,
                x_test=x_test,
                y_test=y_test,
                schemas=schemas,
                simulator=simulator,
                n_observables=n_observables,
                max_raw_dim=max_raw_dim,
                n_classes=n_classes,
                seed=seed + rnd * 833,
                eval_shots=eval_shots,
            )
            rec = {
                "method": ctx.spec.name,
                "round": rnd,
                "acc": ev["acc"],
                "balanced_acc": ev["balanced_acc"],
                "class_gap_proxy": class_gap_proxy(server.prototypes, server.counts),
                "distortion_proxy": 0.0,
                **info,
            }
            history.append(rec)
            append_jsonl(out_dir / "history.jsonl", rec)

    final = history[-1] if history else {}
    return {
        "method": ctx.spec.name,
        "final_acc": float(final.get("acc", 0.0)),
        "final_balanced_acc": float(final.get("balanced_acc", 0.0)),
        "distortion_proxy": 0.0,
        "class_gap_proxy": float(final.get("class_gap_proxy", 0.0)),
        "bytes_per_client_round": communication_bytes(
            ctx.spec,
            n_classes=n_classes,
            sketch_dim=ctx.sketch.sketch_dim,
            hop_dim=0,
        ),
        "elapsed_sec": float(time.time() - start),
    }


def _evaluate_classical_server(
    *,
    server: MomentServer,
    ctx: MethodContext,
    x_test: np.ndarray,
    y_test: np.ndarray,
    n_classes: int,
) -> dict:
    u = ctx.sketch.transform(x_test)
    pred = server.predict(u)
    return {
        "acc": accuracy(y_test, pred),
        "balanced_acc": balanced_accuracy(y_test, pred, n_classes),
    }


def run_classical_kernel(
    *,
    ctx: MethodContext,
    x_train: np.ndarray,
    y_train: np.ndarray,
    x_test: np.ndarray,
    y_test: np.ndarray,
    client_indices: list[np.ndarray],
    n_classes: int,
    rounds: int,
    participation: float,
    beta: float,
    eval_every: int,
    seed: int,
    out_dir: Path,
) -> dict:
    """Classical kernel-FL baseline over original input features."""
    rng = np.random.default_rng(seed)
    server = MomentServer(n_classes=n_classes, feature_dim=ctx.sketch.sketch_dim, beta=beta)
    history = []
    n_part = max(1, int(round(len(client_indices) * participation)))
    start = time.time()

    for rnd in range(1, rounds + 1):
        participants = rng.choice(len(client_indices), size=n_part, replace=False)
        locals_ = []
        for cid in participants:
            idx = client_indices[int(cid)]
            u = ctx.sketch.transform(x_train[idx])
            locals_.append(compute_local_stats(u, y_train[idx], n_classes=n_classes))
        info = server.update(locals_)

        if rnd == 1 or rnd % eval_every == 0 or rnd == rounds:
            ev = _evaluate_classical_server(server=server, ctx=ctx, x_test=x_test, y_test=y_test, n_classes=n_classes)
            rec = {
                "method": ctx.spec.name,
                "round": rnd,
                "acc": ev["acc"],
                "balanced_acc": ev["balanced_acc"],
                "class_gap_proxy": class_gap_proxy(server.prototypes, server.counts),
                "distortion_proxy": 0.0,
                **info,
            }
            history.append(rec)
            append_jsonl(out_dir / "history.jsonl", rec)

    final = history[-1] if history else {}
    return {
        "method": ctx.spec.name,
        "final_acc": float(final.get("acc", 0.0)),
        "final_balanced_acc": float(final.get("balanced_acc", 0.0)),
        "distortion_proxy": 0.0,
        "class_gap_proxy": float(final.get("class_gap_proxy", 0.0)),
        "bytes_per_client_round": communication_bytes(
            ctx.spec,
            n_classes=n_classes,
            sketch_dim=ctx.sketch.sketch_dim,
            hop_dim=0,
        ),
        "elapsed_sec": float(time.time() - start),
    }


def run_centralized_kernel(
    *,
    ctx: MethodContext,
    x_train: np.ndarray,
    y_train: np.ndarray,
    x_test: np.ndarray,
    y_test: np.ndarray,
    n_classes: int,
) -> dict:
    """Centralized classical RFF prototype upper-bound reference."""
    start = time.time()
    u_train = ctx.sketch.transform(x_train)
    ls = compute_local_stats(u_train, y_train, n_classes=n_classes)
    server = MomentServer(n_classes=n_classes, feature_dim=ctx.sketch.sketch_dim, beta=0.0)
    server.update([ls])
    ev = _evaluate_classical_server(server=server, ctx=ctx, x_test=x_test, y_test=y_test, n_classes=n_classes)
    return {
        "method": ctx.spec.name,
        "final_acc": float(ev["acc"]),
        "final_balanced_acc": float(ev["balanced_acc"]),
        "distortion_proxy": 0.0,
        "class_gap_proxy": class_gap_proxy(server.prototypes, server.counts),
        "bytes_per_client_round": 0,
        "elapsed_sec": float(time.time() - start),
    }


def run_experiment(args: argparse.Namespace) -> dict:
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.dataset == "synthetic":
        dataset = make_synthetic_classification(
            n_train=args.n_train,
            n_test=args.n_test,
            input_dim=args.input_dim,
            n_classes=args.n_classes,
            class_sep=args.class_sep,
            structure=args.data_structure,
            cov_boost=args.cov_boost,
            seed=args.seed,
        )
    elif args.dataset == "digits":
        dataset = load_digits_dataset(
            n_train=args.n_train,
            n_test=args.n_test,
            n_classes=args.n_classes,
            test_fraction=args.test_fraction,
            seed=args.seed,
        )
    elif args.dataset == "npz":
        if not args.dataset_path:
            raise ValueError("--dataset-path is required when --dataset npz")
        dataset = load_npz_dataset(
            args.dataset_path,
            n_train=args.n_train,
            n_test=args.n_test,
            n_classes=args.n_classes,
            test_fraction=args.test_fraction,
            seed=args.seed,
        )
    else:
        raise ValueError(f"Unknown dataset: {args.dataset}")

    n_classes = dataset.n_classes
    input_dim = int(dataset.x_train.shape[1])
    client_indices = dirichlet_partition(
        dataset.y_train,
        n_clients=args.clients,
        alpha=args.dirichlet_alpha,
        seed=args.seed + 11,
    )
    shots_levels = parse_int_list(args.shots)
    schemas = make_client_schemas(
        n_clients=args.clients,
        n_observables=args.observables,
        obs_per_client=args.obs_per_client,
        overlap=args.observable_overlap,
        shots_levels=shots_levels,
        readout_p=args.readout_p,
        readout_std=args.readout_std,
        depol_p=args.depol_p,
        depol_std=args.depol_std,
        depth_min=args.depth_min,
        depth_max=args.depth_max,
        common_policy=args.common_policy,
        seed=args.seed + 23,
    )
    max_raw_dim = max(s.n_local for s in schemas)
    shared_keys = np.array(
        sorted(set(schemas[0].local_to_global.tolist()).intersection(*(set(s.local_to_global.tolist()) for s in schemas[1:]))),
        dtype=np.int64,
    )
    if args.readout_backend == "precomputed":
        simulator = PrecomputedReadoutSimulator(
            input_dim=input_dim,
            n_observables=args.observables,
            seed=args.seed + 31,
            shot_noise_scale=args.shot_noise_scale,
        )
    else:
        simulator = QuantumReadoutSimulator(
            input_dim=input_dim,
            n_observables=args.observables,
            seed=args.seed + 31,
            shot_noise_scale=args.shot_noise_scale,
        )
    anchor_x = make_public_anchor_set(dataset.x_train, args.anchor_size, seed=args.seed + 41)
    probe_x = make_public_anchor_set(dataset.x_test, min(args.probe_size, len(dataset.x_test)), seed=args.seed + 43)

    method_names = DEFAULT_METHODS if args.methods == "all" else [m.strip() for m in args.methods.split(",") if m.strip()]
    unknown = [m for m in method_names if m not in METHODS]
    if unknown:
        raise ValueError(f"Unknown methods: {unknown}. Available: {sorted(METHODS)}")

    save_json(out_dir / "config.json", vars(args))
    save_json(
        out_dir / "dataset_info.json",
        {
            "dataset": args.dataset,
            "n_train": int(len(dataset.y_train)),
            "n_test": int(len(dataset.y_test)),
            "input_dim": input_dim,
            "n_classes": n_classes,
        },
    )
    save_json(out_dir / "schemas.json", [dict(asdict(s), local_to_global=s.local_to_global.tolist()) for s in schemas])

    correct_ctx = _build_context(
        spec=METHODS["qproto_hop"],
        anchor_x=anchor_x,
        schemas=schemas,
        simulator=simulator,
        n_observables=args.observables,
        max_raw_dim=max_raw_dim,
        sketch_dim=args.sketch_dim,
        hop_dim=args.hop_dim,
        bandwidth=args.bandwidth,
        anchor_normalize=args.anchor_normalize,
        wrong_shift=args.wrong_shift,
        shared_keys=shared_keys,
        compressed_observables=args.compressed_observables,
        compressed_key_policy=args.compressed_key_policy,
        seed=args.seed + 101,
    )

    summaries = []
    for method_name in method_names:
        spec = METHODS[method_name]
        if spec.kind in {"classical", "centralized"}:
            ctx = _build_classical_context(
                spec=spec,
                anchor_x=anchor_x,
                input_dim=input_dim,
                sketch_dim=args.classical_sketch_dim,
                bandwidth=args.classical_bandwidth,
                anchor_normalize=args.anchor_normalize,
                seed=args.seed + 131,
            )
        else:
            ctx = _build_context(
                spec=spec,
                anchor_x=anchor_x,
                schemas=schemas,
                simulator=simulator,
                n_observables=args.observables,
                max_raw_dim=max_raw_dim,
                sketch_dim=args.sketch_dim,
                hop_dim=args.hop_dim,
                bandwidth=args.bandwidth,
                anchor_normalize=args.anchor_normalize,
                wrong_shift=args.wrong_shift,
                shared_keys=shared_keys,
                compressed_observables=args.compressed_observables,
                compressed_key_policy=args.compressed_key_policy,
                seed=args.seed + 101,
            )
        if spec.kind == "local":
            summary = run_local_only(
                ctx=ctx,
                x_train=dataset.x_train,
                y_train=dataset.y_train,
                x_test=dataset.x_test,
                y_test=dataset.y_test,
                client_indices=client_indices,
                schemas=schemas,
                simulator=simulator,
                n_observables=args.observables,
                max_raw_dim=max_raw_dim,
                n_classes=n_classes,
                eval_shots=args.eval_shots,
                seed=args.seed + 300,
            )
        elif spec.kind == "quantum_centralized":
            summary = run_centralized_qproto(
                ctx=ctx,
                x_train=dataset.x_train,
                y_train=dataset.y_train,
                x_test=dataset.x_test,
                y_test=dataset.y_test,
                client_indices=client_indices,
                schemas=schemas,
                simulator=simulator,
                n_observables=args.observables,
                max_raw_dim=max_raw_dim,
                n_classes=n_classes,
                hop_weight=args.hop_weight,
                rounds=args.rounds,
                beta=args.ema_beta,
                c_shot=args.c_shot,
                eval_shots=args.eval_shots,
                seed=args.seed + 350,
            )
        elif spec.kind in {"fedavg", "fedprox", "fedadam", "scaffold", "feddyn"}:
            summary = run_fedavg_head(
                ctx=ctx,
                x_train=dataset.x_train,
                y_train=dataset.y_train,
                x_test=dataset.x_test,
                y_test=dataset.y_test,
                client_indices=client_indices,
                schemas=schemas,
                simulator=simulator,
                n_observables=args.observables,
                max_raw_dim=max_raw_dim,
                n_classes=n_classes,
                rounds=args.rounds,
                participation=args.participation,
                local_epochs=args.local_epochs,
                lr=args.lr,
                reg=args.reg,
                prox_mu=(args.fedprox_mu if spec.kind == "fedprox" else 0.0),
                server_opt=(
                    "adam"
                    if spec.kind == "fedadam"
                    else ("scaffold" if spec.kind == "scaffold" else ("feddyn" if spec.kind == "feddyn" else "avg"))
                ),
                server_lr=args.server_lr,
                server_beta1=args.fedopt_beta1,
                server_beta2=args.fedopt_beta2,
                server_tau=args.fedopt_tau,
                feddyn_alpha=args.feddyn_alpha,
                eval_shots=args.eval_shots,
                eval_every=args.eval_every,
                seed=args.seed + 400,
                out_dir=out_dir / method_name,
            )
        elif spec.kind == "fedproto":
            summary = run_fedproto(
                ctx=ctx,
                x_train=dataset.x_train,
                y_train=dataset.y_train,
                x_test=dataset.x_test,
                y_test=dataset.y_test,
                client_indices=client_indices,
                schemas=schemas,
                simulator=simulator,
                n_observables=args.observables,
                max_raw_dim=max_raw_dim,
                n_classes=n_classes,
                rounds=args.rounds,
                participation=args.participation,
                beta=args.ema_beta,
                proto_mu=args.fedproto_mu,
                eval_shots=args.eval_shots,
                eval_every=args.eval_every,
                seed=args.seed + 410,
                out_dir=out_dir / method_name,
            )
        elif spec.kind == "masked":
            summary = run_masked_method(
                ctx=ctx,
                x_train=dataset.x_train,
                y_train=dataset.y_train,
                x_test=dataset.x_test,
                y_test=dataset.y_test,
                client_indices=client_indices,
                schemas=schemas,
                simulator=simulator,
                n_observables=args.observables,
                max_raw_dim=max_raw_dim,
                n_classes=n_classes,
                rounds=args.rounds,
                participation=args.participation,
                beta=args.ema_beta,
                hop_weight=args.hop_weight,
                c_shot=args.c_shot,
                eval_every=args.eval_every,
                eval_shots=args.eval_shots,
                seed=args.seed + 425,
                out_dir=out_dir / method_name,
            )
        elif spec.kind == "classical":
            summary = run_classical_kernel(
                ctx=ctx,
                x_train=dataset.x_train,
                y_train=dataset.y_train,
                x_test=dataset.x_test,
                y_test=dataset.y_test,
                client_indices=client_indices,
                n_classes=n_classes,
                rounds=args.rounds,
                participation=args.participation,
                beta=args.ema_beta,
                eval_every=args.eval_every,
                seed=args.seed + 450,
                out_dir=out_dir / method_name,
            )
        elif spec.kind == "centralized":
            summary = run_centralized_kernel(
                ctx=ctx,
                x_train=dataset.x_train,
                y_train=dataset.y_train,
                x_test=dataset.x_test,
                y_test=dataset.y_test,
                n_classes=n_classes,
            )
        else:
            summary = run_stats_method(
                ctx=ctx,
                correct_ctx=correct_ctx,
                x_train=dataset.x_train,
                y_train=dataset.y_train,
                x_test=dataset.x_test,
                y_test=dataset.y_test,
                client_indices=client_indices,
                schemas=schemas,
                simulator=simulator,
                n_observables=args.observables,
                max_raw_dim=max_raw_dim,
                n_classes=n_classes,
                rounds=args.rounds,
                participation=args.participation,
                beta=args.ema_beta,
                hop_weight=args.hop_weight,
                c_shot=args.c_shot,
                eval_every=args.eval_every,
                eval_shots=args.eval_shots,
                probe_x=probe_x,
                seed=args.seed + 500,
                out_dir=out_dir / method_name,
            )
        summaries.append(summary)
        save_json(out_dir / method_name / "metrics.json", summary)
        print(
            f"{method_name:>18} | acc={summary['final_acc']:.4f} "
            f"bal={summary['final_balanced_acc']:.4f} bytes={summary['bytes_per_client_round']}",
            flush=True,
        )

    result = {"summaries": summaries}
    save_json(out_dir / "metrics.json", result)
    return result


def build_argparser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser("QProto-HOP simulated heterogeneous-readout experiments")
    p.add_argument("--out", type=str, default="runs/smoke")
    p.add_argument("--methods", type=str, default="all")
    p.add_argument("--seed", type=int, default=0)

    p.add_argument("--dataset", type=str, default="synthetic", choices=["synthetic", "digits", "npz"])
    p.add_argument("--dataset-path", type=str, default="")
    p.add_argument("--test-fraction", type=float, default=0.25)
    p.add_argument("--n-train", type=int, default=2400)
    p.add_argument("--n-test", type=int, default=1000)
    p.add_argument("--input-dim", type=int, default=12)
    p.add_argument("--n-classes", type=int, default=4)
    p.add_argument("--class-sep", type=float, default=2.2)
    p.add_argument("--data-structure", type=str, default="mean", choices=["mean", "covariance", "hybrid"])
    p.add_argument("--cov-boost", type=float, default=2.5)
    p.add_argument("--readout-backend", type=str, default="synthetic", choices=["synthetic", "precomputed"])

    p.add_argument("--clients", type=int, default=20)
    p.add_argument("--participation", type=float, default=0.4)
    p.add_argument("--dirichlet-alpha", type=float, default=0.25)

    p.add_argument("--observables", type=int, default=64)
    p.add_argument("--obs-per-client", type=int, default=24)
    p.add_argument("--observable-overlap", type=float, default=0.35)
    p.add_argument("--common-policy", type=str, default="random", choices=["random", "prefix", "suffix"])
    p.add_argument("--shots", type=str, default="32,64,128,256,1024")
    p.add_argument("--eval-shots", type=int, default=1024)
    p.add_argument("--shot-noise-scale", type=float, default=1.0)
    p.add_argument("--readout-p", type=float, default=0.03)
    p.add_argument("--readout-std", type=float, default=0.015)
    p.add_argument("--depol-p", type=float, default=0.02)
    p.add_argument("--depol-std", type=float, default=0.01)
    p.add_argument("--wrong-shift", type=int, default=7)
    p.add_argument("--depth-min", type=int, default=2)
    p.add_argument("--depth-max", type=int, default=8)

    p.add_argument("--sketch-dim", type=int, default=64)
    p.add_argument("--hop-dim", type=int, default=24)
    p.add_argument("--bandwidth", type=float, default=5.0)
    p.add_argument("--compressed-observables", type=int, default=0)
    p.add_argument(
        "--compressed-key-policy",
        type=str,
        default="variance",
        choices=["variance", "coverage", "random", "prefix", "suffix"],
    )
    p.add_argument("--classical-sketch-dim", type=int, default=64)
    p.add_argument("--classical-bandwidth", type=float, default=5.0)
    p.add_argument("--anchor-size", type=int, default=64)
    p.add_argument("--anchor-normalize", action="store_true")
    p.add_argument("--probe-size", type=int, default=96)

    p.add_argument("--rounds", type=int, default=25)
    p.add_argument("--eval-every", type=int, default=5)
    p.add_argument("--ema-beta", type=float, default=0.6)
    p.add_argument("--hop-weight", type=float, default=0.12)
    p.add_argument("--c-shot", type=float, default=3.0)

    p.add_argument("--local-epochs", type=int, default=3)
    p.add_argument("--lr", type=float, default=0.25)
    p.add_argument("--reg", type=float, default=1e-3)
    p.add_argument("--fedprox-mu", type=float, default=0.05)
    p.add_argument("--server-lr", type=float, default=0.25)
    p.add_argument("--fedopt-beta1", type=float, default=0.9)
    p.add_argument("--fedopt-beta2", type=float, default=0.99)
    p.add_argument("--fedopt-tau", type=float, default=1e-3)
    p.add_argument("--fedproto-mu", type=float, default=0.1)
    p.add_argument("--feddyn-alpha", type=float, default=0.02)
    return p


def main() -> None:
    args = build_argparser().parse_args()
    run_experiment(args)


if __name__ == "__main__":
    main()


