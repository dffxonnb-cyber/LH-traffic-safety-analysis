# TOP35 Upgrade Report

## 1) Input Discovery
- 4-region integrated CSV: `C:/Users/a0109/.jupyter/1최종_LH/data/통합_데이터/격자_최종통합.csv`
- 4-region grid geojson: `C:/Users/a0109/.jupyter/1최종_LH/data/격자_데이터/01._격자_(4개_시·구).geojson`
- Gyosan priority CSV: `C:/Users/a0109/.jupyter/1최종_LH/data/통합_데이터/하남교산_설치우선순위_격자.csv`
- Robustness reference top20 CSV: `C:/Users/a0109/.jupyter/1최종_LH/data/통합_데이터/hanam_gyosan_safety_site_selected_k20.csv`
- Blueprint source top20 CSV: `C:/Users/a0109/.jupyter/1최종_LH/data/통합_데이터/hanam_gyosan_combined_selected.csv`

## 2) Transfer Validation (Leave-One-Region-Out)
- Mean AUC across holdout regions: **0.8604**
- Mean top-10% lift: **4.39x**
- Worst holdout region: **서울특별시 송파구** (AUC=0.7979)

## 3) Feature Stability
Top stable drivers (high mean importance and high top3_rate):
- AADT_mean: mean_importance=0.2984, top3_rate=1.00
- velocity_mean: mean_importance=0.2251, top3_rate=1.00
- TI_mean: mean_importance=0.1492, top3_rate=0.62

## 4) Gyosan Selection Robustness (Coverage-Based)
- Best deterministic sensitivity scenario: **risk60_flow40** (Jaccard=0.538, coverage=0.668)
- Monte Carlo mean Jaccard vs current top20: **0.503**
- Share of current top20 in `very_high` confidence tier: **5.0%**

## 5) Actionable Top20 Blueprint
- `recommended_package` and `recommendation_reason` columns are ready for slides.
- Use this table for Q&A when asked: why this facility at this location?

## 6) Suggested Slide Tie-in
- Validation slide: transfer_loro_detail + transfer_loro_summary
- Robustness slide: gyosan_mc_runs + gyosan_scenario_sensitivity
- Execution slide: gyosan_top20_facility_blueprint