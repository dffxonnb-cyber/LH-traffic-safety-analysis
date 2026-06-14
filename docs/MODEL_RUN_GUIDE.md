# 모델 실행 가이드 (SLM/SEM/SAM + 공간 좌표 포함 Random Forest)

**실행 위치**: 프로젝트 루트(`1최종_LH/`)에서 실행하는 것을 권장합니다.  
- CSV 입력 기본값: `data/통합_데이터/격자_최종통합.csv`  
- 출력 기본 디렉터리: `outputs/` (필요하면 `--out-dir data/통합_데이터`처럼 변경 가능)

---

## 1) 공간 의존성 모델 실행

- 전체 데이터, `acc_count` 예측
`python scripts/run_spatial_models.py --target acc_count --k 8 --sample-n 0`

- 전체 데이터, `ARI` 예측
`python scripts/run_spatial_models.py --target ARI --k 8 --sample-n 0`

출력 파일:
- `outputs/spatial_summary_acc_count.csv`
- `outputs/spatial_coefs_acc_count.csv`
- `outputs/spatial_summary_ARI.csv`
- `outputs/spatial_coefs_ARI.csv`

해석 포인트:
- `rho` (SLM/SAM): 공간 시차 의존 강도
- `lambda` (SEM/SAM): 공간 오차 의존 강도
- `r2`, `rmse`, `resid_spatial_corr`를 함께 비교

## 2) 공간 좌표 포함 Random Forest 우선순위 모델 실행

- 전체 데이터, `acc_count` 예측
`python scripts/run_grf_ranking.py --target acc_count --n-estimators 500 --max-depth 18`

- 전체 데이터, `ARI` 예측
`python scripts/run_grf_ranking.py --target ARI --n-estimators 500 --max-depth 18`

출력 파일:
- `outputs/grf_ranking_acc_count.csv`
- `outputs/grf_feature_importance_acc_count.csv`
- `outputs/grf_metrics_acc_count.csv`
- `outputs/grf_ranking_ARI.csv`
- `outputs/grf_feature_importance_ARI.csv`
- `outputs/grf_metrics_ARI.csv`

파일명의 `grf`는 기존 실행 경로 호환을 위한 legacy label입니다. 이 스크립트의 실제 estimator는 centroid 좌표를 피처로 포함한 `RandomForestRegressor`입니다.

순위 컬럼:
- `rank_desc = 1` 이 예측 위험도가 가장 높은 우선순위입니다.

## 참고
- 현재 SLM/SEM/SAM 구현은 PySAL 없이 동작하는 근사 버전입니다.
- 논문 수준의 추론 결과(SE, p-value)가 필요하면 `libpysal`과 `spreg`로 다시 실행해야 합니다.
