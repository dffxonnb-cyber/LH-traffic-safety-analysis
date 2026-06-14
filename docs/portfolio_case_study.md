# 포트폴리오 케이스 스터디 요약

## 한 줄 소개

4개 기존 시·구의 사고·교통·공간 패턴을 100m 격자로 학습·검증하고, 하남교산의 고위험 격자를 안전시설 현장 검토 우선 후보로 전환한 공간 위험 신호 분석입니다.

## 문제와 공간 단위

사고 이력이 부족한 신도시에서는 과거 사고 건수만으로 안전시설 우선순위를 정하기 어렵습니다. 시·구 또는 행정동 평균은 같은 지역 내부의 도로 구조와 통행 환경 차이를 가릴 수 있습니다.

이 프로젝트는 `100m × 100m` 격자를 위험도 산정, 후보 비교, 시설 검토, 시나리오 확인의 공통 단위로 사용했습니다. 기존 4개 시·구의 `99,323개` 학습 격자에서 확인한 패턴을 하남교산 `770개` 대상 격자에 적용했습니다.

## 모델과 검증

- 모델: 공간 좌표를 포함한 Random Forest 기반 위험 모델
- 검증: Leave-One-Region-Out
- Mean LORO AUC: `0.8604`
- Mean Top-10% Lift: `4.39x`
- Worst holdout AUC: `0.7979`
- Monte Carlo mean Jaccard: `0.503`

### 지표 해석

- **LORO**: 한 지역을 검증 대상으로 제외하고 나머지 지역에서 학습해, 특정 지역에만 맞춘 모델인지 점검합니다.
- **AUC**: 사고 발생 신호가 있는 격자와 그렇지 않은 격자를 전반적으로 구분하는 정도입니다.
- **Top-10% Lift**: 모델이 상위 위험 후보로 정렬한 격자에 사고 발생 신호가 전체 평균보다 얼마나 집중되는지 보여줍니다.
- **Jaccard**: 반복 실험에서 상위 후보군이 얼마나 안정적으로 겹치는지 확인하는 참고 지표입니다.

## 공개 증거

| Evidence | Public-safe artifact |
| --- | --- |
| 성능·범위 요약 | [portfolio-performance-summary.svg](./images/portfolio-performance-summary.svg) |
| 검증 방식과 지표 해석 | [portfolio-validation-summary.svg](./images/portfolio-validation-summary.svg) |
| 점수 체계 비교 진단 | [portfolio-score-comparison-note.svg](./images/portfolio-score-comparison-note.svg) |
| 4개 지역 100m 위험도 지도 | [four-city-risk-overview-ko.png](./images/four-city-risk-overview-ko.png) |
| 공개 Top-20 미리보기 | [public-top20-priority-preview.svg](./images/public-top20-priority-preview.svg) |
| 공개 Top-20 표 | [public_top20_priority.csv](./data/public_top20_priority.csv) |
| 공개 근거 상태표 | [public_evidence_status.csv](./data/public_evidence_status.csv) |

공개 Top-20 표는 이미 추적 중인 시나리오 CSV의 격자 순위와 정규화 위험도만 사용합니다. 시설 패키지와 추천 사유를 생성하는 코드는 존재하지만 해당 원본 결과는 공개 저장소에 없으므로 `needs confirmation`으로 표시합니다.

LORO 공개 근거는 Mean AUC `0.8604`, Worst holdout AUC `0.7979`, Mean Top-10% Lift `4.39x` 요약까지입니다. fold별 원본과 run-level Monte Carlo 결과는 공개 저장소에 없으며, Dashboard도 실행 코드만 있고 검증 가능한 공개 URL은 없습니다.

## Resume-ready

**LH 교통안전 | 100m 격자 기반 교통사고 위험 신호 분석**

- 4개 시·구 `99,323개` 100m 격자의 사고·교통·공간 데이터를 통합해 위험 신호 설계
- 공간 좌표 포함 Random Forest를 LORO로 검증해 Mean AUC `0.8604`, Top-10% Lift `4.39x` 확인
- 검증된 위험 패턴을 하남교산 `770개` 격자에 적용해 안전시설 현장 검토 우선 후보 도출
- 위험 순위와 시설 패키지·추천 사유 생성 로직, 시나리오 지도를 의사결정 보조 흐름으로 연결

## 한계

- 시나리오 결과는 실제 사고 감소 효과나 인과효과를 증명하지 않습니다.
- 모델 출력은 안전시설 설치 결정이 아니라 현장 점검 우선순위를 위한 위험 신호입니다.
- 실제 현장 점검 및 사고 감소 사후 검증 결과는 없습니다. Top-k는 현장 검토 우선순위 제안입니다.
- 실제 시설 결정에는 현장 조사, 예산, 법규, 주민 수요, 행정 절차가 필요합니다.
- 원본 공모전 데이터와 일부 최종 결과 파일은 공개 저장소에 포함되지 않습니다.
- 지역 간 전이는 도로 구조와 생활권 차이의 영향을 받을 수 있습니다.
- `research_notebooks/gwrf_vs_priority_correlation.png`의 `R²=0.006`은 legacy GWRF 정규화 위험도와 09번 시설 입지 선정 정규화 점수가 거의 같은 순위를 만들지 않았음을 뜻합니다. 이는 모델 실패가 아니라 서로 다른 위험 개념을 측정할 가능성을 보여주며, 성능 근거가 아닌 추가 현장 검토용 진단 자료입니다.
