# Model Run Guide (SLM/SEM/SAM + GRF)

**실행 위치**: 프로젝트 루트(`1최종_LH/`)에서 실행하는 것을 권장합니다.  
- CSV 입력 기본값: `data/통합_데이터/격자_최종통합.csv`  
- 출력 기본 디렉터리: `outputs/` (필요 시 `--out-dir data/통합_데이터` 등으로 변경 가능)

---

## 1) Spatial dependence models (policy explanation)

- Full data, acc_count target
`python scripts/run_spatial_models.py --target acc_count --k 8 --sample-n 0`

- Full data, ARI target
`python scripts/run_spatial_models.py --target ARI --k 8 --sample-n 0`

Outputs:
- `outputs/spatial_summary_acc_count.csv`
- `outputs/spatial_coefs_acc_count.csv`
- `outputs/spatial_summary_ARI.csv`
- `outputs/spatial_coefs_ARI.csv`

Interpretation:
- `rho` (SLM/SAM): spatial lag dependence strength
- `lambda` (SEM/SAM): spatial error dependence strength
- Compare `r2`, `rmse`, `resid_spatial_corr`

## 2) GRF-like ranking model (execution/accuracy)

- Full data, acc_count target
`python scripts/run_grf_ranking.py --target acc_count --n-estimators 500 --max-depth 18`

- Full data, ARI target
`python scripts/run_grf_ranking.py --target ARI --n-estimators 500 --max-depth 18`

Outputs:
- `outputs/grf_ranking_acc_count.csv`
- `outputs/grf_feature_importance_acc_count.csv`
- `outputs/grf_metrics_acc_count.csv`
- `outputs/grf_ranking_ARI.csv`
- `outputs/grf_feature_importance_ARI.csv`
- `outputs/grf_metrics_ARI.csv`

Ranking column:
- `rank_desc = 1` is highest predicted risk (highest priority)

## Notes
- This SLM/SEM/SAM implementation is an approximation without PySAL.
- For publication-grade inference (SE/p-values), rerun with `libpysal` + `spreg`.
