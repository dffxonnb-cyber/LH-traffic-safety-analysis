# 재현성 및 검증 가이드

이 문서는 공개 저장소 기준으로 **무엇을 바로 확인할 수 있고, 무엇은 원본 데이터 없이는 재현할 수 없는지**를 설명합니다.

최종 모델·점수·파이프라인·legacy 처리 기준은 [canonical_project_scope.md](canonical_project_scope.md)에 2026-07-15 정본으로 고정했습니다.

이 프로젝트는 실제 사고 감소 효과나 안전시설 설치 성과를 증명하는 프로젝트가 아닙니다.  
목적은 사고 이력이 부족한 신도시에서 현장 검토 우선순위를 만들기 위한 **100m 격자 기반 의사결정 보조 위험 신호**를 설계하고, 공개 가능한 범위에서 그 근거와 한계를 설명하는 것입니다.

## 정본 확정

| 구분 | 정본 |
| --- | --- |
| 모델 명칭 | 공간 좌표 포함 Random Forest |
| 운영용 점수 모델 | `scripts/run_grf_ranking.py`의 `RandomForestRegressor`; 기본 target `acc_count` |
| full-data 모델 출력 | `pred_risk`, `rank_desc` |
| 전이 검증 | 사고 발생 여부 기반 Random Forest 분류 + LORO AUC·Top-10% Lift |
| 공개 최종 점수 | `gyosan_effect_reduction_by_gid.csv`의 `RiskScore_A_norm_grid`, `grid_rank` |
| 공개 최종 결과 | `public_top20_priority.csv`와 대응 SVG evidence |

운영용 연속 점수 모델과 전이 검증용 분류 모델은 역할이 다릅니다. 분류 모델은 AUC·Lift를 통해 지역 전이 가능성을 점검하며, 공개 Top-20 점수를 직접 생성하는 단일 최종 모델로 주장하지 않습니다.

또한 공개 저장소에는 full model output에서 `RiskScore_A_grid`까지 이어지는 전체 원본 데이터 lineage가 없습니다. 따라서 모델 정의와 공개 결과 파일은 각각 확인 가능하지만, 둘의 전체 재산출 연결은 `needs confirmation`입니다.

## 공개 저장소에서 바로 검증 가능한 범위

| 범위 | 확인 방법 | 공개 상태 | 비고 |
|------|-----------|-----------|------|
| 정본 범위 | [canonical_project_scope.md](canonical_project_scope.md) | `confirmed public summary` | 최종 모델·점수·파이프라인·legacy 처리 기준 |
| 핵심 결과 화면 | [README](../README.md)의 공개 이미지 확인 | `confirmed public summary` | 대표 결과와 시나리오 비교를 바로 확인 가능 |
| 방법론 | [grf_risk_methodology.md](grf_risk_methodology.md), [risk_index_methodology.md](risk_index_methodology.md) | `confirmed public summary` | 공간 좌표 포함 Random Forest 위험도와 관측 기반 지표의 구분 |
| 검증 수치 | 아래 [TOP35 검증 요약](#top35-validation) 절 | `confirmed public summary` | LORO, Lift, Jaccard, 실행용 컬럼 정리 |
| 교산 사후 시나리오 매핑 | [gyosan_effect_reduction_by_gid.csv](data/gyosan_effect_reduction_by_gid.csv) | `confirmed public artifact` | `RiskScore_A_grid`, `RiskScore_A_norm_grid`, `grid_rank` 포함 공개 결과 |
| 공개 Top-20 표 | [public_top20_priority.csv](data/public_top20_priority.csv) | `confirmed public artifact` | 공개 시나리오 CSV에서 파생한 순위·정규화 위험도 |
| 공개 근거 상태 | [public_evidence_status.csv](data/public_evidence_status.csv) | `confirmed public artifact` | 확인됨·제한적 공개·`needs confirmation`·미보유 근거 구분 |
| 공개 evidence 감사표 | [evidence_audit.md](evidence_audit.md) | `confirmed public summary` | 리뷰어가 확인 가능한 근거와 주장하지 않는 범위를 한 번에 확인 |
| 점수 체계 진단 | [portfolio-score-comparison-note.svg](images/portfolio-score-comparison-note.svg) | `confirmed public diagnostic` | `R²=0.006` 비교 대상과 해석 |
| `07` heuristic | [07_gyosan_priority_ranking.ipynb](../analysis_pipeline/07_gyosan_priority_ranking.ipynb) | `confirmed public diagnostic` | 공개 최종 Top-20과 다른 보조 우선순위 경로 |
| UI/코드 구조 | [dashboard/](../dashboard/), [analysis_pipeline/](../analysis_pipeline/) | `partial / limited public evidence` | 대시보드 코드와 분석 흐름은 확인 가능하나, 전체 재실행과 공개 배포 URL은 제한됨 |

## 공개 저장소만으로는 재현되지 않는 범위

다음 항목은 공개 저장소만으로 완전 재현할 수 없습니다.

- 원본 공모전 데이터가 필요한 격자 통합 테이블 생성
- 공간 좌표 포함 Random Forest 학습 및 지역별 전이 결과 재산출
- full model `pred_risk`에서 공개 `RiskScore_A_grid`까지의 전체 lineage
- 하남교산 최종 우선순위 CSV의 원본 단계 전체 재실행
- fold별 `transfer_loro_detail.csv`
- run-level `gyosan_mc_runs.csv`
- 시설 패키지·추천 사유 최종 원본 결과
- 검증 가능한 공개 Dashboard URL
- 실제 현장 점검 결과와 사고 감소 사후 검증 결과

이 제한은 결함을 숨기기 위한 것이 아니라, 공개 가능한 데이터와 비공개 원천 데이터의 경계를 분리하기 위한 것입니다.

## 왜 완전 재현이 제한되는가

- 공모전 원본 데이터는 공개 저장소에 포함할 수 없습니다.
- 일부 핵심 산출물은 승인된 격자·시설·교통량·인구 데이터가 있어야 생성됩니다.
- full retraining과 fold-level 재계산은 원본 데이터와 로컬 분석 환경이 필요합니다.
- `RiskScore_A_grid`의 전체 upstream 중간 산출물은 공개 저장소에 없습니다.
- 따라서 공개 저장소는 `결과를 검토하고 구조를 이해하는 저장소`로 설계했습니다.
- 원본 데이터가 필요한 단계는 방법론 문서, 공개 요약 지표, public-safe CSV, evidence audit로 검증 경계를 보완했습니다.

## 대신 무엇으로 신뢰를 확인할 수 있는가

1. [canonical_project_scope.md](canonical_project_scope.md)에서 최종 모델·점수·legacy 분류를 확인합니다.
2. [evidence_audit.md](evidence_audit.md)에서 공개 evidence 상태와 주장하지 않는 범위를 확인합니다.
3. 아래 [TOP35 검증 요약](#top35-validation) 절에서 전이 성능과 강건성 수치를 확인합니다.
4. [grf_risk_methodology.md](grf_risk_methodology.md)에서 공간 좌표 포함 Random Forest 방식과 legacy 명칭의 경계를 확인합니다.
5. [gyosan_effect_reduction_by_gid.csv](data/gyosan_effect_reduction_by_gid.csv)에서 공개 가능한 수준의 격자 단위 시나리오 결과를 검토합니다.
6. [public_top20_priority.csv](data/public_top20_priority.csv)에서 공개 시나리오 결과 기준 상위 후보를 확인합니다.
7. [public_evidence_status.csv](data/public_evidence_status.csv)에서 각 evidence의 공개 상태를 확인합니다.
8. [build_portfolio_evidence.py](../scripts/build_portfolio_evidence.py)와 [build_readme_key_visuals.py](../scripts/build_readme_key_visuals.py)에서 공개 증거 생성 로직을 확인합니다.

## 평가 기준 요약

| 기준 | 값 | 공개 상태 | 해석 |
| --- | --- | --- | --- |
| 운영용 점수 모델 | 공간 좌표 포함 Random Forest regressor, 기본 target `acc_count` | `confirmed public code` | full-data 연속 위험 신호와 순위 생성 |
| 공개 최종 점수 | `RiskScore_A_norm_grid`, `grid_rank` | `confirmed public artifact` | 추적 가능한 하남교산 public-safe 검토 순서 |
| model-to-public-score lineage | `pred_risk` → `RiskScore_A_grid` | `needs confirmation` | 양 끝의 코드·파일은 있으나 전체 private-data 중간 경로는 공개되지 않음 |
| 전이 검증 | Leave-One-Region-Out | `confirmed public summary` | 한 지역씩 제외하고 다른 지역에서 학습한 위험 신호가 유지되는지 점검 |
| 분리력 | Mean AUC `0.8604` | `confirmed public summary` | 위험 격자와 비위험 격자를 전반적으로 구분하는 정도 |
| 핫스팟 포착력 | Mean Top-10% Lift `4.39x` | `confirmed public summary` | 상위 위험 후보군에 사고 발생 신호가 평균보다 얼마나 집중되는지 확인 |
| 최약 holdout | AUC `0.7979` | `confirmed public summary` | 가장 불리한 지역에서도 일정 수준 이상의 구분력 유지 |
| 선정 강건성 | Monte Carlo mean Jaccard `0.503` | `confirmed public summary` | 반복 실험에서 Top-20 후보군이 얼마나 겹치는지 보는 참고 지표 |
| `07` 우선순위 점수 | 휴리스틱 합산 점수 | `confirmed public diagnostic` | 현재 공개 Top-20과 다른 auxiliary 경로; 정본 점수 아님 |
| 설명 가능성 | 시설 패키지·추천 사유 생성 코드 | `needs confirmation` | 생성 로직은 확인 가능하나 최종 공개 원본 결과는 없음 |
| Dashboard deployment URL | 코드와 fallback 가이드 | `needs confirmation` | public-safe mode 코드는 확인 가능하나 공개 배포 URL은 검증하지 않음 |
| 점수 체계 진단 | `R²=0.006` | `confirmed public diagnostic` | 서로 다른 점수 체계의 낮은 선형 설명력을 보여주는 진단 자료 |

## 한계

- README의 적용 전/후 이미지는 실측 사후 효과가 아니라 시나리오 기반 예상 변화입니다.
- 공개 저장소만으로 완전한 재학습은 불가능합니다.
- 공개 LORO 수치는 요약 지표이며 fold별 원본 결과는 공개 저장소에 없습니다.
- run-level Monte Carlo 결과는 공개 저장소에 없습니다.
- full model output과 공개 `RiskScore_A_grid`의 전체 lineage는 공개 저장소에 없습니다.
- 시설 패키지와 추천 사유의 최종 공개 원본 결과는 없습니다.
- `07`의 `우선순위_점수`와 현재 공개 Top-20은 다른 경로입니다.
- Top-k는 현장 점검 우선순위 제안이며 실제 현장 검증이나 사고 감소 효과를 의미하지 않습니다.
- Dashboard 코드는 공개되어 있으나 검증 가능한 공개 배포 URL은 evidence로 사용하지 않습니다.
- 대신 의사결정 흐름, 검증 방식, 공개 가능한 결과 증거, 공개 불가한 경계를 우선 확인할 수 있도록 구조를 정리했습니다.

<a id="top35-validation"></a>

## TOP35 검증 요약

이 절은 공개 저장소에서 확인 가능한 검증 요약입니다.  
로컬 파이프라인을 원본 데이터와 함께 다시 돌리면 `docs/top35_validation_snapshot.md`에 동일 형식의 자동 생성 스냅샷이 기록될 수 있습니다. 다만 공개 저장소만으로는 원본 데이터가 필요한 full retraining과 fold-level 재산출을 수행하지 않습니다.

### 입력 데이터

로컬 파이프라인 기준 입력 데이터는 다음과 같습니다.

- 4개 시·구 통합 CSV: `data/통합_데이터/격자_최종통합.csv`
- 4개 시·구 격자 GeoJSON: `data/격자_데이터/01._격자_(4개_시·구).geojson`
- 하남교산 우선순위 CSV: `data/통합_데이터/하남교산_설치우선순위_격자.csv`
- 강건성 참조 Top20 CSV: `data/통합_데이터/hanam_gyosan_safety_site_selected_k20.csv`
- 블루프린트 소스 Top20 CSV: `data/통합_데이터/hanam_gyosan_combined_selected.csv`

실제 경로는 환경에 따라 `LH_DATA_ROOT` 등으로 달라질 수 있습니다.  
위 입력 데이터는 공개 저장소에 모두 포함되어 있지 않으므로, 공개 저장소는 요약 지표와 public-safe artifact를 중심으로 검토합니다.

### 전이 검증: Leave-One-Region-Out

- Holdout 지역 평균 AUC: **0.8604**
- Mean top-10% lift: **4.39x**
- 최약 holdout 지역: **서울특별시 송파구** / AUC **0.7979**
- 공개 상태: 요약 지표는 확인 가능하지만 fold별 `transfer_loro_detail.csv`는 공개 저장소에 없어 `needs confirmation`

### 피처 안정성

상위 안정 드라이버는 다음과 같이 요약됩니다.

- `AADT_mean`: mean_importance=0.2984, top3_rate=1.00
- `velocity_mean`: mean_importance=0.2251, top3_rate=1.00
- `TI_mean`: mean_importance=0.1492, top3_rate=0.62

이 값은 공개 요약 지표로 해석하며, feature-level 원본 재계산은 공개 저장소만으로 수행하지 않습니다.

### 하남교산 선정 강건성

- 민감도 시나리오 중 우수: **risk60_flow40** / Jaccard=0.538, coverage=0.668
- Monte Carlo mean Jaccard vs current top20: **0.503**
- current top20 중 `very_high` confidence tier 비율: **5.0%**
- 공개 상태: 요약 지표는 확인 가능하지만 run-level `gyosan_mc_runs.csv`는 공개 저장소에 없어 `needs confirmation`

### 실행·발표 연계

- 로컬 Top20 테이블은 `recommended_package`, `recommendation_reason` 컬럼을 생성하도록 설계되어 있습니다.
- 다만 공개 저장소에는 시설 패키지와 추천 사유의 최종 원본 결과가 없습니다.
- 따라서 공개 Top-20 표에서는 해당 필드를 `needs confirmation`으로 유지합니다.
- `07_gyosan_priority_ranking.ipynb`와 `09_facility_site_selection.ipynb`는 auxiliary 경로이며 현재 공개 `RiskScore_A_norm_grid` Top-20과 혼용하지 않습니다.
- 슬라이드 매핑 예:
  - 검증: `transfer_loro_detail`, `transfer_loro_summary`
  - 강건성: `gyosan_mc_runs`, `gyosan_scenario_sensitivity`
  - 실행: `gyosan_top20_facility_blueprint`

### 점수 체계 비교 진단

- 비교 대상: legacy GWRF 위험도 정규화 점수와 `09_facility_site_selection`의 정규화 우선순위 점수
- 공개 진단 결과: `R²=0.006`
- 해석:
  - 두 점수 사이에서 선형 관계로 설명되는 변동이 매우 적다는 뜻입니다.
  - R²는 순위상관 지표가 아니므로 순위 일치 여부를 직접 증명하지 않습니다.
  - 낮은 R²가 모델 실패를 직접 의미하지도 않습니다.
  - 서로 다른 위험 개념과 가중치를 반영할 수 있으므로 별도 신호로 비교하고 현장에서 확인해야 합니다.
- 공개 상태: 비교 이미지와 요약은 공개되어 있으나 비교 원본 테이블과 재산출 데이터는 `needs confirmation`

## 종결 이후 유지 규칙

- 새 모델, 새 점수 조합, 새 가중치 실험은 정본에 추가하지 않습니다.
- 명백한 버그, 링크, evidence lineage, claim consistency만 수정합니다.
- `needs confirmation`을 없애기 위해 추정 결과를 새로 만들지 않습니다.
- 상태를 승격하려면 실제 파일, 생성 코드, 재현 명령 또는 CI, 문서 동기화가 모두 필요합니다.
