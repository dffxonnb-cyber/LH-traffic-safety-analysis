# Verification Guide

This repository separates public-safe verification from full competition-data reproduction. The public repo is designed to let reviewers inspect the method, validation summary, dashboard fallback behavior, selected review artifacts, and evidence boundaries without requiring private or restricted raw data.

## Verification Scope

| Area | Publicly Verifiable | Notes |
| --- | --- | --- |
| Dashboard public-safe mode | Yes | Smoke tests confirm the dashboard does not require private data to import. |
| Public visuals | Yes | Tests confirm required public-safe visuals exist. |
| Validation summary | Yes | `docs/reproducibility_and_validation.md` documents TOP35 and transfer validation evidence. |
| Public evidence audit | Yes | `docs/evidence_audit.md` separates confirmed public artifacts, `needs confirmation`, and not-available evidence. |
| Review CSV | Yes | `docs/data/gyosan_effect_reduction_by_gid.csv` is tracked for inspection. |
| Full spatial-coordinate Random Forest and grid pipeline | No | Original competition/source data is excluded. |

## Local Verification

```bash
pip install -r dashboard/requirements.txt
python scripts/build_portfolio_evidence.py
python -m unittest discover -s tests -p "test_*.py"
```

Review the validation docs:

```bash
docs/evidence_audit.md
docs/reproducibility_and_validation.md
docs/grf_risk_methodology.md
docs/risk_index_methodology.md
```

## CI Verification

GitHub Actions runs:

```bash
pip install -r dashboard/requirements.txt
python scripts/build_portfolio_evidence.py
python -m unittest discover -s tests -p "test_*.py"
```

## Data Boundary

- Raw competition data, large geospatial files, and generated analysis outputs are intentionally excluded.
- The repository keeps public documentation, images, dashboard fallback logic, public evidence audit, and small review CSVs.
- Full numeric reproduction requires the original source data and notebook pipeline described in `analysis_pipeline/`.

## Known Limits

- CI does not rerun the full spatial-coordinate Random Forest model.
- Public tests verify safe import/render assumptions, not model retraining.
- The validation document and public evidence audit are the main evidence sources for model-quality and evidence-boundary claims.
