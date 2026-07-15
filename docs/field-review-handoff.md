# Field Review Handoff Guide

This document explains how to read the public Top-20 ranking as a field-review handoff artifact. The ranking is a public-safe review signal for 100m grid candidates, not a final facility installation decision.

The frozen model, score, pipeline, and evidence scope are defined in [canonical_project_scope.md](canonical_project_scope.md).

## What the Risk Ranking Is For

The risk ranking helps reviewers decide which 100m grid candidates should be checked first. It is intended to support a field-review workflow where model signals, public context, and local knowledge are reviewed together before any real decision.

Use the ranking as:

- A field-review priority signal
- A way to compare candidate grids under the same public scoring baseline
- A handoff artifact for site validation and stakeholder review
- A starting point for checking whether the public risk signal matches local conditions

Do not use the ranking as:

- Proof that accidents will be reduced
- A direct recommendation to install a facility
- A replacement for site inspection, engineering review, budget review, regulation review, or local stakeholder review

## Canonical Public Ranking

The public Top-20 preview is generated from the tracked `docs/data/gyosan_effect_reduction_by_gid.csv` artifact.

- review score: `RiskScore_A_norm_grid`
- review order: `grid_rank`
- generated table: `docs/data/public_top20_priority.csv`

The `우선순위_점수` produced by `07_gyosan_priority_ranking.ipynb` and the k-scenario site selections produced by `09_facility_site_selection.ipynb` are auxiliary legacy paths. Their recorded candidates differ from the current public Top-20, so they must not be presented as the same final ranking.

The public repository does not contain the full private-data lineage needed to regenerate `RiskScore_A_grid` from the final model. Therefore the public ranking is a confirmed artifact, while the full model-to-public-score lineage remains `needs confirmation`.

## How to Read the Public Top-20 Preview

The public Top-20 preview shows candidate grid rankings and normalized risk scores from public-safe artifacts. It does not disclose private field records or claim that a listed grid is ready for installation.

When reading the preview:

- Treat rank as review order, not final priority approval.
- Treat normalized risk score as a signal for comparison, not a causal explanation.
- Treat facility package and recommendation reason fields marked `needs confirmation` as deliberately excluded from the final public claim.
- Compare nearby candidates under the same baseline before selecting any site for further review.
- Use the output as a handoff into professional and local review, not as an automated decision.

Related public artifacts:

- [Canonical project scope](canonical_project_scope.md)
- [Public Top-20 preview image](images/public-top20-priority-preview.svg)
- [Public Top-20 CSV](data/public_top20_priority.csv)
- [Public evidence audit](evidence_audit.md)
- [Reproducibility and validation guide](reproducibility_and_validation.md)

## Field Review Checklist

Before any real-world decision, a reviewer should re-check at least the following items:

- Road geometry check
- Nearby school, transit, and pedestrian context
- Recent accident or complaint records
- Field visibility and crossing conditions
- Existing safety facilities
- Budget and regulation constraints
- Local stakeholder review
- Post-installation monitoring requirement

The checklist is intentionally conservative. It helps convert a model-ranked candidate into a reviewable field package, but it does not replace professional engineering, administrative, legal, budget, or on-site validation.

## What a Field Reviewer Should Re-check

For each candidate grid, reviewers should confirm whether the public risk signal is still meaningful under current local conditions. Suggested re-check questions include:

- Is the road geometry consistent with the risk interpretation?
- Are schools, transit stops, crosswalks, pedestrian desire lines, or senior/child facilities nearby?
- Have recent accidents, near-miss reports, civil complaints, or construction changes shifted the local context?
- Are visibility, lighting, curb conditions, crossing distance, and driver sightlines consistent with the signal?
- Are there already speed-control, crossing, signage, lighting, or separation facilities in place?
- Are there regulation, right-of-way, maintenance, or budget constraints that limit feasible interventions?
- Have district offices, local residents, schools, transit operators, or other stakeholders reviewed the candidate?
- If an intervention is later approved, how will post-installation monitoring be defined?

## What the Project Does Not Prove

This project does not prove that a listed candidate will experience accident reduction. It does not prove causality, final site suitability, construction feasibility, or budget priority. It also does not prove that any specific facility should be installed at a specific location.

The model output is best understood as a public-safe field-review priority signal. Any real facility decision would require separate site validation, engineering review, budget approval, regulation review, stakeholder coordination, and post-installation monitoring.

## Claim Boundary

For portfolio and reviewer use, the safe claim is:

> This project turns public-safe 100m grid risk signals into a ranked field-review handoff, so reviewers can inspect high-signal candidates, compare them under a common baseline, and document what must be validated before any real-world action.

The project does not claim:

- Accident reduction
- Causal impact
- Final facility installation decisions
- Budget allocation decisions
- Legal, administrative, or engineering approval
- Completed site validation
