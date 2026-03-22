from __future__ import annotations

import base64
import json
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import pydeck as pdk
import streamlit as st
from pyproj import CRS, Transformer


APP_TITLE = "LH 안전 인프라 대시보드"
GRID_CRS = "EPSG:5179"


@dataclass(frozen=True)
class GeoDataset:
    label: str
    path: Path
    value_col: str
    id_col: str = "gid"
    group_col: str = "gbn"
    year_col: str = "std_yr"
    crs_hint: Optional[str] = None  # e.g., "EPSG:5179"


ROOT = Path(__file__).resolve().parent
DATA_ROOT = (ROOT / ".." / "data").resolve()

DS_4CITY_CHILD = GeoDataset(
    label="4개 시·구 (미성년자) 위험점수",
    path=(DATA_ROOT / "통합_데이터" / "QGIS_제출용" / "미성년자_격자_위험점수.geojson").resolve(),
    value_col="위험점수",
)
DS_4CITY_ELDER = GeoDataset(
    label="4개 시·구 (노인) 우선순위점수",
    path=(DATA_ROOT / "통합_데이터" / "QGIS_제출용" / "노인_격자_우선순위.geojson").resolve(),
    value_col="우선순위점수",
)

GYOSAN_GRID = GeoDataset(
    label="하남교산 격자(베이스)",
    path=(DATA_ROOT / "격자_데이터" / "02._격자_(하남교산).geojson").resolve(),
    value_col="__dummy__",
)
GYOSAN_SELECTED_K20 = GeoDataset(
    label="하남교산 설치 후보지(k=20)",
    path=(DATA_ROOT / "통합_데이터" / "hanam_gyosan_safety_site_selected_k20.geojson").resolve(),
    value_col="우선순위_점수",
    year_col="",
    crs_hint="EPSG:5179",
)
GYOSAN_COMBINED_SELECTED = GeoDataset(
    label="하남교산 시설별 선정 결과(오버레이)",
    path=(DATA_ROOT / "통합_데이터" / "hanam_gyosan_combined_selected.geojson").resolve(),
    value_col="우선순위_점수",
    year_col="",
    crs_hint="EPSG:5179",
)

GRF_OUTPUT_DIR = (DATA_ROOT / "grf_06_outputs").resolve()


def _safe_float(x: Any) -> Optional[float]:
    try:
        if x is None:
            return None
        if isinstance(x, (int, float, np.number)):
            return float(x)
        x = str(x).strip()
        if x == "":
            return None
        return float(x)
    except Exception:
        return None


def _poly_centroid(coords: List[List[float]]) -> Tuple[float, float]:
    # coords: [[lon, lat], ...] (closed ring ok)
    arr = np.asarray(coords, dtype=float)
    if arr.ndim != 2 or arr.shape[0] < 3:
        return float(arr[:, 0].mean()), float(arr[:, 1].mean())
    if np.allclose(arr[0], arr[-1]):
        arr = arr[:-1]
    return float(arr[:, 0].mean()), float(arr[:, 1].mean())


@st.cache_data(show_spinner=False)
def load_geojson(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@st.cache_data(show_spinner=False)
def _transformer(src: str, dst: str = "EPSG:4326") -> Transformer:
    return Transformer.from_crs(CRS.from_user_input(src), CRS.from_user_input(dst), always_xy=True)


def _maybe_transform_ring(ring: List[List[float]], src_crs: Optional[str]) -> List[List[float]]:
    if not src_crs:
        return ring
    tr = _transformer(src_crs, "EPSG:4326")
    xs = [p[0] for p in ring]
    ys = [p[1] for p in ring]
    lon, lat = tr.transform(xs, ys)
    return [[float(lon[i]), float(lat[i])] for i in range(len(ring))]


def _lonlat_to_xy(lon: float, lat: float, dst_crs: str = GRID_CRS) -> Tuple[float, float]:
    tr = _transformer("EPSG:4326", dst_crs)
    x, y = tr.transform(lon, lat)
    return float(x), float(y)


def _xy_to_lonlat(x: float, y: float, src_crs: str = GRID_CRS) -> Tuple[float, float]:
    tr = _transformer(src_crs, "EPSG:4326")
    lon, lat = tr.transform(x, y)
    return float(lon), float(lat)


def make_square_grid_polygon_from_lonlat(
    lon: float,
    lat: float,
    *,
    grid_size_m: float = 100.0,
    anchor: str = "cell_center",
) -> List[List[float]]:
    """
    Create a square grid polygon (lon/lat) around a point.

    - grid_size_m: cell size in meters (e.g., 100)
    - anchor:
        - "cell_center": point becomes the cell center
        - "cell_corner": point becomes lower-left corner
    """
    x, y = _lonlat_to_xy(lon, lat, GRID_CRS)
    half = grid_size_m / 2.0
    if anchor == "cell_corner":
        x0, y0 = x, y
        x1, y1 = x + grid_size_m, y + grid_size_m
    else:
        x0, y0 = x - half, y - half
        x1, y1 = x + half, y + half

    ring_xy = [
        [x0, y0],
        [x0, y1],
        [x1, y1],
        [x1, y0],
        [x0, y0],
    ]
    ring_ll = [_xy_to_lonlat(px, py, GRID_CRS) for px, py in ring_xy]
    return [[lon2, lat2] for (lon2, lat2) in ring_ll]


def ring_to_featurecollection(
    ring_ll: List[List[float]],
    *,
    properties: Optional[Dict[str, Any]] = None,
    name: str = "generated_grid",
) -> Dict[str, Any]:
    return {
        "type": "FeatureCollection",
        "name": name,
        "crs": {"type": "name", "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"}},
        "features": [
            {
                "type": "Feature",
                "properties": properties or {},
                "geometry": {"type": "Polygon", "coordinates": [ring_ll]},
            }
        ],
    }


def geojson_to_rows(gj: Dict[str, Any], dataset: GeoDataset) -> pd.DataFrame:
    features = gj.get("features", [])
    rows: List[Dict[str, Any]] = []
    for feat in features:
        props = feat.get("properties", {}) or {}
        geom = feat.get("geometry", {}) or {}
        if geom.get("type") != "Polygon":
            continue
        coords = geom.get("coordinates")
        if not coords or not isinstance(coords, list) or not coords[0]:
            continue
        ring = coords[0]
        ring_ll = _maybe_transform_ring(ring, dataset.crs_hint)
        lon, lat = _poly_centroid(ring_ll)

        row: Dict[str, Any] = {
            dataset.id_col: props.get(dataset.id_col),
            dataset.group_col: props.get(dataset.group_col),
            "_lon": lon,
            "_lat": lat,
            "_polygon": ring_ll,
            "_properties": props,
        }
        if dataset.year_col:
            row[dataset.year_col] = props.get(dataset.year_col)
        if dataset.value_col and dataset.value_col != "__dummy__":
            row[dataset.value_col] = _safe_float(props.get(dataset.value_col))
        rows.append(row)
    return pd.DataFrame(rows)


def value_to_color(value: Optional[float], vmin: float, vmax: float) -> List[int]:
    # purple -> pink -> orange (dark theme friendly)
    if value is None or not np.isfinite(value):
        return [180, 180, 180, 35]
    if vmax <= vmin:
        t = 0.0
    else:
        t = float((value - vmin) / (vmax - vmin))
        t = max(0.0, min(1.0, t))
    r = int(124 + 120 * t)  # 124..244
    g = int(58 + 60 * (1.0 - abs(t - 0.45)))  # bump mid
    b = int(237 - 180 * t)  # 237..57
    a = 160
    return [r, g, b, a]


def build_deck_layers_points(
    df: pd.DataFrame,
    dataset: GeoDataset,
    value_col: str,
    *,
    point_radius: int,
    color_alpha: int = 170,
) -> List[pdk.Layer]:
    vals = df[value_col].dropna() if value_col in df.columns else pd.Series([], dtype=float)
    vmin = float(vals.min()) if len(vals) else 0.0
    vmax = float(vals.max()) if len(vals) else 1.0

    ldf = df.copy()
    ldf["color"] = [
        (value_to_color(v, vmin, vmax)[:3] + [color_alpha])
        if (v is not None and np.isfinite(v))
        else [180, 180, 180, 40]
        for v in ldf.get(value_col, pd.Series([None] * len(ldf))).tolist()
    ]
    return [
        pdk.Layer(
            "ScatterplotLayer",
            ldf,
            id="grid-points",
            get_position=["_lon", "_lat"],
            get_fill_color="color",
            get_radius=point_radius,
            radius_units="meters",
            pickable=True,
            auto_highlight=True,
        )
    ]


def build_deck_layers_polygons(df: pd.DataFrame, dataset: GeoDataset, value_col: str) -> List[pdk.Layer]:
    vals = df[value_col].dropna() if value_col in df.columns else pd.Series([], dtype=float)
    vmin = float(vals.min()) if len(vals) else 0.0
    vmax = float(vals.max()) if len(vals) else 1.0
    ldf = df.copy()
    ldf["fill_color"] = [value_to_color(v, vmin, vmax) for v in ldf.get(value_col, pd.Series([None] * len(ldf))).tolist()]
    return [
        pdk.Layer(
            "PolygonLayer",
            ldf,
            id="grid-polygons",
            get_polygon="_polygon",
            get_fill_color="fill_color",
            get_line_color=[20, 20, 20, 25],
            line_width_min_pixels=1,
            pickable=True,
            auto_highlight=True,
        )
    ]


def build_deck(
    layers: List[pdk.Layer],
    *,
    basemap: str,
    view: pdk.ViewState,
    tooltip_html: str,
) -> pdk.Deck:
    tooltip = {
        "html": tooltip_html,
        "style": {"backgroundColor": "rgba(10,12,18,0.92)", "color": "white"},
    }
    return pdk.Deck(layers=layers, initial_view_state=view, map_style=basemap, tooltip=tooltip)


def pick_latest_run_files(grf_dir: Path) -> Dict[str, Path]:
    if not grf_dir.exists():
        return {}
    files = list(grf_dir.glob("*.csv"))
    # expects *_YYYYMMDD_HHMMSS.csv
    def extract_ts(p: Path) -> Optional[datetime]:
        stem = p.stem
        if "_" not in stem:
            return None
        ts = stem.split("_")[-2] + "_" + stem.split("_")[-1] if stem.split("_")[-1].isdigit() else stem.split("_")[-1]
        # safer: last two parts
        parts = stem.split("_")
        if len(parts) < 3:
            return None
        cand = parts[-2] + "_" + parts[-1]
        try:
            return datetime.strptime(cand, "%Y%m%d_%H%M%S")
        except Exception:
            return None

    scored: List[Tuple[datetime, Path]] = []
    for f in files:
        ts = extract_ts(f)
        if ts:
            scored.append((ts, f))
    if not scored:
        return {}
    latest_ts = max(ts for ts, _ in scored)
    latest = [p for ts, p in scored if ts == latest_ts]
    out: Dict[str, Path] = {}
    for p in latest:
        out[p.name.split("_")[0]] = p
    return out


def try_load_csv(path: Path) -> Optional[pd.DataFrame]:
    try:
        return pd.read_csv(path)
    except Exception:
        return None


def llm_available() -> bool:
    if not os.getenv("OPENAI_API_KEY"):
        return False
    try:
        import openai  # noqa: F401

        return True
    except Exception:
        return False


def llm_summarize(prompt: str, model: str) -> str:
    try:
        from openai import OpenAI

        client = OpenAI()
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a careful data analyst. Use only provided evidence. If unsure, say so.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
        )
        return resp.choices[0].message.content or ""
    except Exception as e:
        raise RuntimeError(
            "LLM 요약을 사용하려면 `pip install openai`가 필요합니다(또는 OPENAI_API_KEY 설정 확인)."
        ) from e


def llm_analyze_image(image_bytes: bytes, prompt: str, model: str) -> str:
    """
    Optional LMM helper.

    Requires `openai` package and OPENAI_API_KEY.
    """
    try:
        from openai import OpenAI

        client = OpenAI()
        b64 = base64.b64encode(image_bytes).decode("ascii")
        data_url = f"data:image/png;base64,{b64}"
        resp = client.responses.create(
            model=model,
            input=[
                {
                    "role": "system",
                    "content": "You are a careful data analyst. Use only provided evidence. If unsure, say so.",
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": prompt},
                        {"type": "input_image", "image_url": data_url},
                    ],
                },
            ],
            temperature=0.2,
        )
        return resp.output_text
    except Exception as e:
        raise RuntimeError(
            "이미지 기반 요약(LMM)을 사용하려면 `pip install openai`가 필요하고, 모델이 이미지 입력을 지원해야 합니다."
        ) from e


def main() -> None:
    st.set_page_config(page_title=APP_TITLE, layout="wide")
    st.markdown(
        """
        <style>
        .block-container { padding-top: 1.2rem; padding-bottom: 2.5rem; }
        div[data-testid="stMetric"] { background: rgba(255,255,255,0.03); padding: 0.9rem; border-radius: 14px; border: 1px solid rgba(255,255,255,0.06); }
        .section-card { background: rgba(255,255,255,0.03); padding: 1.0rem 1.1rem; border-radius: 16px; border: 1px solid rgba(255,255,255,0.06); }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.title(APP_TITLE)
    st.caption("지역별 위험/우선순위를 지도에서 탐색하고, 하남교산 적용 결과(후보지/시설 오버레이)를 한 화면에서 확인합니다.")

    with st.sidebar:
        st.header("내비게이션")
        mode = st.radio(
            "보기",
            ["4개 시·구 (관측 위험/우선순위)", "하남교산 (적용/설치 오버레이)", "도구: 격자 위치 생성기"],
            index=0,
        )

        basemap = st.selectbox(
            "지도 스타일",
            ["mapbox://styles/mapbox/dark-v11", "mapbox://styles/mapbox/light-v11", "mapbox://styles/mapbox/streets-v12"],
            index=0,
        )

        st.divider()
        st.subheader("GRF/SHAP 결과(옵션)")
        grf_dir = st.text_input("grf_06_outputs 경로", value=str(GRF_OUTPUT_DIR))
        latest_files = pick_latest_run_files(Path(grf_dir))
        if latest_files:
            st.success("최신 run 감지")
        else:
            st.caption("없어도 대시보드는 동작합니다.")

        st.divider()
        st.subheader("LLM/LMM (선택)")
        model = st.text_input("모델명", value=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"))
        if os.getenv("OPENAI_API_KEY") and not llm_available():
            st.warning("OPENAI_API_KEY는 있으나 `openai` 패키지가 없어 비활성화.")
            st.caption("필요 시: `pip install openai`")
        elif llm_available():
            st.success("요약 기능 사용 가능")
        else:
            st.caption("키가 없으면 요약 탭은 참고용으로만 동작합니다.")

    if mode.startswith("도구"):
        st.subheader("격자 위치 생성기 (100m 기본)")
        st.caption("좌표(경도/위도)를 입력하면 해당 위치를 기준으로 100m 격자 폴리곤을 생성하고, GeoJSON으로 다운로드할 수 있습니다.")

        c1, c2, c3, c4 = st.columns([1.0, 1.0, 1.0, 1.1])
        with c1:
            lon = st.number_input("경도(lon)", value=127.1832, format="%.6f")
        with c2:
            lat = st.number_input("위도(lat)", value=37.4975, format="%.6f")
        with c3:
            grid_size = st.selectbox("격자 크기(m)", options=[50, 100, 200, 500], index=1)
        with c4:
            anchor = st.selectbox("기준점", options=["cell_center", "cell_corner"], index=0)

        ring = make_square_grid_polygon_from_lonlat(float(lon), float(lat), grid_size_m=float(grid_size), anchor=anchor)
        fc = ring_to_featurecollection(
            ring,
            properties={"grid_size_m": grid_size, "anchor": anchor, "input_lon": float(lon), "input_lat": float(lat)},
            name="generated_grid",
        )

        df = pd.DataFrame([{"_lon": float(lon), "_lat": float(lat), "label": "입력 위치"}])
        poly_df = pd.DataFrame([{"_polygon": ring, "value": 1.0}])
        view = pdk.ViewState(latitude=float(lat), longitude=float(lon), zoom=15.0, pitch=0)
        layers = []
        layers += build_deck_layers_polygons(poly_df, GeoDataset(label="gen", path=Path("."), value_col="value"), "value")
        layers.append(
            pdk.Layer(
                "ScatterplotLayer",
                df,
                id="input-point",
                get_position=["_lon", "_lat"],
                get_fill_color=[245, 158, 11, 220],
                get_radius=60,
                radius_units="meters",
                pickable=True,
            )
        )
        deck = build_deck(
            layers,
            basemap="mapbox://styles/mapbox/dark-v11",
            view=view,
            tooltip_html="<b>{label}</b>",
        )
        st.pydeck_chart(deck, use_container_width=True, height=560)

        st.download_button(
            "GeoJSON 다운로드",
            data=json.dumps(fc, ensure_ascii=False).encode("utf-8"),
            file_name=f"grid_{grid_size}m_lon{lon:.6f}_lat{lat:.6f}.geojson",
            mime="application/geo+json",
            type="primary",
        )
        st.code(json.dumps(fc, ensure_ascii=False, indent=2)[:2000] + "\n...\n", language="json")

    elif mode.startswith("4개"):
        ds = st.selectbox("지표", [DS_4CITY_CHILD.label, DS_4CITY_ELDER.label], index=0)
        dataset = DS_4CITY_CHILD if ds == DS_4CITY_CHILD.label else DS_4CITY_ELDER

        if not dataset.path.exists():
            st.error(f"데이터 파일을 찾을 수 없습니다: `{dataset.path}`")
            st.stop()

        df = geojson_to_rows(load_geojson(str(dataset.path)), dataset)
        if df.empty:
            st.error("GeoJSON에서 Polygon feature를 읽지 못했습니다.")
            st.stop()

        groups = sorted([g for g in df[dataset.group_col].dropna().unique().tolist() if str(g).strip() != ""])
        c1, c2, c3, c4 = st.columns([1.2, 0.9, 0.9, 1.0])
        with c1:
            group_sel = st.multiselect("지역", options=groups, default=groups[:1] if groups else [])
        with c2:
            year_vals = sorted(df[dataset.year_col].dropna().unique().tolist()) if dataset.year_col in df.columns else []
            year_sel = st.selectbox("연도", options=year_vals, index=0) if year_vals else None
        with c3:
            render_mode = st.selectbox("렌더링", ["점(빠름)", "폴리곤(느림, Top만)"], index=0)
        with c4:
            top_pct = st.slider("상위 %만 표시", min_value=1, max_value=50, value=5, step=1)

        fdf = df.copy()
        if group_sel:
            fdf = fdf[fdf[dataset.group_col].isin(group_sel)]
        if year_sel is not None and dataset.year_col in fdf.columns:
            fdf = fdf[fdf[dataset.year_col] == year_sel]

        if fdf.empty:
            st.warning("필터 결과가 비어있습니다.")
            st.stop()

        val = dataset.value_col
        thr = np.nanpercentile(fdf[val].astype(float).values, 100 - top_pct) if val in fdf.columns else None
        sdf = fdf[fdf[val] >= thr] if thr is not None else fdf

        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.metric("격자 수(필터 후)", f"{len(fdf):,}")
        with m2:
            st.metric(f"상위 {top_pct}% 격자", f"{len(sdf):,}")
        with m3:
            st.metric("최대값", f"{float(sdf[val].max()):.3f}" if len(sdf) and val in sdf.columns else "-")
        with m4:
            st.metric("평균(상위만)", f"{float(sdf[val].mean()):.3f}" if len(sdf) and val in sdf.columns else "-")

        center_lon = float(sdf["_lon"].mean())
        center_lat = float(sdf["_lat"].mean())
        view = pdk.ViewState(latitude=center_lat, longitude=center_lon, zoom=11.3, pitch=0)

        if render_mode.startswith("점"):
            layers = build_deck_layers_points(sdf, dataset, val, point_radius=55)
        else:
            layers = build_deck_layers_polygons(sdf, dataset, val)

        deck = build_deck(
            layers,
            basemap=basemap,
            view=view,
            tooltip_html=f"<b>{{{dataset.id_col}}}</b><br/>{dataset.group_col}: {{{dataset.group_col}}}<br/>{val}: {{{val}}}",
        )

        left, right = st.columns([1.6, 1.0])
        with left:
            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            st.subheader("지도 (상위 구간만 오버레이)")
            st.pydeck_chart(deck, use_container_width=True, height=680)
            st.markdown("</div>", unsafe_allow_html=True)
        with right:
            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            st.subheader("Top N")
            top_n = st.slider("Top N", min_value=20, max_value=500, value=100, step=20)
            show_cols = [dataset.id_col, dataset.group_col, dataset.year_col, val, "_lon", "_lat"]
            show_cols = [c for c in show_cols if c in sdf.columns]
            tdf = sdf[show_cols].sort_values(val, ascending=False).head(top_n)
            st.dataframe(tdf, use_container_width=True, height=540)
            gid = st.text_input("gid 상세보기", value=str(tdf.iloc[0][dataset.id_col]) if len(tdf) else "")
            picked = fdf[fdf[dataset.id_col] == gid]
            if len(picked) == 1:
                st.json(dict(picked.iloc[0]["_properties"]))
            st.download_button(
                "상위 격자 CSV 다운로드",
                data=tdf.to_csv(index=False).encode("utf-8-sig"),
                file_name="top_grids.csv",
                mime="text/csv",
            )
            st.markdown("</div>", unsafe_allow_html=True)

    else:
        # Gyosan view
        if not GYOSAN_GRID.path.exists():
            st.error(f"데이터 파일을 찾을 수 없습니다: `{GYOSAN_GRID.path}`")
            st.stop()
        grid_df = geojson_to_rows(load_geojson(str(GYOSAN_GRID.path)), GYOSAN_GRID)

        if not GYOSAN_SELECTED_K20.path.exists():
            st.error(f"데이터 파일을 찾을 수 없습니다: `{GYOSAN_SELECTED_K20.path}`")
            st.stop()
        k20_df = geojson_to_rows(load_geojson(str(GYOSAN_SELECTED_K20.path)), GYOSAN_SELECTED_K20)

        combined_df = None
        if GYOSAN_COMBINED_SELECTED.path.exists():
            combined_df = geojson_to_rows(load_geojson(str(GYOSAN_COMBINED_SELECTED.path)), GYOSAN_COMBINED_SELECTED)

        c1, c2, c3 = st.columns([1.1, 1.0, 0.9])
        with c1:
            facility_filter = None
            if combined_df is not None and "facility" in combined_df["_properties"].iloc[0]:
                facility_filter = st.multiselect("시설 타입 오버레이(선택)", options=sorted(set([r["_properties"].get("facility") for _, r in combined_df.iterrows()])))
        with c2:
            show_polygons = st.toggle("선정 격자(폴리곤) 표시", value=True)
        with c3:
            point_radius = st.slider("표시 크기", min_value=30, max_value=120, value=70, step=10)

        center_lon = float(k20_df["_lon"].mean())
        center_lat = float(k20_df["_lat"].mean())
        view = pdk.ViewState(latitude=center_lat, longitude=center_lon, zoom=12.2, pitch=0)

        layers: List[pdk.Layer] = []
        # Base: gyosan grid centroids (light)
        if not grid_df.empty:
            base = grid_df.copy()
            base["color"] = [[150, 150, 150, 20]] * len(base)
            layers.append(
                pdk.Layer(
                    "ScatterplotLayer",
                    base,
                    id="gyosan-base-grid",
                    get_position=["_lon", "_lat"],
                    get_fill_color="color",
                    get_radius=40,
                    radius_units="meters",
                    pickable=False,
                )
            )

        # Selected k20: points + optional polygons
        k20_points = k20_df.copy()
        k20_points["color"] = [[124, 58, 237, 200]] * len(k20_points)
        layers.append(
            pdk.Layer(
                "ScatterplotLayer",
                k20_points,
                id="gyosan-k20-points",
                get_position=["_lon", "_lat"],
                get_fill_color="color",
                get_radius=point_radius,
                radius_units="meters",
                pickable=True,
                auto_highlight=True,
            )
        )
        if show_polygons:
            layers += build_deck_layers_polygons(k20_df, GYOSAN_SELECTED_K20, GYOSAN_SELECTED_K20.value_col)

        # Facility overlay (from combined_selected): show only selected facility types if chosen
        if combined_df is not None and not combined_df.empty:
            odf = combined_df.copy()
            if facility_filter:
                odf = odf[odf["_properties"].apply(lambda p: p.get("facility") in set(facility_filter))]
            if not odf.empty:
                # color by facility
                palette = {
                    "CCTV": [239, 68, 68, 180],
                    "EmergencyBell": [245, 158, 11, 180],
                }
                odf["fill_color"] = [
                    palette.get(r["_properties"].get("facility"), [59, 130, 246, 160]) for _, r in odf.iterrows()
                ]
                layers.append(
                    pdk.Layer(
                        "PolygonLayer",
                        odf,
                        id="gyosan-facility-overlay",
                        get_polygon="_polygon",
                        get_fill_color="fill_color",
                        get_line_color=[255, 255, 255, 40],
                        line_width_min_pixels=1,
                        pickable=True,
                        auto_highlight=True,
                    )
                )

        deck = build_deck(
            layers,
            basemap=basemap,
            view=view,
            tooltip_html="<b>{gid}</b><br/>우선순위_점수: {우선순위_점수}<br/>selected_order: {selected_order}",
        )

        left, right = st.columns([1.55, 1.0])
        with left:
            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            st.subheader("하남교산: 선정 후보지(k=20) + 시설 오버레이")
            st.pydeck_chart(deck, use_container_width=True, height=680)
            st.markdown("</div>", unsafe_allow_html=True)
        with right:
            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            st.subheader("선정 리스트(k=20)")
            show_cols = ["selected_order", "gid", "우선순위_점수", "우선순위_순위", "미성년자_유동_추정", "blockType", "도로_격자_여부"]
            show_cols = [c for c in show_cols if c in k20_df["_properties"].iloc[0]]
            # flatten properties for table
            rows = []
            for _, r in k20_df.iterrows():
                p = r["_properties"]
                rows.append({k: p.get(k) for k in ["selected_order", "gid", "우선순위_점수", "우선순위_순위", "미성년자_유동_추정", "blockType", "도로_격자_여부"]})
            tdf = pd.DataFrame(rows).sort_values("selected_order")
            st.dataframe(tdf, use_container_width=True, height=420)

            st.divider()
            st.subheader("근거 요약(옵션)")
            gid = st.text_input("gid", value=str(tdf.iloc[0]["gid"]) if len(tdf) else "")
            uploaded = st.file_uploader("지도/도표 스크린샷 업로드(선택)", type=["png", "jpg", "jpeg"])
            if gid:
                picked = k20_df[k20_df["gid"] == gid] if "gid" in k20_df.columns else pd.DataFrame()
                if len(picked) == 1:
                    props = dict(picked.iloc[0]["_properties"])
                    context_lines = [
                        "- dataset: 하남교산 설치 후보지(k=20)",
                        f"- gid: {gid}",
                        "",
                        "격자 속성:",
                        json.dumps(props, ensure_ascii=False),
                    ]
                    if latest_files:
                        global_imp = try_load_csv(latest_files.get("global", Path(""))) if latest_files.get("global") else None
                        shap_imp = try_load_csv(latest_files.get("shap", Path(""))) if latest_files.get("shap") else None
                        if global_imp is not None:
                            context_lines += ["", "global_importance 상위 15행:", global_imp.head(15).to_csv(index=False)]
                        if shap_imp is not None:
                            context_lines += ["", "shap_importance 상위 15행:", shap_imp.head(15).to_csv(index=False)]
                    prompt = "\n".join(context_lines) + "\n\n요청: 위 근거만 사용해서 (1) 왜 여기가 후보로 선택됐는지 5줄, (2) 설치 시 기대 효과/주의점 3개를 써줘. 근거 없으면 근거 부족이라고 해."

                    if st.button("요약 생성", type="primary"):
                        if not llm_available():
                            st.error("OPENAI_API_KEY 또는 openai 패키지가 없어 요약이 비활성화됩니다.")
                        else:
                            with st.spinner("요약 생성 중..."):
                                try:
                                    if uploaded is not None:
                                        out = llm_analyze_image(
                                            image_bytes=uploaded.getvalue(),
                                            prompt=prompt,
                                            model=model,
                                        )
                                    else:
                                        out = llm_summarize(prompt=prompt, model=model)
                                    st.markdown(out)
                                except Exception as e:
                                    st.exception(e)
            st.markdown("</div>", unsafe_allow_html=True)


if __name__ == "__main__":
    main()

