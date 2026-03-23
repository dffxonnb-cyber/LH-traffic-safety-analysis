# 재현성 및 검증 가이드

## 공개 저장소에서 바로 검증 가능한 범위

| 범위 | 확인 방법 | 비고 |
|------|-----------|------|
| 핵심 결과 화면 | [README](../README.md)의 2개 지도 이미지 확인 | 대표 결과와 시나리오 비교를 바로 확인 가능 |
| 방법론 | [grf_risk_methodology.md](./grf_risk_methodology.md), [risk_index_methodology.md](./risk_index_methodology.md) | 위험도 정의, 전이 논리, 정규화 기준 |
| 검증 수치 | [TOP35_UPGRADE_REPORT.md](./TOP35_UPGRADE_REPORT.md) | LORO, lift, 강건성, 실행용 컬럼 정리 |
| 교산 사후 시나리오 매핑 | [gyosan_effect_reduction_by_gid.csv](./data/gyosan_effect_reduction_by_gid.csv) | 교산 100m 격자 기준 저감 매핑 결과 |
| UI/코드 구조 | [dashboard/](../dashboard/), [analysis_pipeline/](../analysis_pipeline/) | 대시보드와 분석 흐름 분리 상태 확인 가능 |

## 공개 저장소만으로는 재현되지 않는 범위

- 원본 공모전 데이터가 필요한 격자 통합 테이블 생성
- GRF 학습 및 지역별 전이 결과 재산출
- 하남교산 최종 우선순위 CSV의 원본 단계 전체 재실행

## 왜 완전 재현이 제한되는가

- 공모전 원본 데이터는 공개 저장소에 포함할 수 없습니다.
- 일부 핵심 산출물은 승인된 격자/시설/교통량/인구 데이터가 있어야 생성됩니다.
- 따라서 공개 저장소는 `결과를 검토하고 구조를 이해하는 저장소`로 설계했고, 원본 데이터가 필요한 단계는 문서로 검증 가능성을 보완했습니다.

## 대신 무엇으로 신뢰를 확인할 수 있는가

1. [TOP35_UPGRADE_REPORT.md](./TOP35_UPGRADE_REPORT.md)에서 전이 성능과 강건성 수치를 확인합니다.
2. [grf_risk_methodology.md](./grf_risk_methodology.md)에서 왜 RF/GRF 기반 방식을 택했는지 확인합니다.
3. [gyosan_effect_reduction_by_gid.csv](./data/gyosan_effect_reduction_by_gid.csv)에서 공개 가능한 수준의 격자 단위 시나리오 결과를 검토합니다.
4. [build_readme_key_visuals.py](../scripts/build_readme_key_visuals.py)에서 README 시각화 생성 로직을 확인합니다.

## 평가 기준 요약

- 전이 검증: Leave-One-Region-Out
- 분리력: Mean AUC `0.8604`
- 핫스팟 포착력: Mean Top-10% Lift `4.39x`
- 선정 강건성: Monte Carlo mean Jaccard `0.503`
- 설명 가능성: `recommended_package`, `recommendation_reason` 컬럼 제공

## 한계

- README의 적용 전/후 이미지는 실측 사후 효과가 아니라 시나리오 기반 예상 변화입니다.
- 공개 저장소만으로 완전한 재학습은 불가능합니다.
- 대신 의사결정 흐름, 검증 방식, 공개 가능한 결과 증거를 우선 확인할 수 있도록 구조를 정리했습니다.
