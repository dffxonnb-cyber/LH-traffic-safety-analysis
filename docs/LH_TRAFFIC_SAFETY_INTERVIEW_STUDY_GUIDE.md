# LH Traffic Safety 면접·학습 가이드

이 문서는 LH Traffic Safety Analysis 전체를 빠르게 복습하고, 공간데이터·GIS·데이터 분석·공공정책·리스크 모델링 면접에서 프로젝트를 일관되게 설명하기 위한 요약본입니다.

> 핵심 질문: **사고 이력이 부족한 신도시에서 제한된 현장 조사 자원을 어떤 100m 격자부터 투입할 것인가?**

---

## 1. 30초 프로젝트 소개

LH Traffic Safety는 사고 이력이 부족한 하남교산 신도시의 안전시설 검토 순서를 정하기 위해, 기존 4개 시·구의 99,323개 100m 격자에서 사고·교통·공간 패턴을 학습하고 하남교산 770개 격자에 위험 신호를 적용한 공간 분석 프로젝트입니다.

공간 좌표를 포함한 Random Forest로 연속 위험 신호를 만들고, 지역 하나를 통째로 제외하는 LORO 검증으로 지역 간 전이 가능성을 확인했습니다. 공개 결과는 `RiskScore_A_norm_grid` 기반 Top-20 현장 검토 후보입니다.

이 결과는 실제 시설 설치 결정이나 사고 감소 효과를 예측하는 것이 아니라, **어떤 격자를 먼저 현장 확인할지 정하는 의사결정 보조 신호**입니다.

## 2. 1분 면접 답변

신도시에서는 과거 사고 이력이 적기 때문에 단순 사고 건수만으로 안전시설 우선순위를 정하면 아직 사고가 관측되지 않았지만 구조적으로 위험한 공간을 놓칠 수 있습니다. 또한 행정동 평균은 같은 지역 안의 도로 구조와 통행 환경 차이를 가립니다.

그래서 100m×100m 격자를 공통 분석 단위로 사용했습니다. 기존 4개 시·구 99,323개 격자에서 교통량, 속도, 도로·교통 위험 변수와 중심 좌표를 정리하고, 공간 좌표 포함 Random Forest Regressor로 연속 위험 신호를 산출했습니다.

단순 random split은 가까운 공간의 유사성이 train과 test에 섞여 성능이 부풀 수 있어, 특정 지역 전체를 제외하는 Leave-One-Region-Out 검증을 적용했습니다. 공개 요약 성능은 Mean AUC 0.8604, Worst holdout AUC 0.7979, Mean Top-10% Lift 4.39배입니다.

하남교산에는 정규화 공개 점수와 순위를 적용해 Top-20 후보를 만들고, 최종 결정이 아니라 도로 구조·보행 맥락·기존 시설·법규·예산을 다시 확인할 현장 검토 순서로 전달했습니다. 공개 저장소에서는 정본 모델, 공개 점수, legacy 휴리스틱과 확인 불가능한 lineage를 명시적으로 구분했습니다.

---

## 3. 문제 정의

### 문제 상황

신규 개발지에서는 다음 문제가 발생합니다.

- 사고 이력이 적다는 것이 안전하다는 뜻은 아닙니다.
- 기존 사고 건수 기반 우선순위는 잠재 위험을 놓칠 수 있습니다.
- 시·구·행정동 평균은 지역 내부의 미세한 위험 차이를 가립니다.
- 안전시설 예산과 현장 조사 인력은 제한되어 있습니다.
- 모델 점수가 실제 설치 결정으로 과장될 위험이 있습니다.

### 분석 질문

1. 기존 도시에서 어떤 공간·교통 패턴이 사고 위험과 연결되는가?
2. 그 패턴은 다른 지역에서도 유지되는가?
3. 사고 이력이 부족한 하남교산에서 어떤 격자가 상대적으로 우선 검토 대상인가?
4. 제한된 현장 조사 자원을 어떤 순서로 배분할 것인가?
5. 결과를 공개 가능한 증거와 함께 어떻게 전달할 것인가?

### 최종 의사결정 단위

```text
100m × 100m grid
```

격자는 단순 지도 표현 단위가 아니라 다음의 공통 기준입니다.

- 위험도 산정
- 후보 간 비교
- 하남교산 transfer
- 현장 검토 순서
- 시나리오 확인

---

## 4. 정본 범위

이 프로젝트는 2026-07-15 기준 정본이 고정되어 있습니다.

| 항목 | 정본 결정 |
| --- | --- |
| 문제 정의 | 하남교산 100m 격자의 현장 검토 우선순위 |
| 최종 모델 명칭 | 공간 좌표 포함 Random Forest |
| 운영용 점수 모델 | `RandomForestRegressor`, 기본 target `acc_count` |
| 전이 검증 모델 | 사고 발생 여부 Random Forest classifier + LORO |
| 모델 출력 | `pred_risk`, `rank_desc` |
| 최종 공개 점수 | `RiskScore_A_norm_grid`, `grid_rank` |
| 최종 공개 결과 | `public_top20_priority.csv`와 SVG evidence |
| 최종 용도 | 설치 결정이 아닌 현장 검토 우선순위 신호 |

`GRF`, `GWRF`는 legacy 파일명과 컬럼 호환을 위해 남아 있습니다. 전용 geographically weighted random forest를 구현했다고 주장하지 않습니다.

---

## 5. 전체 분석 흐름

```text
4개 기존 시·구 공간 데이터
→ 100m grid integration
→ feature preparation
→ spatial-coordinate Random Forest risk scoring
→ Leave-One-Region-Out transfer validation
→ Hanam Gyosan 770-grid transfer
→ normalized public score + rank
→ Top-20 field-review candidates
→ public-safe CSV / SVG / audit / handoff
```

### 단계별 의미

| 단계 | 설명 |
| --- | --- |
| Grid integration | 사고·도로·시설·생활권 데이터를 격자 기준으로 통합 |
| Feature preparation | 교통·공간 변수와 격자 중심 좌표 정리 |
| Risk scoring | 연속 위험 신호와 순위 생성 |
| Transfer validation | 한 지역 전체를 제외해 지역 간 일반화 확인 |
| Gyosan transfer | 기존 도시 패턴을 대상 770개 격자에 적용 |
| Public ranking | 공개 가능한 정규화 점수와 순위 생성 |
| Field handoff | 상위 후보를 현장·공학·예산 검토로 전달 |
| Evidence packaging | 공개 CSV, SVG, 검증 문서, audit 생성 |

---

## 6. 공간 단위 설계

### 왜 행정구역 평균이 아닌 100m 격자인가

같은 행정동 안에서도 다음 조건이 다릅니다.

- 교차로와 도로 형태
- 통행량과 평균 속도
- 학교·생활권·보행 맥락
- 기존 안전시설
- 사고 발생 환경

행정구역 평균을 쓰면 이러한 차이가 평균에 묻힐 수 있습니다. 100m 격자는 현장 검토 단위에 더 가깝고, 지도에서 후보를 직접 비교하기 쉽습니다.

### 격자 설계의 장점

- 서로 다른 공간 데이터를 동일 키로 결합할 수 있습니다.
- 지역 내부의 이질성을 표현할 수 있습니다.
- 기존 도시와 신도시의 feature 구조를 맞추기 쉽습니다.
- Top-k 후보를 현장 단위로 전달할 수 있습니다.

### 격자 설계의 한계

- 격자 경계에 따라 값이 달라지는 MAUP 문제가 있습니다.
- 100m가 실제 보행·도로 영향 범위를 완벽히 대표하지 않습니다.
- 인접 격자 간 공간 자기상관이 존재합니다.
- 격자 중심 좌표만으로 복잡한 공간 관계를 모두 표현할 수 없습니다.

---

## 7. 정본 모델

### 모델

```text
RandomForestRegressor
```

### 기본 target

```text
log1p(acc_count)
```

사고 건수는 0이 많고 오른쪽 꼬리가 긴 count 데이터일 수 있어 `log1p` 변환으로 큰 값의 영향과 분포 왜곡을 완화합니다.

### 기본 features

```text
AADT_mean
velocity_mean
FRIN_mean
TI_mean
x_coord
y_coord
```

### 기본 설정

```text
n_estimators = 500
max_depth = 18
min_samples_leaf = 5
random_state = 42
```

### 출력

```text
pred_log_risk
pred_risk
rank_desc
rank_pct
```

### 왜 Random Forest인가

- 비선형 관계와 feature interaction을 포착할 수 있습니다.
- scaling 요구가 비교적 낮습니다.
- 복잡한 공간·교통 변수의 threshold effect를 표현하기 쉽습니다.
- 선형 모델과 비교해 flexible baseline으로 활용할 수 있습니다.

### 좌표를 포함한 이유

좌표는 위치에 따라 달라지는 배경 패턴을 일부 반영할 수 있습니다. 하지만 좌표 포함이 진정한 공간 모델을 보장하는 것은 아니며, 특정 지역의 위치를 외우는 leakage 위험도 있습니다. 그래서 지역 단위 holdout 검증이 중요합니다.

---

## 8. 운영용 모델과 전이 검증 모델의 차이

이 프로젝트에서 가장 헷갈리기 쉬운 부분입니다.

### 운영용 점수 모델

- `RandomForestRegressor`
- target: `acc_count`의 연속 변환값
- 목적: 격자별 연속 위험 신호와 순위 생성

### 전이 검증 모델

- 사고 발생 여부 기반 Random Forest classification
- 지역 하나를 통째로 제외하는 LORO
- 목적: 새로운 지역에서도 위험 구분 패턴이 유지되는지 검증

### 왜 두 모델을 구분해야 하는가

AUC와 Top-10% Lift는 사고 발생 여부를 기준으로 한 전이 검증 지표입니다. 이 지표를 Regressor의 직접적인 out-of-sample 회귀 성능이라고 말하면 안 됩니다.

면접에서는 다음처럼 설명합니다.

> 연속 위험 점수 생성은 Regressor가 담당하고, 공개 AUC와 Lift는 별도의 지역 전이 검증용 classification setup에서 확인했습니다.

---

## 9. LORO 검증

### Leave-One-Region-Out

```text
지역 A holdout → 나머지 지역 학습 → A 평가
지역 B holdout → 나머지 지역 학습 → B 평가
...
```

### 왜 random split이 아닌가

공간 데이터에서 random split을 하면 가까운 격자나 같은 지역의 유사 패턴이 train과 test에 동시에 들어갈 수 있습니다. 그러면 실제 새로운 지역에 적용할 때보다 성능이 높게 보일 수 있습니다.

LORO는 **지역이 바뀌어도 위험 패턴이 유지되는가**를 더 직접적으로 확인합니다.

### 공개 검증 결과

| 지표 | 결과 | 의미 |
| --- | ---: | --- |
| Mean AUC | 0.8604 | 홀드아웃 지역에서 사고 신호 격자와 비사고 격자를 구분하는 평균 성능 |
| Worst holdout AUC | 0.7979 | 가장 불리한 지역에서도 유지된 구분력 |
| Mean Top-10% Lift | 4.39x | 상위 10% 위험 후보에 사고 신호가 전체 평균보다 집중된 정도 |
| Monte Carlo mean Jaccard | 0.503 | 반복 실험에서 Top-20 후보 집합이 겹치는 정도의 참고값 |

### AUC의 한계

- 순위 구분력을 보여주지만 calibration을 보장하지 않습니다.
- 높은 AUC가 실제 시설 설치 효과를 뜻하지 않습니다.
- class imbalance 상황에서 운영상 필요한 Top-k 성능을 충분히 설명하지 못할 수 있습니다.

### Top-10% Lift의 가치

현장 검토 자원이 제한된 상황에서는 전체 정확도보다 상위 후보에 실제 사고 신호가 얼마나 집중되는지가 중요합니다. Lift는 우선순위 모델의 실무적 효율을 설명하기 좋습니다.

### Jaccard 0.503의 해석

Top-20 후보가 반복 실행에서 완전히 고정적이지 않다는 뜻입니다. 따라서 20위와 21위의 미세한 순위를 확정적 사실처럼 해석하기보다 **후보군 수준의 불확실성**을 인정해야 합니다.

---

## 10. 최종 공개 점수

### 공개 정본

```text
RiskScore_A_grid
RiskScore_A_norm_grid
grid_rank
```

공개 저장소의 최종 검토 순서는 `docs/data/gyosan_effect_reduction_by_gid.csv`의 `RiskScore_A_norm_grid`와 `grid_rank`를 기준으로 합니다.

`scripts/build_portfolio_evidence.py`가 상위 20개를 다음 산출물로 변환합니다.

```text
docs/data/public_top20_priority.csv
docs/images/public-top20-priority-preview.svg
```

### 중요한 lineage 한계

공개 저장소에는 full retraining의 `pred_risk`에서 `RiskScore_A_grid`까지 이어지는 전체 비공개 데이터 lineage가 없습니다.

따라서 다음 두 가지를 구분해야 합니다.

1. **정본 모델 정의**: 공간 좌표 포함 Random Forest와 출력 구조
2. **정본 공개 evidence**: 추적된 `RiskScore_A_norm_grid`와 Top-20 결과

둘이 동일 실행에서 직접 이어졌다고 완전 재산출 가능한 수준으로 주장하지 않습니다.

---

## 11. Core·Auxiliary·Legacy 구분

### Core

- 100m grid integration
- feature preparation
- 공간 좌표 포함 Random Forest
- LORO validation
- 하남교산 770개 격자 적용
- `RiskScore_A_norm_grid`, `grid_rank`
- Public Top-20과 field-review handoff

### Auxiliary

- 유사격자 matching
- 휴리스틱 우선순위 점수
- 인프라 수요 예측
- k=10/20/30 시설 입지·coverage scenario
- 결과 시각화
- ARI target과 공간 회귀 진단

### Legacy

- blended GRF/GWRF 가중치 실험
- 기존 GRF/GWRF 파일명과 컬럼명
- 공개 원본이 없는 외부 결과 의존 실험

### 왜 구분했는가

프로젝트가 발전하면서 여러 점수와 notebook 경로가 생겼습니다. 이를 하나의 최종 모델처럼 말하면 서로 다른 Top-20과 평가 기준이 충돌합니다. 정본을 고정하고 나머지를 보조·역사적 실험으로 분리해 claim을 통제했습니다.

---

## 12. 휴리스틱 경로와 정본 점수를 섞으면 안 되는 이유

`07_gyosan_priority_ranking.ipynb`의 휴리스틱은 다음과 같습니다.

```text
유사_고위험_여부 × 2
+ 도로_격자_여부
+ 학교_비율 × 3
+ 유사도
```

이 점수의 기록된 Top-20은 현재 공개 `RiskScore_A_norm_grid` Top-20과 다릅니다.

`09_facility_site_selection.ipynb`도 해당 휴리스틱을 입력으로 한 입지·coverage prototype입니다. 따라서 이 경로는 auxiliary이며 최종 공개 순위나 정본 모델 성능으로 말하지 않습니다.

---

## 13. 현장 검토 인계

모델 결과는 다음 결정을 대신하지 않습니다.

- 실제 도로 기하 구조
- 보행자·차량 동선
- 학교·정류장·생활시설 맥락
- 기존 안전시설 상태
- 토지 이용과 개발 계획
- 법규와 설치 가능성
- 예산과 유지관리 비용
- 최신 사고와 민원 정보

### 올바른 사용 방식

```text
Top-20 risk candidates
→ 현장 확인 순서 결정
→ 교통공학·정책·예산 검토
→ 설치 후보 재평가
→ 실제 의사결정
```

모델은 “설치하라”가 아니라 “여기부터 확인하라”를 말합니다.

---

## 14. Scenario 분석

개입 전·후 시각화는 실제 사후 효과가 아니라 가정한 안전시설 개입 시 위험도가 어떻게 달라질 수 있는지 보여주는 scenario입니다.

### 말해도 되는 것

- 가정한 개입 하에서 점수 분포가 어떻게 변하는지
- 우선 후보가 어디에 집중되는지
- 여러 k 또는 coverage 조건을 비교한 prototype

### 말하면 안 되는 것

- 시설 설치로 실제 사고가 몇 건 감소했다
- 특정 후보의 사고 예방 효과가 검증됐다
- causal effect를 추정했다

---

## 15. 공개 증거 정책

공개 저장소는 full retraining 저장소가 아니라 **public-safe evidence 저장소**입니다.

### 공개 확인 가능

- 정본 범위와 방법론
- 100m 격자와 데이터 범위
- LORO 요약 지표
- 공개 `RiskScore_A_norm_grid`와 Top-20
- SVG evidence
- field-review handoff
- evidence audit와 CI 검사

### `needs confirmation`

- fold-level LORO 원본
- run-level Monte Carlo 원본
- full model → public score 전체 lineage
- 시설 패키지·추천 사유 최종 원본
- 검증 가능한 dashboard 운영 URL

### `not available`

- 실제 현장 점검 결과
- 안전시설 설치 결과
- 사고 감소 사후 검증

---

## 16. 검증과 evidence integrity

### 검증 목표

- 공개 Top-20이 canonical source와 일치하는가?
- 점수가 내림차순으로 정렬되는가?
- CSV와 SVG evidence가 같은 결과를 말하는가?
- README와 문서가 legacy 점수를 최종 결과처럼 주장하지 않는가?
- 공개 범위를 넘어서는 claim이 없는가?

### 재현 범위

- 공개 evidence 생성과 검증은 재현할 수 있습니다.
- 비공개 원천 데이터가 필요한 full grid integration과 retraining은 공개 범위 밖입니다.
- 공개 결과의 reviewability와 full model reproducibility를 구분합니다.

---

## 17. 핵심 설계 선택과 이유

### 17.1 왜 100m 격자인가

행정구역보다 현장 단위에 가깝고, 서로 다른 공간 데이터를 동일 단위로 통합하며, 신도시에도 같은 구조를 적용할 수 있기 때문입니다.

### 17.2 왜 좌표를 feature로 넣었는가

위치에 따른 배경 패턴을 모델이 활용하게 하기 위해서입니다. 다만 지역 외삽 위험이 있어 LORO 검증과 함께 해석합니다.

### 17.3 왜 LORO인가

인접 공간의 유사성으로 인한 random split 낙관성을 줄이고, 실제 새로운 지역 적용 질문과 검증 구조를 맞추기 위해서입니다.

### 17.4 왜 AUC와 Top-10% Lift를 함께 보는가

AUC는 전체 순위 구분력, Lift는 제한된 검토 자원을 상위 후보에 투입할 때의 집중도를 보여줍니다.

### 17.5 왜 모델 점수와 설치 결정을 분리했는가

시설 설치는 모델에 없는 법규·예산·현장 구조·정책 목표를 포함합니다. 분석은 우선순위 후보를 좁히는 역할에 한정합니다.

### 17.6 왜 정본을 frozen했는가

여러 실험 경로가 계속 추가되면 최종 모델과 점수가 불명확해집니다. 확장보다 claim consistency와 evidence integrity를 우선했습니다.

---

## 18. 반드시 말해야 하는 한계

- 원본 공모전 데이터가 공개되지 않아 full retraining은 재현할 수 없습니다.
- `pred_risk`에서 공개 `RiskScore_A_grid`까지 전체 lineage는 공개 확인이 제한됩니다.
- 공개 AUC와 Lift는 전이 검증용 classification setup의 지표입니다.
- 좌표 feature는 공간 패턴을 활용하지만 지역 위치를 외울 위험이 있습니다.
- 격자 기반 결과는 MAUP와 경계 효과의 영향을 받습니다.
- 하남교산의 실제 사고 이력이 충분하지 않아 target 지역 성능을 직접 검증하기 어렵습니다.
- Top-20 안정성은 완전하지 않으며 Jaccard 0.503은 후보 불확실성을 보여줍니다.
- 시설 입지·coverage 결과는 auxiliary scenario입니다.
- 현장 검토와 실제 사고 감소 효과는 검증되지 않았습니다.
- 점수는 상대적 우선순위이지 절대 사고 확률이 아닙니다.

---

## 19. 개선한다면

### 데이터와 공간 설계

- 도로 network distance와 교차로 topology를 추가합니다.
- 시간대별 교통량·보행량과 사고 유형을 분리합니다.
- 여러 grid size에서 sensitivity analysis를 수행합니다.
- 공간 lag와 neighborhood feature를 명시적으로 모델링합니다.

### 검증

- Spatial block CV와 LORO를 비교합니다.
- calibration curve와 Brier score를 추가합니다.
- Top-k precision·recall과 resource budget별 gain curve를 제공합니다.
- bootstrap으로 candidate rank uncertainty를 표시합니다.

### 모델

- count target에 맞는 Poisson·Negative Binomial 계열 baseline을 비교합니다.
- gradient boosting과 spatial model을 비교합니다.
- coordinate feature 제거 ablation을 수행합니다.
- SHAP 또는 permutation importance를 지역별로 안정성 검토합니다.

### 운영과 현장

- 현장 조사 결과를 feedback label로 수집합니다.
- 설치 전·후 분석은 causal design을 별도로 설계합니다.
- 정책 담당자가 후보를 보류·승인·재검토한 이유를 기록하는 decision log를 추가합니다.

---

## 20. 예상 면접 질문과 답변 핵심

### Q1. 왜 100m 격자를 사용했나요?

행정구역 평균이 가리는 지역 내부 차이를 표현하고, 위험 산정과 현장 검토를 같은 단위로 연결하기 위해서입니다.

### Q2. 왜 random split 대신 LORO를 사용했나요?

공간적으로 가까운 데이터가 train과 test에 섞여 성능이 부풀 수 있기 때문입니다. 새로운 지역 전이라는 실제 질문에 맞춰 지역 전체를 holdout했습니다.

### Q3. 좌표를 feature로 넣으면 leakage 아닌가요?

위치 패턴을 활용할 수 있지만 특정 지역을 외울 위험이 있습니다. 그래서 random split 성능이 아니라 LORO worst-case까지 확인하고 한계로 명시했습니다.

### Q4. Regressor와 classifier를 왜 둘 다 사용했나요?

Regressor는 연속 위험 신호와 순위를 생성하고, classifier는 사고 발생 여부를 기준으로 지역 전이 구분력을 검증합니다. 역할이 다릅니다.

### Q5. AUC 0.8604는 무엇의 성능인가요?

LORO classification validation에서 사고 신호가 있는 격자와 없는 격자를 구분한 평균 성능입니다. 최종 Regressor의 직접적인 회귀 성능으로 말하지 않습니다.

### Q6. Top-10% Lift 4.39배는 무슨 의미인가요?

상위 10% 위험 후보에 사고 발생 신호가 전체 격자 평균보다 4.39배 집중됐다는 뜻입니다. 제한된 현장 검토 자원 배분에 더 직접적인 지표입니다.

### Q7. Jaccard 0.503은 좋은 결과인가요?

후보군이 절반 정도 겹치는 수준의 참고값입니다. Top-20 경계 순위가 불안정할 수 있어 점 순위보다 후보군과 불확실성을 함께 봐야 합니다.

### Q8. 왜 `log1p(acc_count)`를 사용했나요?

0을 포함한 count target을 처리하고 큰 사고 건수의 영향과 오른쪽 꼬리를 완화하기 위해서입니다.

### Q9. `RiskScore_A_norm_grid`는 모델 예측 확률인가요?

아닙니다. 공개 검토용 정규화 위험 점수입니다. 절대 사고 확률이나 calibration된 probability로 해석하지 않습니다.

### Q10. 왜 공개 모델과 공개 점수 lineage를 분리해 말하나요?

비공개 원천 데이터와 전체 중간 산출물이 없어 `pred_risk`에서 공개 점수까지 완전 재산출할 수 없기 때문입니다. 확인 가능한 범위만 주장합니다.

### Q11. GRF나 GWRF를 구현한 프로젝트인가요?

정본 모델은 공간 좌표를 feature로 포함한 Random Forest입니다. GRF/GWRF는 legacy label이며 전용 geographically weighted random forest 구현으로 주장하지 않습니다.

### Q12. 휴리스틱 Top-20과 공개 Top-20이 왜 다른가요?

서로 다른 점수 경로입니다. 휴리스틱은 auxiliary experiment이고 공개 Top-20은 canonical public score 기준이므로 혼용하지 않습니다.

### Q13. 모델이 높은 점수를 준 곳에 바로 시설을 설치하면 되나요?

아닙니다. 모델은 현장 검토 순서를 제안할 뿐이며 도로 구조·법규·예산·기존 시설과 최신 현장 정보를 다시 확인해야 합니다.

### Q14. 실제 사고 감소 효과를 검증했나요?

아닙니다. 개입 전·후 그림은 scenario이며 실제 설치와 causal effect 데이터가 없습니다.

### Q15. 가장 큰 프로젝트 한계는 무엇인가요?

Target 지역의 실제 outcome 검증과 full public lineage가 없다는 점입니다. 그래서 의사결정 보조 신호와 공개 evidence 범위로 claim을 제한했습니다.

### Q16. 이 프로젝트를 비GIS 직무에 어떻게 설명하나요?

새로운 시장이나 지점에서 과거 outcome이 부족할 때 기존 지역 패턴을 전이 검증하고, 제한된 조사 자원을 고위험 후보부터 배분하는 risk prioritization 문제로 설명합니다.

### Q17. 다시 만든다면 무엇을 먼저 개선하겠나요?

Coordinate ablation, spatial block CV, rank uncertainty와 현장 feedback loop를 우선 추가하겠습니다.

---

## 21. 핵심 파일 읽는 순서

### 1단계 · 정본과 주장 범위

1. `README.md`
2. `docs/canonical_project_scope.md`
3. `docs/portfolio_case_study.md`
4. `docs/evidence_audit.md`

### 2단계 · 모델과 검증

1. `docs/grf_risk_methodology.md`
2. `scripts/run_grf_ranking.py`
3. `docs/reproducibility_and_validation.md`
4. LORO validation 관련 script·summary

### 3단계 · 공개 결과

1. `docs/data/gyosan_effect_reduction_by_gid.csv`
2. `scripts/build_portfolio_evidence.py`
3. `docs/data/public_top20_priority.csv`
4. `docs/images/public-top20-priority-preview.svg`
5. `docs/field-review-handoff.md`

### 4단계 · 경로 구분

1. `analysis_pipeline/README.md`
2. `01_grid_api_integration.ipynb`
3. `05_grf_feature_integration.ipynb`
4. `07_gyosan_priority_ranking.ipynb` — auxiliary로 읽기
5. `09_facility_site_selection.ipynb` — scenario prototype로 읽기

### 5단계 · 검증과 CI

1. `VERIFY.md`
2. `.github/workflows/verify.yml`
3. 공개 evidence integrity test

---

## 22. 3회독 학습법

### 1회독 · 정본 흐름만 익히기

```text
100m grid
→ RF risk signal
→ LORO validation
→ Gyosan transfer
→ public Top-20
→ field review
```

Auxiliary notebook과 legacy 명칭은 일단 넘깁니다.

### 2회독 · 모델과 검증 구분하기

- Regressor는 무엇을 출력하는가?
- Classifier LORO는 무엇을 검증하는가?
- AUC와 Lift는 어떤 target 기준인가?
- Public score는 어떤 파일에서 확인하는가?

### 3회독 · Claim boundary 말하기

- 무엇을 full reproducible이라고 할 수 없는가?
- 왜 GRF/GWRF라고 주장하지 않는가?
- 왜 Top-20은 설치 결정이 아닌가?
- 왜 scenario를 실제 효과라고 말할 수 없는가?
- Jaccard 0.503이 어떤 불확실성을 뜻하는가?

---

## 23. 면접 직전 체크리스트

- [ ] 30초 소개를 자연스럽게 말할 수 있다.
- [ ] 100m 격자를 선택한 이유를 설명할 수 있다.
- [ ] 학습 99,323개와 대상 770개 범위를 기억한다.
- [ ] 정본 모델이 공간 좌표 포함 Random Forest임을 말할 수 있다.
- [ ] Regressor와 LORO classifier 역할을 구분할 수 있다.
- [ ] Mean AUC 0.8604와 Top-10% Lift 4.39x를 해석할 수 있다.
- [ ] Worst holdout AUC 0.7979의 의미를 말할 수 있다.
- [ ] Jaccard 0.503을 과장하지 않고 설명할 수 있다.
- [ ] Public score와 model output lineage 한계를 말할 수 있다.
- [ ] Core / auxiliary / legacy를 구분할 수 있다.
- [ ] GRF/GWRF legacy label 문제를 설명할 수 있다.
- [ ] Top-20이 설치 결정이 아니라 현장 검토 순서임을 말할 수 있다.
- [ ] 실제 사고 감소 효과를 주장하지 않는 이유를 말할 수 있다.

---

## 24. 최종 안전 문장

> LH Traffic Safety는 기존 4개 시·구의 99,323개 100m 격자에서 교통·공간 위험 패턴을 학습하고 LORO로 지역 전이 가능성을 검증한 뒤, 하남교산 770개 격자의 공개 가능한 normalized risk score를 Top-20 현장 검토 순서로 정리한 프로젝트입니다. 정본 모델은 공간 좌표 포함 Random Forest이며, 공개 AUC와 Lift는 별도의 사고 발생 여부 기반 LORO 검증 결과입니다. 결과는 시설 설치 결정이나 사고 감소 인과효과가 아니라 제한된 현장 조사 자원의 우선순위를 돕는 위험 신호입니다.
