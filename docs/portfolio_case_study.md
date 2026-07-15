# 포트폴리오 케이스 스터디 요약

최종 모델·점수·파이프라인·legacy 처리 기준은 [canonical_project_scope.md](canonical_project_scope.md)에 고정했습니다.

## 한 줄 소개

4개 기존 시·구의 사고·교통·공간 패턴을 100m 격자로 학습·검증하고, 하남교산의 공개 normalized risk score를 안전시설 현장 검토 우선 후보로 전환한 공간 위험 신호 분석입니다.

## 문제와 공간 단위

사고 이력이 부족한 신도시에서는 과거 사고 건수만으로 안전시설 우선순위를 정하기 어렵습니다. 시·구 또는 행정동 평균은 같은 지역 내부의 도로 구조와 통행 환경 차이를 가릴 수 있습니다.

이 프로젝트는 `100m × 100m` 격자를 위험도 산정, 후보 비교, 현장 검토, 시나리오 확인의 공통 단위로 사용했습니다. 기존 4개 시·구의 `99,323개` 학습 격자에서 확인한 패턴을 하남교산 `770개` 대상 격자에 적용했습니다.

## 정본 모델과 점수

- 최종 모델 명칭: 공간 좌표 포함 Random Forest
- 운영용 모델: `RandomForestRegressor`, 기본 target `acc_count`
- full-data output: `pred_risk`, `rank_desc`
- 전이 검증: Random Forest 분류 기반 Leave-One-Region-Out
- 공개 최종 점수: `RiskScore_A_norm_grid`
- 공개 검토 순서: `grid_rank`

`GRF`·`GWRF`는 기존 파일명과 컬럼 호환을 위한 legacy label입니다. `07_gyosan_priority_ranking.ipynb`의 `우선순위_점수`와 `09_facility_site_selection.ipynb`의 입지선정 결과는 현재 공개 Top-20과 다른 auxiliary 경로입니다.

공개 저장소에는 full model `pred_risk`에서 `RiskScore_A_grid`까지 이어지는 전체 private-data lineage가 없으므로 해당 연결은 `needs confirmation`입니다.

## 모델과 검증

- Mean LORO AUC: `0.8604`
- Mean Top-10% Lift: `4.39x`
- Worst holdout AUC: `0.7979`
- Monte Carlo mean Jaccard: `0.503`

### 지표 해석

- **LORO**: 한 지역을 검증 대상으로 제외하고 나머지 지역에서 학습해, 특정 지역에만 맞춘 모델인지 점검합니다.
- **AUC**: 사고 발생 신호가 있는 격자와 그렇지 않은 격자를 전반적으로 구분하는 정도입니다.
- **Top-10% Lift**: 모델이 상위 위험 후보로 정렬한 격자에 사고 발생 신호가 전체 평균보다 얼마나 집중되는지 보여줍니다.
- **Jaccard**: 반복 실험에서 상위 후보군이 얼마나 안정적으로 겹치는지 확인하는 참고 지표입니다.

이 지표들은 위험 신호의 품질과 전이 가능성을 설명하며, 실제 시설 설치 효과나 사고 감소 인과효과를 증명하지 않습니다.

## 공개 증거

| Evidence | Public-safe artifact |
| --- | --- |
| 정본 범위 | [canonical_project_scope.md](canonical_project_scope.md) |
| 성능·범위 요약 | [portfolio-performance-summary.svg](images/portfolio-performance-summary.svg) |
| 검증 방식과 지표 해석 | [portfolio-validation-summary.svg](images/portfolio-validation-summary.svg) |
| 점수 체계 비교 진단 | [portfolio-score-comparison-note.svg](images/portfolio-score-comparison-note.svg) |
| 4개 지역 100m 위험도 지도 | [four-city-risk-overview-ko.png](images/four-city-risk-overview-ko.png) |
| 공개 ranking source | [gyosan_effect_reduction_by_gid.csv](data/gyosan_effect_reduction_by_gid.csv) |
| 공개 Top-20 미리보기 | [public-top20-priority-preview.svg](images/public-top20-priority-preview.svg) |
| 공개 Top-20 표 | [public_top20_priority.csv](data/public_top20_priority.csv) |
| 공개 근거 상태표 | [public_evidence_status.csv](data/public_evidence_status.csv) |
| 공개 근거 감사표 | [evidence_audit.md](evidence_audit.md) |

공개 Top-20 표는 추적 중인 시나리오 CSV의 `grid_rank`와 `RiskScore_A_norm_grid`만 사용합니다. 시설 패키지와 추천 사유 최종 원본은 공개 저장소에 없으므로 `needs confirmation`으로 유지합니다.

현장 검토로 넘길 때의 재확인 항목과 주장 경계는 [field-review-handoff.md](field-review-handoff.md)에 정리했습니다.

## Resume-ready

**LH 교통안전 | 100m 격자 기반 교통사고 위험 신호 분석**

- 4개 시·구 `99,323개` 100m 격자의 사고·교통·공간 데이터를 통합해 위험 신호 설계
- 공간 좌표 포함 Random Forest의 지역 전이 가능성을 LORO로 검증해 Mean AUC `0.8604`, Top-10% Lift `4.39x` 확인
- 하남교산 `770개` 격자의 공개 normalized risk score를 현장 검토 우선순위로 정리
- 모델·공개 점수·legacy 경로의 evidence boundary를 명시하고 Top-20 검토표와 현장 인계 문서로 패키징

## 한계

- 시나리오 결과는 실제 사고 감소 효과나 인과효과를 증명하지 않습니다.
- 모델 출력은 안전시설 설치 결정이 아니라 현장 점검 우선순위를 위한 위험 신호입니다.
- 실제 현장 점검 및 사고 감소 사후 검증 결과는 없습니다.
- 실제 시설 결정에는 현장 조사, 예산, 법규, 주민 수요, 행정 절차가 필요합니다.
- 원본 공모전 데이터와 일부 최종 결과 파일은 공개 저장소에 포함되지 않습니다.
- full model output과 공개 score의 전체 lineage는 공개 재현되지 않습니다.
- 지역 간 전이는 도로 구조와 생활권 차이의 영향을 받을 수 있습니다.
- `R²=0.006`은 서로 다른 점수 체계의 낮은 선형 설명력을 보는 진단 자료이며, 순위상관이나 모델 실패를 직접 뜻하지 않습니다.
