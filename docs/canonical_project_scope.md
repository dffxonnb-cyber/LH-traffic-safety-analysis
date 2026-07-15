# LH 종결 정본 범위

- 확정일: 2026-07-15
- 상태: **frozen / canonical**
- 목적: 확장보다 종결을 우선하고, 최종 모델·점수·파이프라인·공개 주장 범위를 하나로 고정한다.

## 1. 최종 결정 요약

| 항목 | 정본 결정 |
| --- | --- |
| 문제 정의 | 사고 이력이 부족한 하남교산에서 어떤 `100m × 100m` 격자를 먼저 현장 검토할지 정하는 공간 위험 신호 분석 |
| 최종 모델 명칭 | **공간 좌표 포함 Random Forest** |
| 운영용 점수 모델 | `scripts/run_grf_ranking.py`의 `RandomForestRegressor`; 기본 정본 타깃은 `acc_count` |
| 전이 검증 모델 | 사고 발생 여부를 대상으로 한 Random Forest 분류 + Leave-One-Region-Out; 점수 생성기가 아니라 전이 가능성 검증 장치 |
| 최종 모델 산출 컬럼 | full-data 실행 기준 `pred_risk`, `rank_desc` |
| 최종 공개 점수 | `docs/data/gyosan_effect_reduction_by_gid.csv`의 `RiskScore_A_norm_grid`, `grid_rank` |
| 최종 공개 결과 | `docs/data/public_top20_priority.csv`와 대응 SVG evidence |
| 핵심 공개 성능 | Mean AUC `0.8604`, Worst holdout AUC `0.7979`, Mean Top-10% Lift `4.39x`, Monte Carlo mean Jaccard `0.503` |
| 최종 용도 | 설치 결정이나 사고 감소 예측이 아니라 **현장 검토 우선순위 신호** |

`GRF`·`GWRF`는 파일명과 기존 컬럼의 호환을 위해 남아 있는 legacy label이다. 정본 문구에서 전용 geographically weighted random forest를 구현했다고 주장하지 않는다.

## 2. 최종 점수 체계

### 2.1 정본 모델 출력

`scripts/run_grf_ranking.py`는 다음 구조를 정본 모델 실행 방식으로 사용한다.

- estimator: `RandomForestRegressor`
- 기본 target: `log1p(acc_count)`
- features: `AADT_mean`, `velocity_mean`, `FRIN_mean`, `TI_mean`, 격자 중심 `x_coord`, `y_coord`
- 기본 설정: `n_estimators=500`, `max_depth=18`, `min_samples_leaf=5`, `random_state=42`
- output: `pred_log_risk`, `pred_risk`, `rank_desc`, `rank_pct`

`ARI` target 실행은 민감도·보조 진단 경로로 유지하되, 대표 포트폴리오 문구의 기본 모델 타깃은 `acc_count`로 고정한다.

### 2.2 정본 공개 점수

공개 저장소에서 직접 확인 가능한 하남교산 최종 검토 순서는 다음 컬럼으로 고정한다.

- raw tracked score: `RiskScore_A_grid`
- normalized public review score: `RiskScore_A_norm_grid`
- public review order: `grid_rank`

이 컬럼은 `docs/data/gyosan_effect_reduction_by_gid.csv`에 추적되어 있으며, `scripts/build_portfolio_evidence.py`가 상위 20개를 `public_top20_priority.csv`와 SVG로 변환한다.

다만 공개 저장소에는 full retraining부터 이 CSV까지의 전체 원본 데이터 lineage가 없으므로, `pred_risk`와 `RiskScore_A_grid`가 동일 실행에서 직접 이어졌다고 재산출 가능한 수준으로 주장하지 않는다. **정본 모델 정의**와 **정본 공개 evidence**를 구분해 관리한다.

### 2.3 정본에서 제외되는 점수

| 점수·산출물 | 분류 | 처리 |
| --- | --- | --- |
| `우선순위_점수` (`07_gyosan_priority_ranking.ipynb`) | auxiliary / legacy heuristic | 유사 고위험 여부, 도로, 학교 비율, 유사도를 합친 중간 휴리스틱. 공개 최종 점수로 사용하지 않음 |
| `09_facility_site_selection.ipynb`의 k=10/20/30 선정 | auxiliary siting prototype | `우선순위_점수`를 입력으로 한 시설 입지·커버리지 실험. 최종 공개 Top-20과 분리 |
| `위험점수`, `위험점수_정규화`, `ARI`, `ARI_정규화` | observed baseline / diagnostic | 기존 도시의 관측 기반 위험 설명과 비교용. 하남교산 최종 공개 점수 아님 |
| `02`·`03`의 blended GRF/GWRF 가중치 경로 | legacy experiment | 역사적 실험과 호환을 위해 보존하되 정본 reviewer path에서 제외 |
| SLM/SEM/SAM 결과 | diagnostic | 공간 의존성 진단용. 최종 위험 순위 모델이 아님 |
| `R²=0.006` 점수 비교 | diagnostic | 두 점수 체계의 낮은 선형 설명력 확인용. 성능 또는 순위 일치 근거가 아님 |

`07` 노트북의 기록된 Top-20과 현재 공개 `RiskScore_A_norm_grid` Top-20은 서로 다르다. 따라서 두 경로를 같은 최종 결과로 합치거나 혼용하지 않는다.

## 3. 정본 핵심 파이프라인

### 3.1 모델·분석 정본 흐름

1. `01_grid_api_integration.ipynb`: 4개 기존 시·구 격자 데이터 통합
2. `05_grf_feature_integration.ipynb` 및 승인된 전처리: 모델 입력 피처 정리
3. `scripts/run_grf_ranking.py`: 공간 좌표 포함 Random Forest 연속 위험 신호 산출
4. LORO validation package: 지역을 하나씩 제외해 AUC와 Top-10% Lift 검증
5. 하남교산 transfer / matching 단계: 대상 770개 격자에 위험 신호 적용
6. normalized target score + rank: 하남교산 검토 순서 생성
7. Top-k field-review handoff: 설치 결정이 아닌 현장 검토 후보로 전달

원본 데이터가 필요한 1~6단계의 완전 재실행은 공개 저장소 범위 밖이다.

### 3.2 공개 evidence 정본 흐름

1. `docs/data/gyosan_effect_reduction_by_gid.csv`
2. `scripts/build_portfolio_evidence.py`
3. `docs/data/public_top20_priority.csv`
4. `docs/images/public-top20-priority-preview.svg`
5. `docs/evidence_audit.md`
6. `docs/field-review-handoff.md`

채용담당자·리뷰어는 이 공개 흐름으로 결과, 검증 경계, 현장 인계 방식을 확인한다.

## 4. legacy와 auxiliary 처리 규칙

### Core

- 공간 좌표 포함 Random Forest 정의와 실행 스크립트
- LORO 성능 요약
- 하남교산 770개 격자 적용 범위
- 공개 `RiskScore_A_norm_grid` / `grid_rank`
- public Top-20 evidence와 field-review handoff

### Auxiliary

- `04` 유사격자 매칭
- `07` 휴리스틱 우선순위
- `08` 인프라 수요 예측
- `09` 시설 입지·최대 커버리지 시나리오
- `10` 결과 시각화
- ARI target, SLM/SEM/SAM, 점수 체계 비교

### Legacy

- `02`·`03`의 GRF/GWRF blended-weight 경로
- `GRF`, `GWRF`가 포함된 기존 파일명·컬럼명
- 공개 저장소에 원본이 없는 외부 `mg_gwrf_results.csv` 의존 실험

legacy와 auxiliary 파일은 삭제하지 않는다. 다만 README의 대표 주장, 이력서 문장, 공개 Top-20 근거에는 사용하지 않는다.

## 5. `needs confirmation` 최종 처리

아래 항목은 종결 시점에도 억지로 채우지 않는다.

| 항목 | 최종 상태 | 이유 |
| --- | --- | --- |
| fold-level `transfer_loro_detail.csv` | `needs confirmation` | 요약 지표는 있으나 공개 원본 없음 |
| run-level `gyosan_mc_runs.csv` | `needs confirmation` | mean Jaccard 요약만 공개 |
| full model → `RiskScore_A_grid` 전체 lineage | `needs confirmation` | 비공개 원천 데이터와 전체 중간 산출물 필요 |
| 시설 패키지·추천 사유 최종 결과 | `needs confirmation` | 생성 로직은 있으나 final public-safe result file 없음 |
| 검증 가능한 Dashboard URL | `needs confirmation` | 코드와 fallback은 있으나 운영 URL evidence 없음 |
| 현장 점검 결과·사고 감소 효과 | `not available` | 실제 설치·사후 검증 데이터 없음 |

상태를 `confirmed public artifact`로 바꾸려면 최소한 다음이 모두 필요하다.

1. 저장소에 실제 결과 파일이 존재할 것
2. 입력과 생성 코드가 연결될 것
3. CI 또는 재현 명령으로 다시 만들 수 있을 것
4. README·evidence audit·status CSV가 동시에 갱신될 것

## 6. 종결 이후 변경 규칙

정본 확정 이후에는 다음 작업만 허용한다.

- 명백한 버그 수정
- 끊어진 링크·잘못된 파일명 수정
- 공개 evidence lineage 보강
- 과장되거나 충돌하는 문구 정정
- 테스트와 CI 보강

새 모델 추가, 새 점수 조합, 새 가중치 실험, 새 Top-k 경로 확장은 하지 않는다. 새로운 실험이 필요하면 본 프로젝트의 정본을 바꾸지 않고 별도 브랜치·별도 저장소에서 진행한다.

## 7. 최종 안전 문장

> 4개 기존 시·구의 100m 격자에서 학습한 공간 위험 신호를 LORO로 검증하고, 하남교산의 공개 가능한 normalized risk score를 현장 검토 우선순위로 정리했다. 결과는 실제 시설 설치 결정이나 사고 감소 인과효과가 아니라, 제한된 현장 조사 자원을 어디부터 투입할지 돕는 의사결정 보조 신호다.
