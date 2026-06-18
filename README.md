# QProto: Protocol-Defined Semantic Fusion for Heterogeneous and Incomplete Source Coordinates

This repository contains the reproducibility package for the manuscript:

**Protocol-Defined Semantic Fusion for Heterogeneous and Incomplete Source Coordinates**

QProto studies heterogeneous source-coordinate fusion: distributed sources may expose different coordinate subsets, local orders, missing views, noise levels, or measurement budgets. The code implements schema-bound value-mask records, coverage-aware CProto/KME aggregation, group-balanced source-coordinate fusion, and optional CHOP high-order interaction sketches.

## Repository contents

- `qprotohop/` - core implementation.
- `scripts/` - experiment, plotting, table-export, and dataset-preparation scripts.
- `runs/` - selected result summaries, seed-level records, payload accounting, and configuration snapshots used by the manuscript tables.
- `data/` - dataset notes and download/preprocessing pointers. Public datasets are not redistributed here unless permitted.
- `manuscript/latex_qproto_hop_IF/` - LaTeX source snapshot for the submitted manuscript and supplement.
- `QProto_IF_Manuscript.pdf` and `QProto_IF_Supplement.pdf` - submitted manuscript PDFs for reference.
- `QProto_IF_Cached_Feature_Checksums.csv` and `MANIFEST.sha256` - checksum records.

## Quick start

Create a clean Python environment and install the dependencies:

```bash
python -m venv .venv
. .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Run the package smoke test:

```bash
python -m qprotohop --help
```

Regenerate representative tables and figures from the included result summaries:

```bash
python scripts/export_latex_tables.py
python scripts/plot_if_main_overview.py
python scripts/plot_adaptive_chop_summary.py
```

Dataset-specific preprocessing scripts are provided in `scripts/` and documented in `DATASETS.md`.

## Reproducibility notes

The repository is organized to support review-time reproducibility without redistributing third-party datasets. Public datasets should be downloaded from their original sources, then processed with the scripts in this repository. Cached feature checksums and selected result summaries are included to verify the manuscript artifacts.

The experiments separate three comparison families:

1. diagnostic controls such as no-schema, zero-fill, mask-only, and shared-view aggregation;
2. communication-matched compact statistics such as CProto, group-balanced CProto, CHOP, and adaptive CHOP;
3. full-dimensional trainable boundary references such as HeMIS-style fusion and mask-aware MLPs.

## Citation

If you use this code, please cite the manuscript and this repository. A `CITATION.cff` file is included.

## License

Code in this repository is released under the MIT License. Dataset licenses remain with the original dataset providers.
