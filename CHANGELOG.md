# 변경 이력

## 2026-07-15

- 최종 모델 명칭을 `공간 좌표 포함 Random Forest`로 확정
- 운영용 모델 출력(`pred_risk`, `rank_desc`)과 공개 최종 점수(`RiskScore_A_norm_grid`, `grid_rank`)의 역할을 분리
- 공개 저장소만으로 확인할 수 없는 full model-to-public-score lineage를 `needs confirmation`으로 고정
- `07_gyosan_priority_ranking.ipynb`의 휴리스틱 `우선순위_점수`와 `09_facility_site_selection.ipynb`의 입지선정 결과를 auxiliary 경로로 분류
- `02`·`03` GRF/GWRF blended-weight 경로와 기존 명칭을 legacy로 분류
- `docs/canonical_project_scope.md` 추가
- 재현성 가이드, evidence audit, field-review handoff, 문서 인덱스를 정본 기준으로 동기화
- 존재하지 않던 `public_evidence_audit.json` 링크를 실제 `evidence_audit.md` 링크로 수정
- 공개 Top-20 source 일치, 점수 정렬, claim boundary, legacy 동결 상태를 테스트로 고정
- CI에서 Python compile, evidence 재생성, 생성물 diff 검사를 수행하도록 보강

## 2026-03-23

- README를 `재현 범위`, `검증 수치`, `의사결정 가치` 중심 구조로 재정리
- [docs/reproducibility_and_validation.md](./docs/reproducibility_and_validation.md) 추가
- 공개 저장소 기준 검증 가능 범위와 비공개 데이터 의존 범위를 명시

## 2026-04-16

- work branch push verification
