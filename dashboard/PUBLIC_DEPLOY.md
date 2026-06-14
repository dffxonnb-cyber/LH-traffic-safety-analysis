# 공개 배포 가이드

이 대시보드는 공개 배포가 가능합니다. 다만 아래 조건을 만족해야 합니다.

> 현재 저장소에서 검증 가능한 공개 Dashboard URL은 없습니다. 코드와 배포 가이드는 공개되어 있지만 실제 배포 주소는 `needs confirmation`이며, 공개 포트폴리오에는 확인되지 않은 URL을 연결하지 않습니다.

## 기본 안전 원칙

- 개인 PC 절대경로를 사용하지 않습니다.
- 승인된 데이터만 `data/`에 포함하거나 `LH_DATA_ROOT`로 외부 경로를 연결합니다.
- `OPENAI_API_KEY`는 저장소에 넣지 않고 배포 환경의 시크릿으로만 설정합니다.

## 권장 배포 방식

1. `dashboard/` 폴더와 필요한 `data/` 하위 승인 파일만 별도 공개 저장소로 분리합니다.
2. `pip install -r dashboard/requirements.txt` 로 의존성을 설치합니다.
3. `streamlit run dashboard/app.py` 또는 Streamlit Community Cloud로 배포합니다.

## 배포 전 점검 목록

- `data/` 안에 공개 가능한 파일만 넣었는지 확인
- 재배포 권한이 불명확한 GeoJSON/CSV는 제외
- 환경변수 `LH_DATA_ROOT` 또는 저장소 내부 `data/` 경로가 올바른지 확인
- `OPENAI_API_KEY`가 필요하면 Streamlit secrets 또는 배포 환경 변수로만 설정

## 참고

- 공개 저장소 기준으로 필수 데이터가 없으면 앱은 `public-safe fallback` 화면으로 전환됩니다.
- 승인 데이터를 연결하면 같은 앱에서 실제 지도 탐색 화면이 활성화됩니다.
- 공개 저장소에는 노트북 출력, 로컬 경로 로그, 임시 스크린샷을 포함하지 않는 구성을 권장합니다.
