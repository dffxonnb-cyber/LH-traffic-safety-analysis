## LH 대시보드 (Streamlit)

`1최종_LH` 프로젝트 산출물을 **지도 기반으로 탐색**하고, 선택한 격자에 대해 **근거(지표/중요 변수)** 를 요약해주는 대시보드입니다.

### 실행

```bash
cd 1최종_LH/dashboard
pip install -r requirements.txt
streamlit run app.py
```

### 데이터 경로

기본값은 레포 내부 산출물 경로를 그대로 사용합니다.

- 위험 점수(미성년자): `../data/통합_데이터/QGIS_제출용/미성년자_격자_위험점수.geojson`
- 우선순위(노인): `../data/통합_데이터/QGIS_제출용/노인_격자_우선순위.geojson`
- GRF/SHAP: `../data/grf_06_outputs/*.csv`

데이터를 GitHub에 올리지 않고(권장) 로컬에서만 보관하는 경우에도, 위 상대 경로에만 존재하면 대시보드는 그대로 동작합니다.

### LLM/멀티모달(LMM) 요약(선택)

환경변수 `OPENAI_API_KEY`가 설정되어 있으면, 선택한 격자/지표를 근거 기반으로 요약하는 “분석 어시스턴트” 탭이 활성화됩니다.
*** End Patch
