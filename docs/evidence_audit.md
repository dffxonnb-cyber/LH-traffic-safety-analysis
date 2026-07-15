# Public Evidence Audit

이 문서는 공개 저장소 기준으로 **무엇을 확인할 수 있고, 무엇은 확인할 수 없는지**를 한 번에 보기 위한 reviewer-facing 감사표입니다.

최종 모델·점수·파이프라인·legacy 처리 기준은 [canonical_project_scope.md](canonical_project_scope.md)에 2026-07-15 정본으로 고정했습니다.

이 프로젝트의 결과는 실제 사고 감소 효과나 안전시설 설치 성과가 아니라, 사고 이력이 부족한 신도시에서 안전시설 현장 검토 우선순위를 정하기 위한 **의사결정 보조 위험 신호**로 해석합니다.

## Reviewer Takeaway

이 프로젝트는 “어디에 안전시설을 설치하면 사고가 줄어든다”를 증명하지 않습니다.

대신 다음을 보여줍니다.

- 사고 이력이 부족한 신도시에서도 검토 가능한 공간 단위를 설계할 수 있음
- 행정구역 평균이 아니라 `100m × 100m` 격자로 위험 신호를 비교할 수 있음
- 기존 4개 시·구의 위험 패턴을 LORO 방식으로 검증하고, 하남교산 후보 격자에 적용할 수 있음
- 공개 가능한 요약 지표, Top-20 후보 표, 방법론 문서, 검증 경계를 함께 제시할 수 있음
- 비공개 원천 데이터가 필요한 부분과 공개 저장소에서 확인 가능한 부분을 분리해 과장 없이 설명할 수 있음
- 중간 휴리스틱과 최종 공개 점수를 혼용하지 않고 역할을 분리할 수 있음

## Evidence Status Rule

| Status | Meaning |
| --- | --- |
| `confirmed public summary` | 공개 저장소에서 요약 지표나 문서로 확인 가능 |
| `confirmed public artifact` | 공개 저장소에 실제 파일이 있어 직접 확인 가능 |
| `confirmed public diagnostic` | 공개 파일로 확인 가능하지만 최종 성능·순위 근거가 아닌 진단 자료 |
| `partial / limited public evidence` | 코드, 가이드, 요약은 있으나 완전한 실행 결과나 공개 URL은 없음 |
| `needs confirmation` | 생성 로직이나 언급은 있으나 최종 공개 결과 또는 전체 lineage를 확인할 수 없음 |
| `not available` | 현장 검증, 사후 성과, 운영 URL처럼 공개 evidence가 없음 |

## Audit Summary

| Evidence Area | Public Status | Public Artifact | Reviewer Interpretation |
| --- | --- | --- | --- |
| Canonical model·score·pipeline decision | `confirmed public summary` | [canonical_project_scope.md](canonical_project_scope.md) | 공간 좌표 포함 Random Forest, 정본 공개 점수, legacy·auxiliary 범위를 고정 |
| Spatial unit and scope | `confirmed public summary` | [README](../README.md), [portfolio-performance-summary.svg](images/portfolio-performance-summary.svg) | `100m × 100m` 격자, 기존 4개 시·구 `99,323개` 학습 격자, 하남교산 `770개` 대상 격자는 공개 요약으로 확인 가능 |
| LORO transfer summary | `confirmed public summary` | [reproducibility_and_validation.md](reproducibility_and_validation.md#top35-validation), [portfolio-validation-summary.svg](images/portfolio-validation-summary.svg) | Mean AUC `0.8604`, Worst holdout AUC `0.7979`, Top-10% Lift `4.39x`는 공개 요약 지표로 확인 가능 |
| Monte Carlo stability | `confirmed public summary` | [reproducibility_and_validation.md](reproducibility_and_validation.md#top35-validation), [public_evidence_status.csv](data/public_evidence_status.csv) | Mean Jaccard `0.503`은 Top-20 후보군 안정성의 참고 지표로만 해석 |
| Canonical public score and Top-20 | `confirmed public artifact` | [gyosan_effect_reduction_by_gid.csv](data/gyosan_effect_reduction_by_gid.csv), [public_top20_priority.csv](data/public_top20_priority.csv), [public-top20-priority-preview.svg](images/public-top20-priority-preview.svg) | `RiskScore_A_norm_grid`와 `grid_rank` 기준 공개 가능한 상위 후보를 직접 확인 가능 |
| Full model → public score lineage | `needs confirmation` | 모델 코드와 공개 결과 파일은 각각 존재 | 비공개 원천 데이터와 전체 중간 산출물이 없어 `pred_risk`에서 `RiskScore_A_grid`까지 공개 저장소만으로 재산출할 수 없음 |
| `07` heuristic priority score | `confirmed public diagnostic` | [07_gyosan_priority_ranking.ipynb](../analysis_pipeline/07_gyosan_priority_ranking.ipynb) | `유사_고위험×2 + 도로 + 학교비율×3 + 유사도`의 보조 점수이며 현재 공개 Top-20과 다른 경로 |
| `09` site-selection scenarios | `partial / limited public evidence` | [09_facility_site_selection.ipynb](../analysis_pipeline/09_facility_site_selection.ipynb) | `07` 점수를 입력으로 한 k=10/20/30 입지·커버리지 프로토타입; 최종 공개 순위 아님 |
| Facility package / recommendation reason | `needs confirmation` | Generation logic only; final public-safe result file is not available | 생성 로직은 설명 가능하지만, 공개 저장소에서 최종 시설 패키지와 추천 사유 원본 결과값은 확인 불가 |
| Dashboard deployment URL | `needs confirmation` | [dashboard/app.py](../dashboard/app.py), [dashboard/README.md](../dashboard/README.md) | Streamlit 코드와 public-safe fallback 구조는 확인 가능하나, 검증 가능한 공개 배포 URL은 없음 |
| Score-system comparison | `confirmed public diagnostic` | [portfolio-score-comparison-note.svg](images/portfolio-score-comparison-note.svg) | `R²=0.006`은 서로 다른 점수 체계의 낮은 선형 설명력을 보여주는 진단 자료이며, 순위 일치나 실패를 직접 뜻하지 않음 |
| Field inspection / accident reduction | `not available` | 없음 | 현장 점검 결과와 사고 감소 사후 데이터는 없으며, Top-k는 설치 효과가 아니라 검토 우선순위 제안 |

## What Reviewers Can Safely Confirm

1. 공간 단위와 데이터 범위: `100m × 100m` 격자, 기존 4개 시·구 `99,323개` 학습 격자, 하남교산 `770개` 대상 격자.
2. 정본 모델 명칭: 전용 GWRF가 아니라 공간 좌표를 피처로 포함한 Random Forest.
3. 공개 요약 성능: LORO Mean AUC `0.8604`, Worst holdout AUC `0.7979`, Mean Top-10% Lift `4.39x`.
4. 후보 안정성 참고값: Monte Carlo mean Jaccard `0.503`.
5. 공개 후보 미리보기: `RiskScore_A_norm_grid`와 `grid_rank`에서 파생한 [public_top20_priority.csv](data/public_top20_priority.csv).
6. `07`의 `우선순위_점수`와 `09`의 입지선정은 현재 공개 Top-20과 분리된 보조 경로.
7. 검증 경계: fold별 원본, run-level Monte Carlo, full model-to-public-score lineage, 시설 패키지·추천 사유 원본은 공개 저장소에서 재검산할 수 없음.
8. 대시보드 경계: dashboard 코드는 공개되어 있으나, 공개 배포 URL은 검증 가능한 evidence로 사용하지 않음.

## What This Does Not Claim

- 실제 안전시설 설치 결정이 완료되었다고 주장하지 않습니다.
- 실제 사고 감소 효과나 인과효과를 주장하지 않습니다.
- 공개 저장소만으로 전체 공간 Random Forest 학습과 모든 후보 산출을 완전 재현할 수 있다고 주장하지 않습니다.
- `07`의 휴리스틱 우선순위와 현재 공개 Top-20이 동일한 결과라고 주장하지 않습니다.
- `pred_risk`와 `RiskScore_A_grid`의 전체 lineage가 공개 재현 가능하다고 주장하지 않습니다.
- 시설 패키지와 추천 사유의 최종 공개 원본 결과가 존재한다고 주장하지 않습니다.
- 공개 Dashboard URL이 검증 가능하다고 주장하지 않습니다.
- Top-20 후보가 실제 현장 위험도 순위를 확정한다고 주장하지 않습니다.

## Reviewer Route

| Step | Open | Purpose |
| --- | --- | --- |
| 1 | [README](../README.md) | 프로젝트 포지셔닝과 핵심 지표 확인 |
| 2 | [canonical_project_scope.md](canonical_project_scope.md) | 최종 모델·점수·핵심 파이프라인·legacy 처리 확인 |
| 3 | [reproducibility_and_validation.md](reproducibility_and_validation.md) | 전이 검증, Top-10% Lift, Jaccard, R² 해석 확인 |
| 4 | [public_evidence_status.csv](data/public_evidence_status.csv) | 근거별 확인 가능 / limited / needs confirmation / not available 상태 확인 |
| 5 | [public_top20_priority.csv](data/public_top20_priority.csv) | 공개 가능한 상위 후보 순위 확인 |
| 6 | [field-review-handoff.md](field-review-handoff.md) | 결과를 실제 결정이 아닌 현장 재확인 순서로 읽는 방법 확인 |

## Maintenance Rule

새로운 evidence를 공개 저장소에 추가할 때는 아래 중 하나로 상태를 분류합니다.

- `confirmed public summary`: 공개 저장소에서 요약 지표나 문서로 확인 가능
- `confirmed public artifact`: 공개 저장소에 실제 파일이 있어 직접 확인 가능
- `confirmed public diagnostic`: 공개 파일이 있지만 최종 성능·순위의 직접 근거는 아님
- `partial / limited public evidence`: 코드, 가이드, 요약은 있으나 완전한 실행 결과나 공개 URL은 없음
- `needs confirmation`: 생성 로직이나 요약은 있으나 원본 결과 또는 전체 lineage가 공개되어 있지 않음
- `not available`: 현장 검증, 사후 성과, 운영 URL처럼 공개 evidence가 없음

분류가 바뀌면 [canonical_project_scope.md](canonical_project_scope.md), [public_evidence_status.csv](data/public_evidence_status.csv), [reproducibility_and_validation.md](reproducibility_and_validation.md), README의 Public Scope Boundary를 함께 갱신합니다.
