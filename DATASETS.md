# Dataset Notes

This repository does not redistribute third-party datasets unless redistribution is explicitly permitted. Use the original dataset providers and the preparation scripts in `scripts/`.

## Public datasets used in the manuscript

- MNIST / Fashion-MNIST / CIFAR-10 feature-readout experiments: download through standard torchvision-compatible sources or regenerate cached features using the provided scripts.
- UCI HAR: public smartphone-sensor activity dataset from the UCI Machine Learning Repository.
- UCI Multiple Features: public multi-view handwritten digit dataset from the UCI Machine Learning Repository.
- MHEALTH: public mobile health monitoring dataset.
- PAMAP2: public physical activity monitoring dataset.
- Hydraulic Systems: public industrial condition monitoring dataset.
- WDBC: public Wisconsin Diagnostic Breast Cancer dataset.
- Gas Drift: retained as a boundary-check dataset in the development scripts.

## Checksums

`QProto_IF_Cached_Feature_Checksums.csv` records checksums for cached features and selected artifacts used in the manuscript pipeline. `MANIFEST.sha256` records files included in this repository snapshot.

## Notes for reviewers

The manuscript's main claims rely on protocol-level comparisons under matched payloads and source-coordinate heterogeneity. Full-dimensional learned baselines are included as boundary references, not as communication-matched competitors.
