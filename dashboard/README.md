## LH 대시보드 (Streamlit)

이 대시보드는 승인된 데이터만 연결해 **지도 기반으로 탐색**하고, 선택한 격자에 대해 **근거(지표/중요 변수)** 를 요약해주는 분석 화면입니다.

### 실행

```bash
cd dashboard
pip install -r requirements.txt
streamlit run app.py
```

### 데이터 경로

공개 배포 기준 데이터 탐색 우선순위는 아래와 같습니다.

1. 환경변수 `LH_DATA_ROOT`
2. 저장소 내부 `../data`
3. 현재 작업 폴더의 `./data`

- 위험 점수(미성년자): `../data/통합_데이터/QGIS_제출용/미성년자_격자_위험점수.geojson`
- 우선순위(노인): `../data/통합_데이터/QGIS_제출용/노인_격자_우선순위.geojson`
- GRF/SHAP: `../data/grf_06_outputs/*.csv`

공개 저장소에는 승인된 데이터만 포함하세요. 원본 경쟁 데이터나 재배포 권한이 불분명한 파일은 저장소 밖에 두고 `LH_DATA_ROOT`로 연결하는 방식을 권장합니다.

### LLM/멀티모달(LMM) 요약(선택)

환경변수 `OPENAI_API_KEY`가 설정되어 있으면, 선택한 격자/지표를 근거 기반으로 요약하는 “분석 어시스턴트” 탭이 활성화됩니다.
*** End Patch
