# ipynb·py 파일 정리 가이드 (필수 vs 불필요·중복)

**목적**: 전체 데이터 크기·유지보수 부담을 줄이기 위해, **진짜 필요 없는 파일**과 **용량을 많이 쓰는 데이터**를 구분합니다.

---

## 1. 삭제 권장 (불필요·중복)

### 1-1. team_share_package 폴더 **전체**

| 구분 | 내용 |
|------|------|
| **위치** | `1최종_LH/team_share_package/` |
| **파일 수** | 노트북 22개 + docs 1개 + data 내 CSV 8개 |
| **판단** | 메인 `notebooks/`, `data/통합_데이터/`와 **동일·유사 복사본**. 분석 진행에 따라 달라지므로 정본은 메인만 두는 것이 좋음. |
| **조치** | **폴더 통째로 삭제** 권장. (이전에 삭제했어도 복원됐다면 다시 삭제.) |

---

### 1-2. 노트북 **중복·실험용** (삭제 또는 아카이브)

| 파일 | 판단 | 이유 |
|------|------|------|
| `notebooks/06_shap_100x100.ipynb` | **삭제 후보** | `06_grf_shap_100x100.ipynb`와 **내용 거의 동일** (GRF+SHAP, 설정만 약간 다름). 하나만 남기면 됨. |
| `notebooks/06_grf_shap_100x100.ipynb` | **선택 보관** | 위와 쌍. **mg.gpkg**·`grid_100m_traffic_final_*` 등 **메인 파이프라인(격자_최종통합)과 다른 데이터 소스** 사용. 하남/미사 전용 실험이면 참고용으로 하나만 남기고, 사용 안 하면 둘 다 삭제 가능. |
| `notebooks/10_GWRF_vs_Greedy_Algorithm_Comparison.ipynb` | **선택 보관** | GWRF vs 09번 탐욕 알고리즘 **비교용**. `mg_gwrf_results.csv`(Downloads) 등 **외부 산출물**에 의존. 방법론 비교가 필요 없으면 삭제해도 됨. |

- **정리**: `06_shap_100x100.ipynb`는 **삭제**해도 됨. `06_grf_shap_100x100.ipynb`는 “mg.gpkg 기반 실험” 쓰면 하나만 보관. `10_GWRF_vs_Greedy`는 비교 분석 안 하면 삭제 가능.

---

### 1-3. Python 캐시 (삭제 가능)

| 위치 | 설명 |
|------|------|
| `1최종_LH/__pycache__/` | Python 바이트캐시. **실행에 불필요**. 삭제해도 되고, `.gitignore`에 `__pycache__/` 넣어 두면 됨. |
| `__pycache__/시각화.py` | `시각화.py` 모듈의 캐시. 원본 `시각화.py`가 프로젝트에 없으면 사용처 없음 → 캐시만 삭제 가능. |

---

## 2. 데이터 용량이 과도한 부분 (정리 권장)

**“전체 데이터가 너무 크다”**면 아래가 주원인일 가능성이 큼.

### 2-1. `data/grf_06_outputs/`

| 항목 | 내용 |
|------|------|
| **현황** | run별 타임스탬프 CSV **185개 이상** (약 18 run × 10종 파일). |
| **원인** | `06_grf_shap_100x100.ipynb`(또는 06_shap) 실행할 때마다 **새 타임스탬프 세트**가 쌓임. |
| **조치** | **최신 1~2개 run만 남기고** 나머지 삭제 또는 `archive/`로 이동. `data/grf_06_outputs/README.md`에 안내되어 있음. |

### 2-2. team_share_package 내 data

- `team_share_package/data/통합_데이터/` 안 CSV들은 메인 `data/통합_데이터/`와 **중복**.
- **team_share_package 폴더를 삭제**하면 이 용량도 함께 줄어듦.

---

## 3. 필수로 두는 것이 좋은 것 (삭제 비권장)

### 3-1. docs/README 실행 순서에 있는 노트북 (파이프라인)

- **미성년자_분석**: 00~06  
- **인구_전처리**: 01~02  
- **노인_분석**: 01~04  
- **인사이트_분석**: 01~05  
- **구체적인_EDA**: 01~08  
- **시각화_공유**: 01~05  

→ 위는 **필수**. 삭제하면 재현·제출에 차질.

### 3-2. 문서에 없지만 역할이 다른 노트북

| 파일 | 역할 | 권장 |
|------|------|------|
| `09_hanam_gyosan_safety_facility_site_selection.ipynb` | 07 결과를 쓰는 **탐욕적 커버리지 입지 선정**(k=10/20/30). 07과 **다른 단계**. | **유지** (입지 선정 결과가 필요하면). |

### 3-3. scripts/*.py

| 스크립트 | 문서 참조 | 권장 |
|----------|-----------|------|
| `run_spatial_models.py` | MODEL_RUN_GUIDE | **유지** |
| `run_grf_ranking.py` | MODEL_RUN_GUIDE | **유지** |
| `run_top35_upgrade_pack.py` | PPT_15min_top35_guide | **유지** |
| `make_top35_ppt_figures.py` | TOP35 발표용 그림 | **유지** |
| `run_grf_sem_pipeline_no_save.py` | 없음 | 실험/배치용. 사용 안 하면 **삭제 가능**. |
| `model_return_tables.py` | 없음 | GWR/SLM/GRF 등 테이블. 다른 스크립트·노트에서 부르는지 확인 후, 미사용이면 **삭제 가능**. |

---

## 4. 요약 표

| 구분 | 항목 | 조치 |
|------|------|------|
| **삭제 권장** | `team_share_package/` 전체 | 폴더 통째로 삭제 |
| **삭제 권장** | `notebooks/06_shap_100x100.ipynb` | 06_grf_shap과 중복 → 하나만 남기기 |
| **선택 삭제** | `notebooks/06_grf_shap_100x100.ipynb` | mg.gpkg 실험 안 하면 삭제 가능 |
| **선택 삭제** | `notebooks/10_GWRF_vs_Greedy_Algorithm_Comparison.ipynb` | 방법 비교 안 하면 삭제 가능 |
| **삭제 가능** | `__pycache__/` | 캐시만 제거 (용량·정리) |
| **정리 권장** | `data/grf_06_outputs/` | 최신 1~2 run만 남기고 나머지 삭제 또는 archive |
| **유지** | 파이프라인 노트북(00~08, 인구·노인·인사이트·시각화) | 삭제 비권장 |
| **유지** | 09_hanam_gyosan_safety_facility_site_selection | 입지 선정용으로 유지 권장 |
| **유지** | run_spatial_models, run_grf_ranking, run_top35, make_top35_ppt_figures | 문서에서 사용 → 유지 |

---

## 5. 용량이 큰 이유 정리

- **노트북/스크립트 개수** 자체보다는, **데이터 파일**이 크게 작용함.
- 특히:
  1. **team_share_package** (노트북+데이터 복사본),
  2. **grf_06_outputs** (run 여러 번 쌓인 CSV),
  3. **원본 데이터** (격자·교통·API 등)  
  중 1·2를 정리하면 전체 크기를 많이 줄일 수 있음.

원하면 “team_share_package만 삭제”“grf_06_outputs만 최신 1 run 남기기”처럼 단계별로 정리하는 스크립트나 체크리스트도 만들어 줄 수 있음.
