# PostGIS 연동 가이드

**목적**: 노인 격자 등 공간 데이터를 **PostgreSQL + PostGIS**에 적재하고, QGIS·Python에서 연결해 지도 시각화하는 방법을 정리한다.

---

## 1. 사전 요구사항

- **PostgreSQL** 설치
- **PostGIS** 확장 설치 (`CREATE EXTENSION postgis;`)
- Python: `geoalchemy2`, `sqlalchemy`, `geopandas`, `psycopg2`(또는 `psycopg2-binary`)

```bash
pip install geoalchemy2 sqlalchemy geopandas psycopg2-binary
```

---

## 2. Python에서 PostGIS로 데이터 넣기

노트북에서 만든 `map_df`(GeoDataFrame)를 그대로 DB에 넣을 수 있다.

### 2-1. 연결 문자열

```
postgresql://사용자:비밀번호@호스트:5432/DB이름
```

예: `postgresql://postgres:mypass@localhost:5432/gisdb`

### 2-2. GeoPandas로 테이블 적재

- 좌표계를 **EPSG:4326 (WGS84)** 로 맞춘 뒤 적재한다.
- 테이블명은 영문 권장(예: `elderly_grid`).

```python
from sqlalchemy import create_engine
import geopandas as gpd

# 연결 문자열만 본인 환경에 맞게 수정
conn_str = "postgresql://postgres:비밀번호@localhost:5432/DB이름"
engine = create_engine(conn_str)

# WGS84로 변환 후 적재
map_df_wgs = map_df.to_crs(4326)
map_df_wgs.to_postgis("elderly_grid", engine, if_exists="replace", index=False)
```

- `if_exists="replace"`: 기존 테이블이 있으면 삭제 후 다시 생성  
- `if_exists="append"`: 기존 테이블에 행만 추가

### 2-3. 나중에 Python에서 다시 읽기

```python
import geopandas as gpd
from sqlalchemy import create_engine

engine = create_engine(conn_str)
gdf = gpd.read_postgis("SELECT * FROM elderly_grid", engine, geom_col="geometry")
# 이후 Folium 등으로 시각화
```

---

## 3. QGIS에서 PostGIS 레이어 추가

1. QGIS 메뉴: **레이어 → 레이어 추가 → PostGIS 레이어 추가**
2. **연결**에서 새 연결 생성:
   - 이름: 임의
   - 호스트: `localhost` (또는 서버 주소)
   - 포트: `5432`
   - 데이터베이스: DB이름
   - 사용자/비밀번호 입력
3. **연결** 후 목록에서 테이블 `elderly_grid` 선택 → **추가**
4. 맵 캔버스에 레이어가 올라오면, 속성에서 스타일(색상 구간 등) 설정 후 인쇄 레이아웃으로 지도 구성

---

## 4. GeoJSON만 쓸 때 (PostGIS 미사용)

PostGIS 서버 없이 **GeoJSON 파일**만으로도 QGIS에서 동일하게 시각화 가능하다.

- 노트북에서 `map_df.to_crs(4326).to_file("경로/노인_격자.geojson", driver="GeoJSON")` 로 저장
- QGIS: **레이어 → 레이어 추가 → 벡터 레이어 추가** 에서 해당 GeoJSON 선택

제출용은 [qgis_submission_guide.md](qgis_submission_guide.md) 절차대로 `.qgz` + 레이어 파일 패키징하면 된다.

---

## 5. 관련 문서

- [qgis_submission_guide.md](qgis_submission_guide.md) — 공모전 QGIS 제출 절차
- [README.md](README.md) — 산출물 경로
