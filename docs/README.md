# 문서 개요

이 폴더는 공개 저장소 기준으로 핵심 문서를 빠르게 찾을 수 있도록 정리한 인덱스입니다.

## 프로젝트 목적

이 프로젝트는 4개 시·구의 사고·도로·교통·공간 패턴을 바탕으로 하남교산의 교통안전 위험도와 시설 설치 우선순위를 도출합니다. 결과는 실제 설치 효과가 아니라 공개 가능한 범위 안에서 검토 가능한 **현장 점검 우선순위 신호**로 해석합니다.

## 먼저 볼 문서

1. [../README.md](../README.md)
2. [evidence_audit.md](evidence_audit.md)
3. [reproducibility_and_validation.md](reproducibility_and_validation.md)
4. [portfolio_case_study.md](portfolio_case_study.md)
5. [../analysis_pipeline/README.md](../analysis_pipeline/README.md)
6. [risk_index_methodology.md](risk_index_methodology.md)
7. [grf_risk_methodology.md](grf_risk_methodology.md)
8. [MODEL_RUN_GUIDE.md](MODEL_RUN_GUIDE.md)

## 현재 저장소 구조

```text
LH-traffic-safety-analysis/
├── analysis_pipeline/   # 핵심 실행 노트북
├── research_notebooks/  # 공간 RF 보강 분석, SHAP, 인사이트 탐색
├── dashboard/           # Streamlit 대시보드
├── scripts/             # 실행/요약/시각화 보조 스크립트
├── docs/                # 방법론, 변수 정의, 적용 배경, 실행 가이드
└── data/                # 공개 저장소에서는 원본 데이터 미포함
```

## 핵심 문서

| 문서 | 용도 |
|------|------|
| [evidence_audit.md](evidence_audit.md) | 공개 저장소에서 확인 가능한 근거, `needs confirmation`, 미보유 evidence를 한 번에 정리 |
| [reproducibility_and_validation.md](reproducibility_and_validation.md) | 재현성 가이드, TOP35 검증 요약, LORO·Lift·Jaccard·R² 해석 |
| [portfolio_case_study.md](portfolio_case_study.md) | 포트폴리오 요약, 공개 증거, 이력서 문장 |
| [competition_context.md](competition_context.md) | 공모전 배경, 데이터 출처, 요구사항 |
| [grid_variable_dictionary.md](grid_variable_dictionary.md) | 격자 단위 변수 정의 |
| [risk_index_methodology.md](risk_index_methodology.md) | 관측 기반 위험점수와 ARI 산출 근거 |
| [grf_risk_methodology.md](grf_risk_methodology.md) | 공간 좌표 포함 Random Forest 기반 예측 위험지수 산출 근거 |
| [MODEL_RUN_GUIDE.md](MODEL_RUN_GUIDE.md) | Python 스크립트 실행 가이드 |
| [qgis_submission_guide.md](qgis_submission_guide.md) | QGIS 제출용 결과 정리 가이드 |
| [gyosan_site_context.md](gyosan_site_context.md) | 하남교산 적용 배경과 해석 방향 |
| [feature_engineering_plan.md](feature_engineering_plan.md) | 파생 변수와 간접 변수 설계 방향 |

## 보조 문서

| 문서 | 용도 |
|------|------|
| [regional_domain_summary.md](regional_domain_summary.md) | 지역별 도메인 배경 |
| [regional_insights_summary.md](regional_insights_summary.md) | 지역별 해석 요약 |
| [regional_terrain_visual_notes.md](regional_terrain_visual_notes.md) | 지형/시각화 메모 |
| [indirect_feature_data_guide.md](indirect_feature_data_guide.md) | 외부 데이터 후보 정리 |
| [postgis_integration_guide.md](postgis_integration_guide.md) | PostGIS 연동 참고 |
| [PROJECT_DOCUMENTATION.md](PROJECT_DOCUMENTATION.md) | 확장형 프로젝트 설명서 |

## 참고

- 발표 자료 PDF: [safe_new_town_for_vulnerable_road_users.pdf](safe_new_town_for_vulnerable_road_users.pdf)
