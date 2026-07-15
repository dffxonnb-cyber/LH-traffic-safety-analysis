# 분석 파이프라인

핵심 분석 노트북을 실행 순서대로 정리한 폴더입니다.

- 작업 디렉터리(`cwd`)는 이 폴더(`analysis_pipeline`)로 두는 것을 권장합니다.
- 일부 원본 데이터와 대용량 중간 산출물은 공개 저장소에서 제외되어 있습니다.
- 2026-07-15 종결 기준 정본 범위는 [canonical_project_scope.md](../docs/canonical_project_scope.md)를 따릅니다.

## 정본 분류

| 단계 | 파일명 | 역할 | 정본 분류 |
|------|--------|------|----------|
| 01 | `01_grid_api_integration.ipynb` | API 데이터와 격자를 연동해 통합 테이블 기반 구축 | `core input` |
| 02 | `02_grf_blended_weights.ipynb` | legacy GRF 명칭의 global/local importance 실험값 블렌딩 | `legacy experiment` |
| 03 | `03_grf_risk_index.ipynb` | legacy blended 가중치 기반 위험지수 산출 | `legacy experiment` |
| 04 | `04_gyosan_grid_matching.ipynb` | 하남교산과 4개 시·구 유사 격자 매칭 | `auxiliary transfer` |
| 05 | `05_grf_feature_integration.ipynb` | 공간 RF 관련 피처 보강·통합 | `core feature preparation` |
| 07 | `07_gyosan_priority_ranking.ipynb` | 유사 고위험·도로·학교·유사도 기반 휴리스틱 우선순위 | `auxiliary heuristic` |
| 08 | `08_gyosan_infrastructure_forecast.ipynb` | 하남교산 인프라 수요 예측 | `auxiliary forecast` |
| 09 | `09_facility_site_selection.ipynb` | 휴리스틱 점수를 입력으로 한 시설 입지·커버리지 시나리오 | `auxiliary siting prototype` |
| 10 | `10_gyosan_final_visualization.ipynb` | 결과 시각화 | `presentation` |

## 정본 모델 경로

정본 모델은 노트북 파일명의 `GRF/GWRF`가 아니라 [run_grf_ranking.py](../scripts/run_grf_ranking.py)의 **공간 좌표 포함 Random Forest**입니다.

- 운영용 연속 위험 신호: `RandomForestRegressor`, 기본 target `acc_count`
- full-data output: `pred_risk`, `rank_desc`
- 전이 검증: 별도 Random Forest 분류 기반 LORO AUC·Top-10% Lift
- 공개 검토 순서: `docs/data/gyosan_effect_reduction_by_gid.csv`의 `RiskScore_A_norm_grid`, `grid_rank`

`07`의 `우선순위_점수`와 `09`의 선정 결과는 현재 공개 Top-20과 다른 보조 경로이므로 최종 공개 점수로 사용하지 않습니다.

## 공개 evidence 경로

```text
docs/data/gyosan_effect_reduction_by_gid.csv
  → scripts/build_portfolio_evidence.py
  → docs/data/public_top20_priority.csv
  → docs/images/public-top20-priority-preview.svg
  → docs/field-review-handoff.md
```

## 참고

- 노트북·폴더명의 `GRF`·`GWRF`는 기존 실행 경로 호환을 위한 legacy label입니다. 공개 저장소에서 확인되는 핵심 모델은 공간 좌표를 포함한 Random Forest입니다.
- `06_하남교산_GRF_SHAP.ipynb`는 공개 저장소에서 제외했습니다.
- `02` 실행 결과가 `03`의 입력으로 사용됩니다.
- `data/grf_06_outputs/`가 있어야 일부 legacy 명칭 단계가 동작합니다.
- legacy·auxiliary 단계는 삭제하지 않지만 대표 README·이력서·공개 Top-20 근거에서는 제외합니다.
