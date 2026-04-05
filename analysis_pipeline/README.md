# 분석 파이프라인

핵심 분석 노트북을 실행 순서대로 정리한 폴더입니다.

- 작업 디렉터리(`cwd`)는 이 폴더(`analysis_pipeline`)로 두는 것을 권장합니다.
- 일부 원본 데이터와 대용량 중간 산출물은 공개 저장소에서 제외되어 있습니다.

| 단계 | 파일명 | 역할 |
|------|--------|------|
| 01 | `01_grid_api_integration.ipynb` | API 데이터와 격자를 연동해 통합 테이블 기반 구축 |
| 02 | `02_grf_blended_weights.ipynb` | GRF global/local importance를 블렌딩 |
| 03 | `03_grf_risk_index.ipynb` | 블렌딩 가중치로 GRF 기반 위험지수 산출 |
| 04 | `04_gyosan_grid_matching.ipynb` | 하남교산과 4개 시·구 유사 격자 매칭 |
| 05 | `05_grf_feature_integration.ipynb` | GRF 기반 피처 보강·통합 |
| 07 | `07_gyosan_priority_ranking.ipynb` | 시설 설치 우선순위 산출 |
| 08 | `08_gyosan_infrastructure_forecast.ipynb` | 하남교산 인프라 수요 예측 |
| 09 | `09_facility_site_selection.ipynb` | 스마트 시설 입지 선정 |
| 10 | `10_gyosan_final_visualization.ipynb` | 최종 결과 시각화 |

## 참고

- `06_하남교산_GRF_SHAP.ipynb`는 공개 저장소에서 제외했습니다.
- `02` 실행 결과가 `03`의 입력으로 사용됩니다.
- `data/grf_06_outputs/`가 있어야 일부 GRF 단계가 동작합니다.
