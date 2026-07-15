# LH Traffic Safety | 100m Grid Risk Signals

[![Verify](https://github.com/dffxonnb-cyber/LH-traffic-safety-analysis/actions/workflows/verify.yml/badge.svg)](https://github.com/dffxonnb-cyber/LH-traffic-safety-analysis/actions/workflows/verify.yml)
[![Mean AUC](https://img.shields.io/badge/Mean%20AUC-0.8604-2563eb)](./docs/reproducibility_and_validation.md#top35-validation)
[![Top 10 Lift](https://img.shields.io/badge/Top--10%25%20Lift-4.39x-0f766e)](./docs/reproducibility_and_validation.md#top35-validation)

> 100m 격자 위험 예측을 안전시설 현장 검토 우선순위로 전환한 공간 위험 신호 분석

사고 이력이 부족한 신도시에서는 과거 사고 건수만으로 안전시설 우선순위를 정하기 어렵습니다. 이 프로젝트는 4개 기존 시·구 `99,323개` 100m 격자의 사고·교통·공간 패턴을 LORO로 검증하고, 하남교산 `770개` 격자를 현장 검토 후보로 우선순위화했습니다. 결과는 실제 사고 예방 효과가 아닌 **의사결정 보조 위험 신호**로 해석합니다.

행정구역 평균은 같은 지역 내부의 도로 구조와 통행 환경 차이를 가릴 수 있습니다. 그래서 `100m × 100m` 격자를 위험도 산정, 후보 비교, 시설 검토, 시나리오 확인의 공통 단위로 사용했습니다.

## Reviewer Takeaway

이 프로젝트는 실제 안전시설 설치 효과나 사고 감소 인과효과를 증명하지 않습니다.

대신 사고 이력이 부족한 신도시에서 **어떤 100m 격자를 먼저 현장 검토해야 하는지**를 판단하기 위한 위험 신호 설계와 공개 가능한 검증 경계를 보여줍니다.

- `100m × 100m` 격자를 공통 의사결정 단위로 사용했습니다.
- 기존 4개 시·구 `99,323개` 학습 격자의 사고·교통·공간 패턴을 바탕으로 하남교산 `770개` 대상 격자를 우선순위화했습니다.
- LORO 검증으로 지역 간 전이 가능성을 점검했습니다.
- 공개 저장소에서는 요약 지표, public-safe CSV, SVG evidence, 방법론 문서, evidence audit을 확인할 수 있습니다.
- fold-level 원본, run-level Monte Carlo, full model-to-public-score lineage, 시설 패키지·추천 사유 최종 결과, 현장 검증 결과는 공개 evidence로 주장하지 않습니다.

## Canonical Freeze · 2026-07-15

최종 모델·점수·파이프라인·legacy 처리 기준은 [Canonical Project Scope](./docs/canonical_project_scope.md)에 고정했습니다.

| Item | Canonical decision |
| --- | --- |
| Final model name | **공간 좌표 포함 Random Forest** |
| Operational scoring model | `scripts/run_grf_ranking.py`의 `RandomForestRegressor`, 기본 target `acc_count` |
| Full-data model output | `pred_risk`, `rank_desc` |
| Transfer validation | 사고 발생 여부 기반 Random Forest 분류 + LORO AUC·Top-10% Lift |
| Final public score | `RiskScore_A_norm_grid`, `grid_rank` |
| Final public result | `public_top20_priority.csv`와 대응 SVG evidence |
| Final decision use | 설치 결정이 아닌 현장 검토 우선순위 신호 |

`GRF`·`GWRF`는 파일명과 기존 컬럼 호환을 위한 legacy label입니다. 전용 geographically weighted random forest 구현으로 주장하지 않습니다.

`07_gyosan_priority_ranking.ipynb`의 `우선순위_점수`와 `09_facility_site_selection.ipynb`의 입지선정 결과는 현재 공개 Top-20과 다른 auxiliary 경로입니다. 최종 공개 점수와 혼용하지 않습니다.

## 3-Minute Reviewer Path

| Step | Open | What to check |
| --- | --- | --- |
| 1 | [Performance Summary](./docs/images/portfolio-performance-summary.svg) | 공간 단위, 학습·대상 범위, 핵심 검증 지표 |
| 2 | [Canonical Project Scope](./docs/canonical_project_scope.md) | 최종 모델·점수·핵심 파이프라인·legacy 처리 |
| 3 | [Validation Summary](./docs/images/portfolio-validation-summary.svg) | LORO 검증 구조, AUC, Lift, Jaccard 해석 |
| 4 | [Public Top-20 Preview](./docs/images/public-top20-priority-preview.svg) | 공개 `RiskScore_A_norm_grid` 기준 후보 순위 |
| 5 | [Field Review Handoff](./docs/field-review-handoff.md) | Top-20을 현장 재확인 순서로 읽는 방법 |
| 6 | [Reproducibility Guide](./docs/reproducibility_and_validation.md) | 공개 저장소 기준 확인 가능 범위와 한계 |
| 7 | [Portfolio Case Study](./docs/portfolio_case_study.md) | 이 프로젝트를 이력서/포트폴리오에서 읽는 방식 |

## What This Proves

| Signal | Evidence |
| --- | --- |
| **Spatial structuring** | 행정구역 평균 대신 `100m × 100m` 격자를 위험도 산정과 후보 비교의 공통 단위로 사용 |
| **Transfer validation** | 기존 4개 시·구를 기준으로 LORO 검증을 적용해 지역 간 위험 패턴 유지 여부를 점검 |
| **Priority design** | 위험도 점수를 현장 검토 우선 후보로 번역 |
| **Controlled claims** | 실제 사고 감소 효과나 설치 성과를 주장하지 않고 의사결정 보조 신호로 제한 |
| **Public evidence policy** | 비공개 원천 데이터 없이 확인 가능한 SVG, CSV, 방법론 문서, 검증 요약만 공개 |
| **Scope control** | 모델 점수, 공개 점수, 휴리스틱·legacy 경로를 구분해 과장과 혼용을 방지 |

## Public Scope Boundary

`needs confirmation`은 결함을 숨기는 표시가 아니라, **공개 저장소에서 실제로 확인 가능한 범위를 통제하기 위한 표시**입니다.

| Scope | Public Status | What reviewers can check |
| --- | --- | --- |
| 정본 모델·점수·파이프라인 | `confirmed public summary` | [canonical_project_scope.md](./docs/canonical_project_scope.md) |
| 공간 단위와 데이터 범위 | `confirmed public summary` | `100m × 100m` 격자, 4개 기존 시·구 `99,323개` 학습 격자, 하남교산 `770개` 대상 격자 |
| LORO 전이 검증 요약 | `confirmed public summary` | Mean AUC `0.8604`, Worst holdout AUC `0.7979`, Mean Top-10% Lift `4.39x` |
| Monte Carlo 후보 안정성 | `confirmed public summary` | Top-20 후보군 안정성 참고값인 mean Jaccard `0.503` |
| 공개 Top-20 후보 | `confirmed public artifact` | [public_top20_priority.csv](./docs/data/public_top20_priority.csv)의 상위 20개 격자와 정규화 위험도 |
| model-to-public-score lineage | `needs confirmation` | 모델 코드와 공개 결과 파일은 있으나 `pred_risk`에서 `RiskScore_A_grid`까지 전체 private-data 경로는 공개되지 않음 |
| `07` 휴리스틱 점수 | `confirmed public diagnostic` | `유사_고위험×2 + 도로 + 학교비율×3 + 유사도`; 현재 공개 Top-20과 다른 auxiliary 경로 |
| `09` 시설 입지 시나리오 | `partial / limited public evidence` | k=10/20/30 커버리지 프로토타입; 최종 공개 순위 아님 |
| 점수 체계 진단 | `confirmed public diagnostic` | legacy GWRF 정규화 위험도와 09번 시설 입지 선정 정규화 점수의 `R²=0.006` 진단 |
| Dashboard 공개 배포 URL | `needs confirmation` | Streamlit 코드와 public-safe fallback 구조는 확인 가능하나, 검증 가능한 공개 배포 URL은 없음 |
| 시설 패키지·추천 사유 | `needs confirmation` | 생성 로직은 설명 가능하지만 최종 공개 원본 결과 파일은 없음 |
| 현장 점검·사고 감소 효과 | `not available` | 실제 설치 결과, 현장 점검 결과, 사고 감소 사후 검증 데이터 없음 |

공개 저장소는 full retraining 저장소가 아니라, **결과를 검토하고 의사결정 구조와 검증 경계를 이해하기 위한 public-safe evidence 저장소**로 설계했습니다.

![Public performance summary](./docs/images/portfolio-performance-summary.svg)

## Portfolio Summary

| Item | Description |
|------|-------------|
| Problem | 사고 이력이 부족한 신도시에서는 과거 사고 건수만으로 안전시설 설치 우선순위를 정하기 어렵다 |
| Target Area | 하남교산 신도시 후보 격자 |
| Training Context | 4개 기존 시·구 `99,323개` 학습 격자 |
| Target Scope | 하남교산 `770개` 대상 격자 |
| Spatial Unit | `100m × 100m` 격자 단위 위험도 산정 및 후보지 비교 |
| Core Method | 공간 좌표를 포함한 Random Forest 기반 위험 모델과 지역 간 전이 검증 |
| Validation | Mean AUC `0.8604`, Mean Top-10% Lift `4.39x`, Worst holdout AUC `0.7979` |
| Robustness | Monte Carlo 기반 Top20 후보 안정성 점검, mean Jaccard `0.503` |
| Public Output | `RiskScore_A_norm_grid` 기반 Top-20 현장 검토 후보와 evidence package |
| Role | 공간 분석 설계, 위험도 산정, 전이 검증, 우선순위 도출, 시각화와 문서화 수행 |

## Public Evidence

공개 증거 자산은 비공개 원천 데이터나 좌표를 새로 노출하지 않고, 저장소에서 이미 확인 가능한 범위만 요약합니다.

| Evidence | Public Status | 확인 내용 |
| --- | --- | --- |
| [Canonical Project Scope](./docs/canonical_project_scope.md) | `confirmed public summary` | 최종 모델·점수·파이프라인·legacy 처리 |
| [Performance Summary](./docs/images/portfolio-performance-summary.svg) | `confirmed public summary` | 공간 단위, 학습·대상 범위, 핵심 검증 지표 |
| [Validation Summary](./docs/images/portfolio-validation-summary.svg) | `confirmed public summary` | LORO 흐름과 AUC·Lift·Jaccard의 평이한 해석 |
| [Score Comparison Note](./docs/images/portfolio-score-comparison-note.svg) | `confirmed public diagnostic` | `R²=0.006` 비교 대상과 해석 |
| [Gyosan Scenario Mapping CSV](./docs/data/gyosan_effect_reduction_by_gid.csv) | `confirmed public artifact` | `RiskScore_A_grid`, `RiskScore_A_norm_grid`, `grid_rank` |
| [Public Top-20 Preview](./docs/images/public-top20-priority-preview.svg) | `confirmed public artifact` | 공개 시나리오 CSV 기준 상위 격자 순위와 정규화 위험도 |
| [Public Top-20 CSV](./docs/data/public_top20_priority.csv) | `confirmed public artifact` | 공개 검토용 20개 후보 표 |
| [Public Evidence Status](./docs/data/public_evidence_status.csv) | `confirmed public artifact` | 확인됨·제한적 공개·`needs confirmation`·미보유 근거 상태 |
| [Public Evidence Audit](./docs/evidence_audit.md) | `confirmed public summary` | 리뷰어가 확인 가능한 근거와 주장하지 않는 범위 |

시설 패키지와 추천 사유를 생성하는 코드는 존재하지만 해당 최종 원본 결과 파일은 공개 저장소에 없습니다. 따라서 공개 Top-20 표에서는 해당 결과를 `needs confirmation`으로 유지합니다.

LORO는 Mean AUC `0.8604`, Worst holdout AUC `0.7979`, Mean Top-10% Lift `4.39x`의 공개 요약을 제공합니다. 다만 fold별 원본 `transfer_loro_detail.csv`와 run-level Monte Carlo 결과는 공개 저장소에 없어 원본 재검산 범위는 `needs confirmation`입니다.

## Project Context

신도시나 신규 개발지에서는 기존 사고 이력이 충분하지 않은 경우가 많습니다. 이때 단순히 현재 사고 건수가 적다는 이유로 안전시설 우선순위를 낮게 잡으면, 실제 위험 요인이 숨어 있는 지역을 놓칠 수 있습니다.

이 프로젝트는 다음 질문에서 출발했습니다.

- 사고 데이터가 충분한 기존 도시에서는 어떤 공간 패턴이 위험과 연결되는가?
- 그 패턴은 다른 지역에서도 어느 정도 유지되는가?
- 사고 이력이 부족한 하남교산에는 어떤 격자가 상대적으로 위험한 후보인가?
- 제한된 현장 조사 자원을 어떤 격자부터 투입해야 하는가?
- 결과를 담당자가 재확인 가능한 형태로 제시할 수 있는가?

즉, 목적은 “위험한 곳을 확정했다”가 아니라 **사고 데이터가 부족한 지역에서도 검토 가능한 우선순위를 만드는 것**입니다.

## Decision Value

이 프로젝트는 비GIS 채용담당자 관점에서 보면 `리스크 스코어 기반 자원 배분` 문제에 가깝습니다.

| Decision Layer | Meaning |
|----------------|---------|
| Risk Scoring | 후보 격자별 위험도를 산정해 비교 가능하게 만든다 |
| Priority Ranking | 위험도가 높은 후보를 현장 검토 순서로 정리한다 |
| Evidence Boundary | 공개 가능한 점수·파일과 비공개 lineage를 분리한다 |
| Field Handoff | 도로 구조, 보행 맥락, 기존 시설, 법규·예산을 재확인하도록 넘긴다 |
| Scenario Review | 개입 가정에 따른 위험도 변화를 검토하되 실측 효과로 주장하지 않는다 |

비즈니스 문제로 바꾸면, 신규 상권/지점 후보의 입지 리스크를 비교하고 제한된 조사 자원을 고위험 후보에 먼저 배분하는 구조와 유사합니다.

## Canonical Analysis Flow

| Step | Description |
|------|-------------|
| 1. Grid Integration | 도시별 사고, 도로, 시설, 생활권 관련 데이터를 격자 단위로 통합 |
| 2. Feature Preparation | 교통안전 위험을 설명할 공간·교통 변수와 중심 좌표 정리 |
| 3. Spatial RF Scoring | 공간 좌표 포함 Random Forest로 연속 위험 신호 산출 |
| 4. Transfer Validation | 특정 지역을 홀드아웃하고 AUC·Top-10% Lift로 전이 가능성 점검 |
| 5. Gyosan Transfer | 기존 도시 위험 패턴을 하남교산 770개 격자에 적용 |
| 6. Public Ranking | `RiskScore_A_norm_grid`와 `grid_rank`로 공개 검토 순서 정리 |
| 7. Field Review Handoff | 상위 후보를 현장·공학·예산·법규 검토로 전달 |
| 8. Evidence Packaging | 공개 CSV, SVG, audit, reproducibility 문서 생성 |

## Spatial Design

행정동이나 시·구 단위만 사용하면 지역 내부의 위험 차이가 평균값에 묻힐 수 있습니다.

- 같은 행정구역 안에서도 도로 구조, 생활권, 시설 접근성, 사고 위험은 다르게 나타날 수 있음
- 안전시설 검토는 실제 현장 단위에 가까운 작은 공간 단위가 필요함
- 위험도를 지도 위에서 직접 비교하고 우선순위를 정하기 위해서는 공간 단위가 세밀해야 함
- 신도시처럼 사고 이력이 부족한 지역에도 기존 도시의 공간 패턴을 전이 적용하기 용이함

따라서 격자는 단순한 시각화 단위가 아니라, **위험도 산정, 후보 비교, 현장 검토, 시나리오 적용의 기준 단위**로 사용했습니다.

## Transfer Validation Strategy

일반적인 랜덤 train/test split보다 **지역이 바뀌어도 위험 패턴이 유지되는가**가 중요했습니다.

- 특정 지역을 홀드아웃하고 나머지 지역에서 학습
- 홀드아웃 지역에서 위험 구간 분리력이 유지되는지 확인
- 상위 위험 구간이 실제 사고 집중과 얼마나 맞물리는지 확인
- 가장 불리한 홀드아웃에서도 해석 가능한 성능이 유지되는지 점검
- 후보 선정 결과가 시나리오 변화에 과도하게 흔들리지 않는지 확인

## Validation Summary

| Category | Metric | Meaning | Reference |
|----------|--------|---------|-----------|
| Transfer Validation | Mean AUC `0.8604` | LORO에서 사고 발생 신호가 있는 격자와 그렇지 않은 격자를 전반적으로 구분하는 정도 | [validation guide](./docs/reproducibility_and_validation.md#top35-validation) |
| Hotspot Capture | Mean Top-10% Lift `4.39x` | 상위 10% 위험 후보군에 사고 발생 신호가 전체 평균보다 집중된 정도 | [validation guide](./docs/reproducibility_and_validation.md#top35-validation) |
| Worst Case | Worst holdout AUC `0.7979` | 가장 불리한 홀드아웃 지역에서 확인된 위험 구분력 | [validation guide](./docs/reproducibility_and_validation.md#top35-validation) |
| Selection Robustness | Monte Carlo mean Jaccard `0.503` | 반복 실험에서 Top20 후보군이 겹치는 정도를 보는 참고 지표 | [validation guide](./docs/reproducibility_and_validation.md#top35-validation) |

![Validation summary](./docs/images/portfolio-validation-summary.svg)

## Priority Ranking Logic

정본 공개 순위는 `docs/data/gyosan_effect_reduction_by_gid.csv`의 `RiskScore_A_norm_grid`와 `grid_rank`를 사용합니다. `scripts/build_portfolio_evidence.py`가 이 소스의 상위 20개를 공개 CSV와 SVG로 변환합니다.

`07_gyosan_priority_ranking.ipynb`는 다음 휴리스틱을 사용합니다.

```text
유사_고위험_여부 × 2 + 도로_격자_여부 + 학교_비율 × 3 + 유사도
```

이 경로의 기록된 Top-20은 현재 공개 Top-20과 다르므로 auxiliary heuristic으로 유지합니다. `09_facility_site_selection.ipynb`도 이 점수를 입력으로 한 입지·커버리지 프로토타입이며 정본 공개 순위가 아닙니다.

## Scenario Design

하남교산 적용 전/후 비교는 실제 사후 효과 검증이 아니라, 안전시설 개입을 가정한 시나리오 기반 예상 변화입니다.

- 위험 격자의 분포를 직관적으로 확인
- 우선 검토 후보가 어디에 집중되는지 확인
- 가정한 개입 후 위험도가 어떻게 달라질 수 있는지 비교
- 분석 결과를 정책·현장 검토자가 이해할 수 있는 형태로 전달

## Key Visuals

### Public Top-20 Priority Preview

공개 시나리오 CSV에서 확인 가능한 격자 순위와 정규화 위험도만 사용한 안전한 미리보기입니다.

![Public Top-20 priority preview](./docs/images/public-top20-priority-preview.svg)

### 4-City Risk Overview

동탄 생활권, 판교, 송파, 미사의 고위험 격자를 동일 기준으로 비교한 이미지입니다.

![4-city risk overview](./docs/images/four-city-risk-overview-ko.png)

### Hanam Gyosan Before/After Scenario

이 그림은 `실측 사후 효과`가 아니라 우선순위 후보에 시설 개선을 적용했을 때 위험도가 어떻게 완화될 수 있는지 보여주는 `시나리오 기반 예상 변화`입니다.

![Hanam Gyosan before/after](./docs/images/gyosan-before-after-ko.png)

## Repository Review Guide

1. [Canonical Project Scope](./docs/canonical_project_scope.md)에서 정본 모델·점수·pipeline을 확인합니다.
2. [Reproducibility & Validation Guide](./docs/reproducibility_and_validation.md)에서 검증 요약과 공개 범위를 확인합니다.
3. [Spatial-coordinate RF Risk Methodology](./docs/grf_risk_methodology.md)에서 모델 정의를 확인합니다.
4. [Gyosan Scenario Mapping CSV](./docs/data/gyosan_effect_reduction_by_gid.csv)와 [Public Top-20 CSV](./docs/data/public_top20_priority.csv)로 공개 산출물 구조를 검토합니다.
5. [Field Review Handoff](./docs/field-review-handoff.md)에서 결과를 실제 결정 전에 무엇과 재확인해야 하는지 확인합니다.
6. [VERIFY.md](./VERIFY.md)에서 공개 검증 명령과 CI 범위를 확인합니다.

## Engineering Signals

| Item | Description |
|------|-------------|
| Entry Points | [analysis_pipeline/](./analysis_pipeline/), [dashboard/](./dashboard/), [scripts/](./scripts/) |
| Canonical Model | 공간 좌표 포함 Random Forest regressor + LORO validation companion |
| Public Score | `RiskScore_A_norm_grid`, `grid_rank` |
| Pipeline Design | core, auxiliary, legacy 경로를 명시적으로 분리 |
| Public Release Policy | 원본 데이터 제외, 검증 가능한 시각화·문서·CSV만 공개 |
| Evidence Integrity | public Top-20 source 일치, 점수 정렬, claim boundary를 테스트와 CI로 검증 |

## Pipeline Classification

| Classification | Paths |
| --- | --- |
| `core` | `01_grid_api_integration`, `05_grf_feature_integration`, `scripts/run_grf_ranking.py`, LORO validation, public evidence build |
| `auxiliary` | `04_gyosan_grid_matching`, `07_gyosan_priority_ranking`, `08_gyosan_infrastructure_forecast`, `09_facility_site_selection`, `10_gyosan_final_visualization` |
| `legacy` | `02_grf_blended_weights`, `03_grf_risk_index`, 기존 GRF/GWRF 파일·컬럼명, 비공개 외부 GWRF 결과 의존 실험 |

세부 분류는 [analysis_pipeline/README.md](./analysis_pipeline/README.md)에 정리했습니다.

## Reproducibility Scope

| Scope | Availability |
|-------|--------------|
| 정본 범위·방법론·검증 문서 | 확인 가능 |
| 공개 Top-20 source와 생성 결과 | 확인 가능 |
| 대시보드 public-safe 코드 | 확인 가능 |
| 원본 공모전 데이터 기반 격자 통합 | 비공개 데이터 필요 |
| 공간 좌표 포함 Random Forest 학습 전체 재현 | 비공개 데이터 필요 |
| `pred_risk` → `RiskScore_A_grid` 전체 lineage | `needs confirmation` |
| 시설 패키지·추천 사유 최종 원본 | `needs confirmation` |
| 현장 점검·사고 감소 사후 결과 | `not available` |

## Data Policy

- 공개 저장소에는 원본 공모전 데이터와 대용량 파생 데이터가 포함되지 않습니다.
- 로컬 재현 시 승인된 데이터만 `data/`에 넣거나 환경변수 `LH_DATA_ROOT`로 경로를 지정해야 합니다.
- 공개 저장소 기준 검증 가능 범위는 [Reproducibility & Validation Guide](./docs/reproducibility_and_validation.md)에 따릅니다.
- 저장소의 코드와 문서는 [MIT License](./LICENSE)를 따르며, 외부 원천 데이터 권리는 각 제공처 정책을 따릅니다.

## Limitations

- 하남교산 적용 결과는 실제 사후 효과 검증이 아니라 시나리오 기반 예상 변화입니다.
- 실제 현장 점검 결과와 사고 감소 사후 데이터는 없습니다.
- 원본 공모전 데이터가 공개 저장소에 포함되지 않아 전체 파이프라인의 완전 재현은 제한됩니다.
- 모델 output과 공개 score의 전체 lineage는 공개 재현되지 않습니다.
- 특정 지역에서 학습한 위험 패턴은 다른 지역에 적용할 때 공간 구조와 생활권 차이에 따른 해석 주의가 필요합니다.
- 시설 패키지와 추천 사유의 공개 원본 결과는 없어 `needs confirmation` 상태입니다.
- 검증 가능한 공개 Dashboard URL은 없어 `needs confirmation` 상태입니다.
- `R²=0.006`은 점수 체계 차이를 보는 진단 자료이며 순위상관이나 모델 실패를 직접 뜻하지 않습니다.

## Resume-ready Summary

**LH 교통안전 | 100m 격자 기반 교통사고 위험 신호 분석**

- 4개 시·구 `99,323개` 100m 격자의 사고·교통·공간 데이터를 통합해 위험 신호 설계
- 공간 좌표 포함 Random Forest의 지역 전이 가능성을 LORO로 검증해 Mean AUC `0.8604`, Top-10% Lift `4.39x` 확인
- 하남교산 `770개` 격자의 공개 normalized risk score를 현장 검토 우선순위로 정리
- 모델·공개 점수·legacy 경로의 evidence boundary를 명시하고 public-safe Top-20과 현장 인계 문서로 패키징

## References

- [Canonical Project Scope](./docs/canonical_project_scope.md)
- [Docs Index](./docs/README.md)
- [Public Evidence Audit](./docs/evidence_audit.md)
- [Reproducibility & Validation Guide](./docs/reproducibility_and_validation.md)
- [Field Review Handoff](./docs/field-review-handoff.md)
- [Risk Index Methodology](./docs/risk_index_methodology.md)
- [Spatial-coordinate RF Risk Methodology](./docs/grf_risk_methodology.md)
- [Hanam Gyosan Site Context](./docs/gyosan_site_context.md)
- [Changelog](./CHANGELOG.md)
- [License](./LICENSE)
