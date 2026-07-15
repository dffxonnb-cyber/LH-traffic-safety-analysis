# Verification Guide

This repository separates public-safe verification from full competition-data reproduction. The public repo is designed to let reviewers inspect the canonical model and score decisions, validation summary, dashboard fallback behavior, selected review artifacts, and evidence boundaries without requiring private or restricted raw data.

## Verification Scope

| Area | Publicly Verifiable | Notes |
| --- | --- | --- |
| Canonical model·score·pipeline scope | Yes | `docs/canonical_project_scope.md` freezes the final model name, score roles, core pipeline, legacy paths, and `needs confirmation` policy. |
| Dashboard public-safe mode | Yes | Smoke tests confirm the dashboard does not require private data to import. |
| Public visuals | Yes | Tests confirm required public-safe visuals exist. |
| Public Top-20 source match | Yes | Tests compare `public_top20_priority.csv` against the first 20 rows of tracked `gyosan_effect_reduction_by_gid.csv`. |
| Public ranking integrity | Yes | Tests check rank sequence, unique grid IDs, descending normalized scores, and the field-review claim boundary. |
| Validation summary | Yes | `docs/reproducibility_and_validation.md` documents TOP35 and transfer validation evidence. |
| Public evidence audit | Yes | `docs/evidence_audit.md` separates confirmed public artifacts, diagnostics, `needs confirmation`, and not-available evidence. |
| Full spatial-coordinate Random Forest and grid pipeline | No | Original competition/source data and the full model-to-public-score lineage are excluded. |

## Local Verification

```bash
pip install -r dashboard/requirements.txt
python -m compileall dashboard scripts
python scripts/build_portfolio_evidence.py
python -m unittest discover -s tests -p "test_*.py"
git diff --exit-code -- \
  docs/data/public_top20_priority.csv \
  docs/data/public_evidence_status.csv \
  docs/images/portfolio-performance-summary.svg \
  docs/images/portfolio-validation-summary.svg \
  docs/images/portfolio-score-comparison-note.svg \
  docs/images/public-top20-priority-preview.svg
```

Review the canonical and validation docs:

```text
docs/canonical_project_scope.md
docs/evidence_audit.md
docs/reproducibility_and_validation.md
docs/field-review-handoff.md
docs/grf_risk_methodology.md
docs/risk_index_methodology.md
```

## CI Verification

GitHub Actions runs the same public-safe sequence:

1. install dashboard dependencies
2. compile public Python entry points
3. rebuild public portfolio evidence
4. run dashboard and evidence tests
5. fail if regenerated evidence differs from committed artifacts

## Data Boundary

- Raw competition data, large geospatial files, and most generated analysis outputs are intentionally excluded.
- The repository keeps public documentation, images, dashboard fallback logic, public evidence audit, and small review CSVs.
- `scripts/run_grf_ranking.py` confirms the canonical estimator implementation, but full numeric reproduction requires the original source data.
- The public ranking source is tracked, but the full `pred_risk` → `RiskScore_A_grid` lineage remains `needs confirmation`.
- `07_gyosan_priority_ranking.ipynb` and `09_facility_site_selection.ipynb` are auxiliary paths and are not treated as the canonical public ranking.

## Known Limits

- CI does not rerun the full spatial-coordinate Random Forest model.
- CI does not recreate private-data LORO fold files or run-level Monte Carlo outputs.
- Public tests verify safe import, artifact generation, source consistency, rank integrity, and claim boundaries—not model retraining.
- Field inspection and accident-reduction impact are not available.
- The canonical scope, validation document, and public evidence audit are the main evidence sources for model-quality and evidence-boundary claims.
