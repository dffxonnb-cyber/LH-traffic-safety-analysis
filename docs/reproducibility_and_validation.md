# 재현성 및 검증 가이드

## 공개 저장소에서 바로 검증 가능한 범위

| 범위 | 확인 방법 | 비고 |
|------|-----------|------|
| 핵심 결과 화면 | [README](../README.md)의 2개 지도 이미지 확인 | 대표 결과와 시나리오 비교를 바로 확인 가능 |
| 방법론 | [grf_risk_methodology.md](./grf_risk_methodology.md), [risk_index_methodology.md](./risk_index_methodology.md) | 공간 좌표 포함 Random Forest 위험도 정의, 전이 논리, 정규화 기준 |
| 검증 수치 | 아래 [TOP35 검증 요약](#top35-validation) 절 | LORO, lift, 강건성, 실행용 컬럼 정리 |
| 교산 사후 시나리오 매핑 | [gyosan_effect_reduction_by_gid.csv](./data/gyosan_effect_reduction_by_gid.csv) | 교산 100m 격자 기준 저감 매핑 결과 |
| 공개 Top-20 표 | [public_top20_priority.csv](./data/public_top20_priority.csv) | 공개 시나리오 CSV에서 파생한 순위·정규화 위험도 |
| 공개 근거 상태 | [public_evidence_status.csv](./data/public_evidence_status.csv) | 확인됨·`needs confirmation`·미보유 근거 구분 |
| 점수 체계 진단 | [portfolio-score-comparison-note.svg](./images/portfolio-score-comparison-note.svg) | `R²=0.006` 비교 대상과 해석 |
| UI/코드 구조 | [dashboard/](../dashboard/), [analysis_pipeline/](../analysis_pipeline/) | 대시보드와 분석 흐름 분리 상태 확인 가능 |

## 공개 저장소만으로는 재현되지 않는 범위

- 원본 공모전 데이터가 필요한 격자 통합 테이블 생성
- 공간 좌표 포함 Random Forest 학습 및 지역별 전이 결과 재산출
- 하남교산 최종 우선순위 CSV의 원본 단계 전체 재실행
- fold별 `transfer_loro_detail.csv`, run-level `gyosan_mc_runs.csv`, 시설 패키지·추천 사유 최종 결과
- 실제 현장 점검 결과와 사고 감소 사후 검증 결과

## 왜 완전 재현이 제한되는가

- 공모전 원본 데이터는 공개 저장소에 포함할 수 없습니다.
- 일부 핵심 산출물은 승인된 격자/시설/교통량/인구 데이터가 있어야 생성됩니다.
- 따라서 공개 저장소는 `결과를 검토하고 구조를 이해하는 저장소`로 설계했고, 원본 데이터가 필요한 단계는 문서로 검증 가능성을 보완했습니다.

## 대신 무엇으로 신뢰를 확인할 수 있는가

1. 아래 [TOP35 검증 요약](#top35-validation) 절에서 전이 성능과 강건성 수치를 확인합니다.
2. [grf_risk_methodology.md](./grf_risk_methodology.md)에서 공간 좌표 포함 Random Forest 방식과 legacy 명칭의 경계를 확인합니다.
3. [gyosan_effect_reduction_by_gid.csv](./data/gyosan_effect_reduction_by_gid.csv)에서 공개 가능한 수준의 격자 단위 시나리오 결과를 검토합니다.
4. [public_top20_priority.csv](./data/public_top20_priority.csv)에서 공개 시나리오 결과 기준 상위 후보를 확인합니다.
5. [build_portfolio_evidence.py](../scripts/build_portfolio_evidence.py)와 [build_readme_key_visuals.py](../scripts/build_readme_key_visuals.py)에서 공개 증거 생성 로직을 확인합니다.

## 평가 기준 요약

- 전이 검증: Leave-One-Region-Out
- 분리력: Mean AUC `0.8604`
- 핫스팟 포착력: Mean Top-10% Lift `4.39x`
- 선정 강건성: Monte Carlo mean Jaccard `0.503`
- 설명 가능성: 시설 패키지·추천 사유 생성 코드는 확인 가능하나 공개 원본 결과는 `needs confirmation`
- Dashboard: 코드와 배포 가이드는 확인 가능하나 검증 가능한 공개 URL은 `needs confirmation`
- 점수 체계 진단: legacy GWRF 정규화 위험도와 09번 시설 입지 선정 정규화 점수의 `R²=0.006`

## 한계

- README의 적용 전/후 이미지는 실측 사후 효과가 아니라 시나리오 기반 예상 변화입니다.
- 공개 저장소만으로 완전한 재학습은 불가능합니다.
- 공개 LORO 수치는 요약 지표이며 fold별 원본 결과는 공개 저장소에 없습니다.
- Top-k는 현장 점검 우선순위 제안이며 실제 현장 검증이나 사고 감소 효과를 의미하지 않습니다.
- 대신 의사결정 흐름, 검증 방식, 공개 가능한 결과 증거를 우선 확인할 수 있도록 구조를 정리했습니다.

<a id="top35-validation"></a>

## TOP35 검증 요약

이전 `TOP35_UPGRADE_REPORT.md` 별도 파일에 있던 내용을 이 문서로 통합했다. 파이프라인을 로컬에서 다시 돌리면 `docs/top35_validation_snapshot.md`에 동일 형식의 **자동 생성 스냅샷**이 기록될 수 있다.

### 입력 데이터(로컬 파이프라인 기준)

- 4개 시·구 통합 CSV: `data/통합_데이터/격자_최종통합.csv`
- 4개 시·구 격자 GeoJSON: `data/격자_데이터/01._격자_(4개_시·구).geojson`
- 하남교산 우선순위 CSV: `data/통합_데이터/하남교산_설치우선순위_격자.csv`
- 강건성 참조 Top20 CSV: `data/통합_데이터/hanam_gyosan_safety_site_selected_k20.csv`
- 블루프린트 소스 Top20 CSV: `data/통합_데이터/hanam_gyosan_combined_selected.csv`

(실제 경로는 환경에 따라 `LH_DATA_ROOT` 등으로 달라질 수 있다.)

### 전이 검증 (Leave-One-Region-Out)

- Holdout 지역 평균 AUC: **0.8604**
- Mean top-10% lift: **4.39x**
- 최약 holdout 지역: **서울특별시 송파구** (AUC **0.7979**)
- 공개 상태: 요약 지표는 확인 가능하지만 fold별 `transfer_loro_detail.csv`는 공개 저장소에 없어 `needs confirmation`

### 피처 안정성

상위 안정 드라이버(mean importance·top3_rate):

- `AADT_mean`: mean_importance=0.2984, top3_rate=1.00
- `velocity_mean`: mean_importance=0.2251, top3_rate=1.00
- `TI_mean`: mean_importance=0.1492, top3_rate=0.62

### 하남교산 선정 강건성 (coverage 기반)

- 민감도 시나리오 중 우수: **risk60_flow40** (Jaccard=0.538, coverage=0.668)
- Monte Carlo mean Jaccard vs current top20: **0.503**
- current top20 중 `very_high` confidence tier 비율: **5.0%**

### 실행·발표 연계

- 로컬 Top20 테이블은 `recommended_package`, `recommendation_reason` 컬럼을 생성하도록 설계되어 있으나 공개 원본 결과는 없어 `needs confirmation`이다.
- 슬라이드 매핑 예: 검증 `transfer_loro_detail`·`transfer_loro_summary`, 강건성 `gyosan_mc_runs`·`gyosan_scenario_sensitivity`, 실행 `gyosan_top20_facility_blueprint`.

### 점수 체계 비교 진단

- 비교 대상: legacy GWRF 위험도 정규화 점수와 `09_facility_site_selection`의 정규화 우선순위 점수
- 공개 진단 결과: `R²=0.006`
- 해석: 두 점수 체계가 거의 같은 순위를 만들지 않았다는 뜻이며, 모델 실패를 직접 의미하지 않는다. 서로 다른 위험 개념과 가중치를 반영할 수 있으므로 대체 점수가 아니라 별도 신호로 비교하고 현장에서 확인해야 한다.
- 공개 상태: 비교 이미지와 요약은 공개되어 있으나 비교 원본 테이블과 재산출 데이터는 `needs confirmation`
