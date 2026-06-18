# Reproduction Guide

## 1. Environment

Install the dependencies:

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
```

On Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## 2. Verify included result summaries

```bash
python scripts/export_latex_tables.py
python scripts/plot_if_main_overview.py
python scripts/plot_adaptive_chop_summary.py
```

These scripts use included `runs/` summaries and regenerate manuscript-style tables and figures.

## 3. Regenerate dataset-dependent experiments

Download datasets using the provider links described in `DATASETS.md`, then run the corresponding preparation and experiment scripts in `scripts/`.

Representative examples:

```bash
python scripts/prepare_real_image_features.py --help
python scripts/run_real_dataset_seeds.py --help
python scripts/run_adaptive_chop_ablation.py --help
```

Some backend compatibility checks require optional packages such as Qiskit Aer or PennyLane.

## 4. Payload and fairness checks

The manuscript reports communication-matched compact comparisons. Use:

```bash
python scripts/audit_experiment_fairness.py
python scripts/audit_if_results.py
```

These scripts summarize payload accounting, baseline families, and consistency checks.
