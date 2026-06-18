from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
from torchvision.datasets import FashionMNIST, MNIST


DATASETS = {
    "mnist": MNIST,
    "fashion_mnist": FashionMNIST,
}


def main() -> None:
    ap = argparse.ArgumentParser("Export cached torchvision datasets to QProto-HOP npz files")
    ap.add_argument("--root", type=str, default="data/torchvision")
    ap.add_argument("--out-dir", type=str, default="data")
    ap.add_argument("--dataset", type=str, choices=sorted(DATASETS), required=True)
    ap.add_argument("--download", action="store_true")
    args = ap.parse_args()

    cls = DATASETS[args.dataset]
    train = cls(root=args.root, train=True, download=args.download)
    test = cls(root=args.root, train=False, download=args.download)

    xtr = train.data.numpy().astype(np.float32).reshape(len(train), -1) / 255.0
    ytr = train.targets.numpy().astype(np.int64)
    xte = test.data.numpy().astype(np.float32).reshape(len(test), -1) / 255.0
    yte = test.targets.numpy().astype(np.int64)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"{args.dataset}.npz"
    np.savez_compressed(out, xtr=xtr, ytr=ytr, xte=xte, yte=yte)
    print(f"Wrote {out} with train={xtr.shape}, test={xte.shape}")


if __name__ == "__main__":
    main()

