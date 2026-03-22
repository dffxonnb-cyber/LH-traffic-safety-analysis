# 파이프라인 (실행 순서)

아래 노트북을 **번호 순서대로** 실행하세요. 각 노트북의 cwd는 이 폴더(`파이프라인`)로 두면 `../../data/` 경로가 올바르게 동작합니다.

| 번호 | 파일명 | 설명 |
|------|--------|------|
| 01 | 01_격자_API연동.ipynb | API 데이터 격자 연동 → `격자_최종통합.csv` |
| 02 | 02_GRF_블렌딩가중치.ipynb | GRF global·local 블렌딩 → blended_weights CSV |
| 03 | 03_GRF_위험지수.ipynb | 5그룹 가중치로 Risk_Base(위험지수) 산출 |
| 04 | 04_하남교산_유사격자매칭.ipynb | 하남교산 ↔ 4시·구 유사 격자 매칭 |
| 05 | 05_GRF_보강통합.ipynb | GRF 보강·통합 |
| 06 | 06_하남교산_GRF_SHAP.ipynb | 하남교산 GRF·SHAP |
| 07 | 07_하남교산_설치우선순위.ipynb | 설치 우선순위 산출 → `하남교산_설치우선순위_격자.csv` |
| 08 | 08_하남교산_인프라예측.ipynb | 하남교산 인프라 예측 |
| 09 | 09_시설_입지선정.ipynb | 스마트 시설 입지 선정 (k=10/20/30) |
| 10 | 10_하남교산_종합시각화.ipynb | 하남교산 종합 시각화 |

## 사전 조건

- `data/grf_06_outputs/` 에 `global_importance`, `local_importance`, `shap_importance`, `X_shap` CSV가 있어야 02·03 실행 가능
- 02 실행 후 03 실행 (03이 02의 blended_weights 사용)
