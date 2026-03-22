# LH Traffic Safety Analysis

포트폴리오 및 GitHub 공개용으로 정리한 버전입니다.

- 원본 프로젝트 폴더: `1최종_LH`
- 공개 저장소에는 원본/가공 데이터와 일부 대용량 산출물을 포함하지 않았습니다.
- 이 저장소는 `무엇을 분석했고`, `어떤 순서로 실행하는지`가 바로 보이도록 구조를 재정리한 버전입니다.

## Project Summary

이 프로젝트는 4개 시·구의 교통안전 패턴을 학습한 뒤 하남교산에 전이 적용해 스마트 교통안전시설 우선순위를 제안하는 분석 프로젝트입니다.

- 분석 대상: 성남, 화성, 하남, 송파
- 적용 대상: 하남교산
- 분석 단위: 100x100m grid
- 핵심 결과: 위험점수, ARI, 유사 격자 매칭, 설치 우선순위, 대시보드

## Repository Structure

| 경로 | 역할 |
|------|------|
| [analysis_pipeline/](./analysis_pipeline/) | 순서대로 실행하는 핵심 분석 노트북 |
| [research_notebooks/](./research_notebooks/) | GWRF/SHAP, 인사이트 탐색, 보강 분석 자료 |
| [dashboard/](./dashboard/) | Streamlit 대시보드 |
| [scripts/](./scripts/) | 모델 실행, 요약표 생성, 시각화 보조 스크립트 |
| [docs/](./docs/) | 방법론, 변수 정의, 적용 배경, 실행 가이드 |
| [data/](./data/) | 공개 저장소에서는 원본 데이터 미포함 |

## Recommended Reading Order

1. [docs/README.md](./docs/README.md)
2. [analysis_pipeline/README.md](./analysis_pipeline/README.md)
3. [docs/risk_index_methodology.md](./docs/risk_index_methodology.md)
4. [docs/grf_risk_methodology.md](./docs/grf_risk_methodology.md)
5. [docs/model_run_guide.md](./docs/model_run_guide.md)

## Core Pipeline

핵심 분석 흐름은 아래 노트북 순서입니다.

1. `01_grid_api_integration.ipynb`
2. `02_grf_blended_weights.ipynb`
3. `03_grf_risk_index.ipynb`
4. `04_gyosan_grid_matching.ipynb`
5. `05_grf_feature_integration.ipynb`
6. `07_gyosan_priority_ranking.ipynb`
7. `08_gyosan_infrastructure_forecast.ipynb`
8. `09_facility_site_selection.ipynb`
9. `10_gyosan_final_visualization.ipynb`

상세 설명은 [analysis_pipeline/README.md](./analysis_pipeline/README.md)에 정리했습니다.

## Data Notice

- 원본 공모전 데이터와 대용량 파생 데이터는 저장소에 포함하지 않았습니다.
- 로컬 재현 시 `data/` 구조를 원본 프로젝트와 동일하게 맞춰야 합니다.
- 데이터 출처와 과제 배경은 [docs/competition_context.md](./docs/competition_context.md)를 참고하세요.

## Main Outputs

| 파일 | 설명 |
|------|------|
| `data/통합_데이터/격자_최종통합.csv` | 격자별 통합 피처 테이블 |
| `data/통합_데이터/하남교산_유사격자_매칭.csv` | 하남교산 유사 격자 매칭 결과 |
| `data/통합_데이터/하남교산_설치우선순위_격자.csv` | 최종 설치 우선순위 결과 |

## Documentation

- 개요 및 문서 인덱스: [docs/README.md](./docs/README.md)
- 실행 가이드: [docs/model_run_guide.md](./docs/model_run_guide.md)
- 위험지수 정의: [docs/risk_index_methodology.md](./docs/risk_index_methodology.md)
- GRF 기반 방법론: [docs/grf_risk_methodology.md](./docs/grf_risk_methodology.md)
- 하남교산 적용 배경: [docs/gyosan_site_context.md](./docs/gyosan_site_context.md)
