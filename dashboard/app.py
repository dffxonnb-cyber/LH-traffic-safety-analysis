from __future__ import annotations

import base64
import html
import json
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd
import pydeck as pdk
import streamlit as st
from pyproj import CRS, Transformer


APP_TITLE = "LH 안전 인프라 대시보드"
GRID_CRS = "EPSG:5179"
MAP_STYLES = {
    "Urban Light": "mapbox://styles/mapbox/light-v11",
    "Street Context": "mapbox://styles/mapbox/streets-v12",
    "Satellite Hybrid": "mapbox://styles/mapbox/satellite-streets-v12",
    "Night Navigation": "mapbox://styles/mapbox/navigation-night-v1",
}

APP_CSS = """
<style>
:root {
    --bg: #07161d;
    --bg-deep: #09131a;
    --stroke: rgba(156, 204, 194, 0.16);
    --text: #eef5f2;
    --muted: #9fb4ae;
    --accent: #27c2a7;
    --accent-soft: #8ee5d4;
    --accent-warm: #f4b73e;
}
.stApp {
    background:
        radial-gradient(circle at 12% 12%, rgba(39, 194, 167, 0.20), transparent 30%),
        radial-gradient(circle at 86% 10%, rgba(244, 183, 62, 0.16), transparent 28%),
        linear-gradient(180deg, var(--bg) 0%, var(--bg-deep) 100%);
    color: var(--text);
}
html, body, [class*="css"] {
    font-family: "Pretendard", "Segoe UI", "Apple SD Gothic Neo", sans-serif;
}
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, rgba(9, 24, 30, 0.98) 0%, rgba(7, 19, 26, 0.98) 100%);
    border-right: 1px solid rgba(156, 204, 194, 0.12);
}
.block-container { max-width: 1450px; padding-top: 1.2rem; padding-bottom: 2.6rem; }
.app-brand, .hero-shell, .callout-card, .metric-tile {
    border: 1px solid var(--stroke);
    background: linear-gradient(145deg, rgba(16, 37, 46, 0.95), rgba(9, 20, 27, 0.95));
}
.app-brand {
    position: relative; overflow: hidden; border-radius: 26px; padding: 1.2rem 1.1rem 1rem; margin-bottom: 1rem;
}
.brand-kicker, .hero-kicker {
    display: inline-block; font-size: 0.73rem; letter-spacing: 0.08em; text-transform: uppercase; color: var(--accent-soft);
}
.brand-kicker { padding: 0.3rem 0.62rem; border-radius: 999px; background: rgba(39, 194, 167, 0.12); }
.brand-title { margin: 0.9rem 0 0.35rem; font-size: 1.18rem; font-weight: 700; }
.brand-copy, .hero-subtitle, .callout-copy, .section-desc, .metric-help, .small-note { color: var(--muted); line-height: 1.6; }
.hero-shell { border-radius: 30px; padding: 1.55rem; margin-bottom: 1rem; }
.hero-title { margin: 0; font-size: clamp(1.8rem, 2.3vw, 2.8rem); font-weight: 750; line-height: 1.14; }
.hero-pill-row, .callout-pills { display: flex; flex-wrap: wrap; gap: 0.58rem; margin-top: 1rem; }
.hero-pill, .callout-pill {
    display: inline-flex; padding: 0.48rem 0.78rem; border-radius: 999px;
    border: 1px solid rgba(156, 204, 194, 0.18); background: rgba(255, 255, 255, 0.04); font-size: 0.86rem;
}
.metric-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 0.85rem; margin: 0.95rem 0 1.25rem; }
.metric-tile { border-radius: 22px; padding: 1rem; }
.metric-label { color: var(--muted); font-size: 0.78rem; letter-spacing: 0.08em; text-transform: uppercase; }
.metric-value { margin-top: 0.42rem; font-size: 1.65rem; font-weight: 730; line-height: 1.1; }
.section-title { margin: 0; font-size: 1.08rem; font-weight: 690; }
.callout-card { border-radius: 24px; padding: 1rem 1.05rem; margin-bottom: 1rem; }
div[data-testid="stDataFrame"], div[data-testid="stDeckGlJsonChart"], div[data-testid="stCodeBlock"], div[data-testid="stExpander"] {
    border-radius: 22px; overflow: hidden; border: 1px solid var(--stroke); background: rgba(9, 22, 28, 0.84);
}
div[data-baseweb="select"] > div, div[data-baseweb="input"] > div, div[data-testid="stTextInputRootElement"] > div,
div[data-testid="stNumberInput"] > div, div[data-testid="stFileUploaderDropzone"] {
    border-radius: 18px !important; border: 1px solid rgba(156, 204, 194, 0.15) !important; background: rgba(9, 22, 28, 0.76) !important;
}
label[data-testid="stWidgetLabel"] p { color: var(--muted); font-size: 0.78rem; letter-spacing: 0.08em; text-transform: uppercase; }
button[kind="primary"] { border-radius: 16px !important; border: 0 !important; color: #081118 !important; background: linear-gradient(135deg, var(--accent), #6be0c8) !important; font-weight: 700 !important; }
button[kind="secondary"], button[kind="tertiary"] { border-radius: 16px !important; }
@media (max-width: 960px) { .metric-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
@media (max-width: 640px) { .metric-grid { grid-template-columns: 1fr; } .hero-shell { padding: 1.25rem 1.05rem 1.1rem; border-radius: 24px; } }
</style>
"""

FACILITY_PALETTE = {
    "CCTV": [255, 124, 91, 190],
    "EmergencyBell": [244, 183, 62, 190],
}


@dataclass(frozen=True)
class GeoDataset:
    label: str
    path: Path
    value_col: str
    id_col: str = "gid"
    group_col: str = "gbn"
    year_col: str = "std_yr"
    crs_hint: Optional[str] = None


ROOT = Path(__file__).resolve().parent
DOCS_ROOT = (ROOT / ".." / "docs").resolve()
DOCS_IMAGE_DIR = DOCS_ROOT / "images"


def resolve_data_root() -> Path:
    candidates: List[Path] = []
    env_data_root = os.getenv("LH_DATA_ROOT")
    if env_data_root:
        candidates.append(Path(env_data_root).expanduser().resolve())
    candidates.extend(
        [
            (ROOT / ".." / "data").resolve(),
            Path.cwd().resolve() / "data",
        ]
    )
    required = Path("통합_데이터") / "QGIS_제출용" / "미성년자_격자_위험점수.geojson"
    for candidate in candidates:
        if (candidate / required).exists():
            return candidate
    return candidates[0]


DATA_ROOT = resolve_data_root()
DS_4CITY_CHILD = GeoDataset("4개 시·구 (미성년자) 위험점수", (DATA_ROOT / "통합_데이터" / "QGIS_제출용" / "미성년자_격자_위험점수.geojson").resolve(), "위험점수")
DS_4CITY_ELDER = GeoDataset("4개 시·구 (노인) 우선순위점수", (DATA_ROOT / "통합_데이터" / "QGIS_제출용" / "노인_격자_우선순위.geojson").resolve(), "우선순위점수")
GYOSAN_GRID = GeoDataset("하남교산 격자(베이스)", (DATA_ROOT / "격자_데이터" / "02._격자_(하남교산).geojson").resolve(), "__dummy__")
GYOSAN_SELECTED_K20 = GeoDataset("하남교산 설치 후보지(k=20)", (DATA_ROOT / "통합_데이터" / "hanam_gyosan_safety_site_selected_k20.geojson").resolve(), "우선순위_점수", year_col="", crs_hint="EPSG:5179")
GYOSAN_COMBINED_SELECTED = GeoDataset("하남교산 시설별 선정 결과(오버레이)", (DATA_ROOT / "통합_데이터" / "hanam_gyosan_combined_selected.geojson").resolve(), "우선순위_점수", year_col="", crs_hint="EPSG:5179")
GRF_OUTPUT_DIR = (DATA_ROOT / "grf_06_outputs").resolve()
REGION_LABEL_MAP = {
    "경기도 성남시": "판교",
    "경기도 하남시": "하남미사",
    "경기도 화성시": "동탄",
    "서울특별시 송파구": "송파",
}
PROJECT_REGION_ORDER = ["판교", "하남미사", "동탄", "송파"]
PROJECT_REGION_META = {
    "판교": {
        "theme": "업무·주거 복합형 중심지",
        "summary": "밀도 높은 생활권과 업무권이 겹치는 구조라 교차로·횡단보도 주변의 보행 안전 해석이 중요합니다.",
        "focus": "집중형 결절 관리",
    },
    "하남미사": {
        "theme": "대규모 주거 확장형 신도시",
        "summary": "신도시 확장축과 생활 SOC 동선이 넓게 퍼져 있어 생활권 연결 구간의 안전 취약을 읽는 데 적합합니다.",
        "focus": "연결축 안전 보강",
    },
    "동탄": {
        "theme": "분산 다핵 생활권",
        "summary": "생활권이 넓게 분산된 구조라 고립된 격자보다는 다수의 중위험 격자 패턴을 함께 보는 것이 중요합니다.",
        "focus": "분산형 우선순위 관리",
    },
    "송파": {
        "theme": "보행 결절 밀집 도시형 권역",
        "summary": "지하철·상업·주거가 조밀하게 중첩되어 단위 격자 간 밀도 차이가 크고, 상위 격자의 설명력이 강합니다.",
        "focus": "고밀 결절 보호",
    },
}

PUBLIC_SAFE_VISUALS = {
    "4개 시·구 위험 격자 비교": DOCS_IMAGE_DIR / "four-city-risk-overview-ko.png",
    "하남교산 적용 전/후 시나리오": DOCS_IMAGE_DIR / "gyosan-before-after-ko.png",
}


def inject_css() -> None:
    st.markdown(APP_CSS, unsafe_allow_html=True)


def display_region_name(value: Any) -> Any:
    if value is None:
        return value
    return REGION_LABEL_MAP.get(str(value), value)


def region_sort_key(value: Any) -> Tuple[int, str]:
    name = str(value)
    if name in PROJECT_REGION_ORDER:
        return (PROJECT_REGION_ORDER.index(name), name)
    return (len(PROJECT_REGION_ORDER), name)


def render_sidebar_brand() -> None:
    st.markdown(
        """
        <section class="app-brand">
            <div class="brand-kicker">Decision Support</div>
            <h1 class="brand-title">LH 안전 인프라 대시보드</h1>
            <p class="brand-copy">위험 격자, 후보지, 시설 오버레이를 실제 지도 위에서 비교하는 분석형 의사결정 화면</p>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_hero(title: str, subtitle: str, pills: Sequence[str], kicker: str) -> None:
    pill_html = "".join(f'<span class="hero-pill">{html.escape(str(pill))}</span>' for pill in pills if pill)
    st.markdown(
        f"""
        <section class="hero-shell">
            <div class="hero-kicker">{html.escape(kicker)}</div>
            <h2 class="hero-title">{html.escape(title)}</h2>
            <p class="hero-subtitle">{html.escape(subtitle)}</p>
            <div class="hero-pill-row">{pill_html}</div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_metric_tiles(cards: Sequence[Tuple[str, str, str]]) -> None:
    tiles = "".join(
        f'<article class="metric-tile"><div class="metric-label">{html.escape(label)}</div><div class="metric-value">{html.escape(value)}</div><div class="metric-help">{html.escape(help_text)}</div></article>'
        for label, value, help_text in cards
    )
    st.markdown(f'<section class="metric-grid">{tiles}</section>', unsafe_allow_html=True)


def render_section_head(title: str, description: str) -> None:
    st.markdown(
        f'<section><h3 class="section-title">{html.escape(title)}</h3><p class="section-desc">{html.escape(description)}</p></section>',
        unsafe_allow_html=True,
    )


def render_callout(title: str, copy: str, pills: Optional[Sequence[str]] = None) -> None:
    pill_html = ""
    if pills:
        pill_html = '<div class="callout-pills">' + "".join(f'<span class="callout-pill">{html.escape(str(p))}</span>' for p in pills) + "</div>"
    st.markdown(
        f'<section class="callout-card"><h4>{html.escape(title)}</h4><p class="callout-copy">{html.escape(copy)}</p>{pill_html}</section>',
        unsafe_allow_html=True,
    )


def required_dashboard_paths() -> List[Path]:
    return [
        DS_4CITY_CHILD.path,
        DS_4CITY_ELDER.path,
        GYOSAN_GRID.path,
        GYOSAN_SELECTED_K20.path,
    ]


def missing_dashboard_paths() -> List[Path]:
    return [path for path in required_dashboard_paths() if not path.exists()]


def dashboard_data_available() -> bool:
    return not missing_dashboard_paths()


def render_public_safe_mode(mode: str, basemap: str, latest_files: Dict[str, Path]) -> None:
    render_hero(
        "공개 저장소용 미리보기 모드",
        "원본 공간 데이터 없이도 핵심 결과와 검토 포인트를 확인할 수 있도록 public-safe 화면을 제공합니다.",
        [
            display_region_name(mode),
            Path(DATA_ROOT).name,
            "public-safe fallback",
        ],
        "Public Preview",
    )
    render_callout(
        "왜 fallback 화면이 보이나요?",
        "이 저장소는 승인된 데이터만 공개하기 때문에, 공개 저장소만으로는 원본 GeoJSON/CSV 전체를 재생성할 수 없습니다. 대신 README와 문서에서 확인 가능한 핵심 시각화와 검토 포인트를 먼저 보여줍니다.",
        pills=["공개 안전 모드", "원본 데이터 비포함", "검토 우선"],
    )

    cards = [
        ("필수 데이터 상태", "미연결", f"{len(missing_dashboard_paths())}개 필수 경로 누락"),
        ("공간 RF/SHAP 결과", "선택 연결", "없어도 미리보기는 가능"),
        ("지도 스타일", next((name for name, value in MAP_STYLES.items() if value == basemap), basemap), "실데이터 연결 시 적용"),
        ("검토 경로", "README / docs", "공개 저장소 기준"),
    ]
    render_metric_tiles(cards)

    render_section_head("공개 저장소에서 바로 확인할 수 있는 것", "데이터가 없을 때도 읽히는 결과물과 검토 순서를 한 화면에 모았습니다.")
    for title, image_path in PUBLIC_SAFE_VISUALS.items():
        if image_path.exists():
            st.markdown(f"#### {title}")
            st.image(str(image_path), use_container_width=True)

    render_section_head("우선 확인할 문서", "실데이터 연결 없이도 프로젝트 가치를 설명하는 핵심 문서입니다.")
    guide_rows = pd.DataFrame(
        [
            {
                "문서": "README.md",
                "역할": "문제 정의, 검증 요약, 공개 확인 포인트",
                "경로": "./README.md",
            },
            {
                "문서": "docs/reproducibility_and_validation.md",
                "역할": "공개 저장소 기준 검증 범위와 TOP35 수치",
                "경로": "./docs/reproducibility_and_validation.md",
            },
            {
                "문서": "docs/grf_risk_methodology.md",
                "역할": "공간 좌표 포함 Random Forest 위험도와 전이 논리 설명",
                "경로": "./docs/grf_risk_methodology.md",
            },
            {
                "문서": "dashboard/PUBLIC_DEPLOY.md",
                "역할": "승인 데이터 연결과 공개 배포 가이드",
                "경로": "./dashboard/PUBLIC_DEPLOY.md",
            },
        ]
    )
    st.dataframe(guide_rows, use_container_width=True, hide_index=True)

    if latest_files:
        timestamps = [ts for ts in (extract_run_timestamp(path) for path in latest_files.values()) if ts is not None]
        if timestamps:
            render_callout(
                "참고",
                f"현재 연결된 공간 RF/SHAP 결과 기준 최신 run 시각은 {max(timestamps).strftime('%Y-%m-%d %H:%M:%S')} 입니다.",
            )

    with st.expander("누락된 필수 경로 보기"):
        for path in missing_dashboard_paths():
            st.code(str(path))

    st.info("실제 지도 탐색을 열려면 승인된 데이터를 `LH_DATA_ROOT` 또는 저장소 내부 `data/`로 연결하세요.")


def render_region_profile_cards(region_names: Sequence[str]) -> None:
    cards: List[Tuple[str, str, str]] = []
    for region in region_names:
        meta = PROJECT_REGION_META.get(str(region))
        if not meta:
            continue
        cards.append((str(region), str(meta["focus"]), f"{meta['theme']} | {meta['summary']}"))
    if cards:
        render_metric_tiles(cards)


def format_count(value: int) -> str:
    return f"{value:,}"


def format_float(value: Optional[float], digits: int = 3) -> str:
    if value is None or not np.isfinite(value):
        return "-"
    return f"{float(value):,.{digits}f}"


def percentile_rank(series: pd.Series, value: Optional[float]) -> str:
    cleaned = pd.to_numeric(series, errors="coerce").dropna()
    if value is None or not np.isfinite(value) or cleaned.empty:
        return "-"
    pct = float((cleaned <= value).mean() * 100.0)
    return f"{pct:.1f}%"


def order_region_frame(df: pd.DataFrame, column: str = "지역") -> pd.DataFrame:
    if df.empty or column not in df.columns:
        return df
    return df.sort_values(column, key=lambda s: s.map(region_sort_key)).reset_index(drop=True)


def extract_run_timestamp(path: Path) -> Optional[datetime]:
    parts = path.stem.split("_")
    if len(parts) < 3:
        return None
    try:
        return datetime.strptime(f"{parts[-2]}_{parts[-1]}", "%Y%m%d_%H%M%S")
    except ValueError:
        return None


def _safe_float(x: Any) -> Optional[float]:
    try:
        if x is None:
            return None
        return float(str(x).strip()) if not isinstance(x, (int, float, np.number)) else float(x)
    except Exception:
        return None


def _poly_centroid(coords: List[List[float]]) -> Tuple[float, float]:
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
    return tuple(map(float, _transformer("EPSG:4326", dst_crs).transform(lon, lat)))


def _xy_to_lonlat(x: float, y: float, src_crs: str = GRID_CRS) -> Tuple[float, float]:
    return tuple(map(float, _transformer(src_crs, "EPSG:4326").transform(x, y)))


def geojson_to_rows(gj: Dict[str, Any], dataset: GeoDataset) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []
    for feat in gj.get("features", []):
        props = feat.get("properties", {}) or {}
        geom = feat.get("geometry", {}) or {}
        coords = geom.get("coordinates")
        if geom.get("type") != "Polygon" or not coords or not coords[0]:
            continue
        ring_ll = _maybe_transform_ring(coords[0], dataset.crs_hint)
        lon, lat = _poly_centroid(ring_ll)
        row: Dict[str, Any] = {dataset.id_col: props.get(dataset.id_col), dataset.group_col: display_region_name(props.get(dataset.group_col)), "_lon": lon, "_lat": lat, "_polygon": ring_ll, "_properties": props}
        if dataset.year_col:
            row[dataset.year_col] = props.get(dataset.year_col)
        if dataset.value_col != "__dummy__":
            row[dataset.value_col] = _safe_float(props.get(dataset.value_col))
        rows.append(row)
    return pd.DataFrame(rows)


def _interpolate_rgb(start: Sequence[int], end: Sequence[int], t: float) -> List[int]:
    return [int(round(start[i] + (end[i] - start[i]) * t)) for i in range(3)]


def value_to_color(value: Optional[float], vmin: float, vmax: float) -> List[int]:
    if value is None or not np.isfinite(value):
        return [145, 154, 160, 22]
    t = 0.0 if vmax <= vmin else max(0.0, min(1.0, float((value - vmin) / (vmax - vmin))))
    rgb = _interpolate_rgb([118, 160, 184], [70, 177, 150], t / 0.6) if t < 0.6 else _interpolate_rgb([70, 177, 150], [239, 184, 76], (t - 0.6) / 0.4)
    return rgb + [104]


def build_deck_layers_points(df: pd.DataFrame, value_col: str, *, point_radius: int, color_alpha: int = 172) -> List[pdk.Layer]:
    vals = df[value_col].dropna() if value_col in df.columns else pd.Series([], dtype=float)
    vmin = float(vals.min()) if len(vals) else 0.0
    vmax = float(vals.max()) if len(vals) else 1.0
    ldf = df.copy()
    ldf["color"] = [(value_to_color(v, vmin, vmax)[:3] + [color_alpha]) if (v is not None and np.isfinite(v)) else [130, 144, 148, 36] for v in ldf.get(value_col, pd.Series([None] * len(ldf))).tolist()]
    return [pdk.Layer("ScatterplotLayer", ldf, id="grid-points", get_position=["_lon", "_lat"], get_fill_color="color", get_radius=point_radius, radius_units="meters", pickable=True, auto_highlight=True)]


def build_deck_layers_polygons(df: pd.DataFrame, value_col: str) -> List[pdk.Layer]:
    vals = df[value_col].dropna() if value_col in df.columns else pd.Series([], dtype=float)
    vmin = float(vals.min()) if len(vals) else 0.0
    vmax = float(vals.max()) if len(vals) else 1.0
    ldf = df.copy()
    ldf["fill_color"] = [value_to_color(v, vmin, vmax) for v in ldf.get(value_col, pd.Series([None] * len(ldf))).tolist()]
    return [pdk.Layer("PolygonLayer", ldf, id="grid-polygons", get_polygon="_polygon", get_fill_color="fill_color", get_line_color=[86, 98, 110, 44], line_width_min_pixels=1, opacity=0.72, pickable=True, auto_highlight=True)]


def build_constant_polygon_layer(
    df: pd.DataFrame,
    *,
    layer_id: str,
    fill_color: Sequence[int],
    line_color: Sequence[int],
    line_width_min_pixels: int = 1,
    pickable: bool = False,
) -> pdk.Layer:
    ldf = df.copy()
    ldf["fill_color"] = [list(fill_color)] * len(ldf)
    ldf["line_color"] = [list(line_color)] * len(ldf)
    return pdk.Layer(
        "PolygonLayer",
        ldf,
        id=layer_id,
        get_polygon="_polygon",
        get_fill_color="fill_color",
        get_line_color="line_color",
        line_width_min_pixels=line_width_min_pixels,
        pickable=pickable,
        auto_highlight=pickable,
    )


def build_extruded_polygon_layer(
    df: pd.DataFrame,
    value_col: str,
    *,
    layer_id: str,
    elevation_scale: float = 1.0,
    line_color: Sequence[int] = (220, 240, 236, 40),
    line_width_min_pixels: int = 1,
    opacity_boost: int = 205,
) -> pdk.Layer:
    vals = df[value_col].dropna() if value_col in df.columns else pd.Series([], dtype=float)
    vmin = float(vals.min()) if len(vals) else 0.0
    vmax = float(vals.max()) if len(vals) else 1.0
    ldf = df.copy()
    fill_colors: List[List[int]] = []
    elevations: List[float] = []
    for value in ldf.get(value_col, pd.Series([None] * len(ldf))).tolist():
        color = value_to_color(value, vmin, vmax)
        color[3] = opacity_boost
        fill_colors.append(color)
        if value is None or not np.isfinite(value):
            elevations.append(1.0)
        elif vmax <= vmin:
            elevations.append(25.0 * elevation_scale)
        else:
            norm = max(0.0, min(1.0, float((value - vmin) / (vmax - vmin))))
            elevations.append((22.0 + norm * 180.0) * elevation_scale)
    ldf["fill_color"] = fill_colors
    ldf["elevation"] = elevations
    return pdk.Layer(
        "PolygonLayer",
        ldf,
        id=layer_id,
        get_polygon="_polygon",
        get_fill_color="fill_color",
        get_line_color=list(line_color),
        get_elevation="elevation",
        extruded=True,
        wireframe=True,
        line_width_min_pixels=line_width_min_pixels,
        pickable=True,
        auto_highlight=True,
    )


def build_deck(layers: List[pdk.Layer], *, basemap: str, view: pdk.ViewState, tooltip_html: str) -> pdk.Deck:
    tooltip = {"html": tooltip_html, "style": {"backgroundColor": "rgba(8, 20, 26, 0.94)", "color": "#eef5f2", "border": "1px solid rgba(142, 229, 212, 0.18)"}}
    return pdk.Deck(layers=layers, initial_view_state=view, map_style=basemap, tooltip=tooltip)


def make_square_grid_polygon_from_lonlat(lon: float, lat: float, *, grid_size_m: float = 100.0, anchor: str = "cell_center") -> List[List[float]]:
    x, y = _lonlat_to_xy(lon, lat, GRID_CRS)
    half = grid_size_m / 2.0
    x0, y0, x1, y1 = (x, y, x + grid_size_m, y + grid_size_m) if anchor == "cell_corner" else (x - half, y - half, x + half, y + half)
    ring_xy = [[x0, y0], [x0, y1], [x1, y1], [x1, y0], [x0, y0]]
    return [[lon2, lat2] for lon2, lat2 in [_xy_to_lonlat(px, py, GRID_CRS) for px, py in ring_xy]]


def ring_to_featurecollection(ring_ll: List[List[float]], *, properties: Optional[Dict[str, Any]] = None, name: str = "generated_grid") -> Dict[str, Any]:
    return {"type": "FeatureCollection", "name": name, "crs": {"type": "name", "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"}}, "features": [{"type": "Feature", "properties": properties or {}, "geometry": {"type": "Polygon", "coordinates": [ring_ll]}}]}


def with_square_grid(df: pd.DataFrame, grid_size_m: float = 100.0) -> pd.DataFrame:
    square_df = df.copy()
    square_df["_polygon"] = [
        make_square_grid_polygon_from_lonlat(float(row["_lon"]), float(row["_lat"]), grid_size_m=grid_size_m, anchor="cell_center")
        for _, row in square_df.iterrows()
    ]
    return square_df


def legend_markdown(items: Sequence[Tuple[str, str]]) -> str:
    labels = "".join(
        f'<span class="callout-pill"><span style="display:inline-block;width:10px;height:10px;border-radius:3px;background:{color};margin-right:8px;"></span>{html.escape(label)}</span>'
        for label, color in items
    )
    return f'<div class="callout-pills">{labels}</div>'


def pick_latest_run_files(grf_dir: Path) -> Dict[str, Path]:
    if not grf_dir.exists():
        return {}
    scored = [(ts, file_path) for file_path in grf_dir.glob("*.csv") if (ts := extract_run_timestamp(file_path))]
    if not scored:
        return {}
    latest_ts = max(ts for ts, _ in scored)
    return {path.name.split("_")[0]: path for ts, path in scored if ts == latest_ts}


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
    from openai import OpenAI
    client = OpenAI()
    resp = client.chat.completions.create(model=model, messages=[{"role": "system", "content": "You are a careful data analyst. Use only provided evidence. If unsure, say so."}, {"role": "user", "content": prompt}], temperature=0.2)
    return resp.choices[0].message.content or ""


def llm_analyze_image(image_bytes: bytes, prompt: str, model: str) -> str:
    from openai import OpenAI
    client = OpenAI()
    data_url = f"data:image/png;base64,{base64.b64encode(image_bytes).decode('ascii')}"
    resp = client.responses.create(model=model, input=[{"role": "system", "content": "You are a careful data analyst. Use only provided evidence. If unsure, say so."}, {"role": "user", "content": [{"type": "input_text", "text": prompt}, {"type": "input_image", "image_url": data_url}]}], temperature=0.2)
    return resp.output_text


def first_properties(df: Optional[pd.DataFrame]) -> Dict[str, Any]:
    if df is None or df.empty or "_properties" not in df.columns:
        return {}
    return df.iloc[0]["_properties"] if isinstance(df.iloc[0]["_properties"], dict) else {}


def render_tool_mode(basemap: str) -> None:
    render_hero("격자 위치 생성기", "좌표 기준 50m~500m 격자를 바로 생성하고, 생성 결과를 지도와 GeoJSON으로 동시에 검토합니다.", ["도구 모드", "좌표 입력", "GeoJSON export", "분석용 미리보기"], "Utility")
    render_callout("사용 흐름", "경도와 위도를 넣으면 중심 기준 또는 코너 기준으로 격자를 만들고, 생성 폴리곤을 즉시 지도에서 검증할 수 있습니다.", ["기본 100m", "중심/코너 기준 선택", "다운로드 포함"])
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
    fc = ring_to_featurecollection(ring, properties={"grid_size_m": grid_size, "anchor": anchor, "input_lon": float(lon), "input_lat": float(lat)}, name="generated_grid")
    render_metric_tiles([("기준 좌표", f"{lat:.4f}, {lon:.4f}", "입력한 위도/경도 기준"), ("격자 크기", f"{grid_size}m", "한 변 길이"), ("생성 방식", "중심 기준" if anchor == "cell_center" else "코너 기준", "앵커 선택 반영"), ("출력 포맷", "GeoJSON", "바로 다운로드 가능")])
    point_df = pd.DataFrame([{"_lon": float(lon), "_lat": float(lat), "label": "입력 위치"}])
    poly_df = pd.DataFrame([{"_polygon": ring, "value": 1.0}])
    layers = build_deck_layers_polygons(poly_df, "value") + [pdk.Layer("ScatterplotLayer", point_df, id="input-point", get_position=["_lon", "_lat"], get_fill_color=[255, 124, 91, 230], get_radius=60, radius_units="meters", pickable=True)]
    view = pdk.ViewState(latitude=float(lat), longitude=float(lon), zoom=15.0, pitch=28)
    left, right = st.columns([1.45, 1.0], gap="large")
    with left:
        render_section_head("지도 미리보기", "생성된 격자 폴리곤과 입력 포인트를 한 화면에서 확인합니다.")
        st.pydeck_chart(build_deck(layers, basemap=basemap, view=view, tooltip_html="<b>{label}</b>"), use_container_width=True, height=620)
    with right:
        render_section_head("내보내기", "생성된 폴리곤을 바로 내려받고 원본 구조를 점검할 수 있습니다.")
        st.download_button("GeoJSON 다운로드", data=json.dumps(fc, ensure_ascii=False).encode("utf-8"), file_name=f"grid_{grid_size}m_lon{lon:.6f}_lat{lat:.6f}.geojson", mime="application/geo+json", type="primary", use_container_width=True)
        with st.expander("GeoJSON 미리보기", expanded=True):
            st.code(json.dumps(fc, ensure_ascii=False, indent=2), language="json")


def render_four_city_mode(basemap: str) -> None:
    ds_label = st.selectbox("지표", [DS_4CITY_CHILD.label, DS_4CITY_ELDER.label], index=0)
    dataset = DS_4CITY_CHILD if ds_label == DS_4CITY_CHILD.label else DS_4CITY_ELDER
    if not dataset.path.exists():
        st.error(f"데이터 파일을 찾을 수 없습니다: `{dataset.path}`")
        st.stop()
    df = geojson_to_rows(load_geojson(str(dataset.path)), dataset)
    if df.empty:
        st.error("GeoJSON에서 Polygon feature를 읽지 못했습니다.")
        st.stop()

    groups = sorted([g for g in df[dataset.group_col].dropna().unique().tolist() if str(g).strip()], key=region_sort_key)
    years = sorted(df[dataset.year_col].dropna().unique().tolist()) if dataset.year_col in df.columns else []
    c1, c2, c3, c4 = st.columns([1.15, 0.95, 0.95, 0.95], gap="large")
    with c1:
        scope_mode = st.radio("범위", ["전체 4개 시·구", "지역 선택"], index=0)
    with c2:
        year_sel = st.selectbox("연도", options=years, index=0) if years else None
    with c3:
        render_mode = st.selectbox("시각화", ["실제 격자", "3D 격자"], index=0)
    with c4:
        top_pct = st.slider("상위 %만 표시", min_value=1, max_value=100, value=10, step=1)

    group_sel = groups
    if scope_mode == "지역 선택":
        group_sel = st.multiselect("지역 선택", options=groups, default=groups[:2] if len(groups) > 1 else groups)

    fdf = df.copy()
    if scope_mode == "지역 선택" and group_sel:
        fdf = fdf[fdf[dataset.group_col].isin(group_sel)]
    if year_sel is not None and dataset.year_col in fdf.columns:
        fdf = fdf[fdf[dataset.year_col] == year_sel]
    if fdf.empty:
        st.warning("필터 결과가 비어있습니다.")
        st.stop()

    values = pd.to_numeric(fdf[dataset.value_col], errors="coerce")
    valid_values = values.dropna()
    if valid_values.empty:
        st.warning("현재 조건에서 수치형 점수를 읽을 수 없습니다.")
        st.stop()
    threshold = float(valid_values.min()) if top_pct >= 100 else float(np.nanpercentile(valid_values.values, 100 - top_pct))
    sdf = fdf.copy() if top_pct >= 100 else fdf[values >= threshold].copy()
    if sdf.empty:
        st.warning("상위 비율 필터 결과가 비어있습니다.")
        st.stop()

    selected_regions = "전체 4개 시·구" if scope_mode == "전체 4개 시·구" else ", ".join(map(str, group_sel[:3]))
    if scope_mode == "지역 선택" and group_sel and len(group_sel) > 3:
        selected_regions += f" 외 {len(group_sel) - 3}개"
    active_regions = groups if scope_mode == "전체 4개 시·구" else group_sel
    render_hero("4개 시·구 위험/우선순위 탐색", "실제 격자 polygon, 지역별 비교, 상위 격자, 상세 포커스를 분석 흐름에 맞게 묶었습니다.", [dataset.label, selected_regions, f"연도 {year_sel}" if year_sel is not None else "연도 전체", f"상위 {top_pct}%", render_mode], "Regional Scan")
    render_metric_tiles([("필터 후 전체 격자 수", format_count(len(fdf)), "현재 조건에 남은 실제 격자 수"), (f"상위 {top_pct}% 격자", format_count(len(sdf)), "지도에 강조되는 실제 격자 수"), ("최대 점수", format_float(float(valid_values.max())), "선택 조건 기준 최대값"), ("상위 평균", format_float(float(pd.to_numeric(sdf[dataset.value_col], errors='coerce').mean())), "강조 구간 평균")])
    st.markdown(legend_markdown([("전체 격자", "#27C2A7"), ("상위 격자 강조", "#F4B73E"), ("선택 격자", "#DAF7F1")]), unsafe_allow_html=True)
    render_callout("현재 탐색 상태", f"{selected_regions} 기준으로 실제 격자 polygon을 그대로 시각화합니다. 상위 비율은 1%부터 100%까지 모두 지원하고, 100%를 선택하면 전체 격자가 전부 보입니다. 이 화면의 목적은 '어느 권역에 어떤 위험 격자가 몰리는지'를 바로 설명하는 것입니다.", [f"연도 {year_sel}" if year_sel is not None else "연도 전체", render_mode, f"임계값 {threshold:.3f}" if top_pct < 100 else "전체 표시"])
    render_region_profile_cards(active_regions)

    top_n_max = min(500, len(sdf))
    if top_n_max <= 20:
        top_n = st.slider("우측 패널 Top N", min_value=1, max_value=top_n_max, value=top_n_max, step=1)
    else:
        top_n = st.slider("우측 패널 Top N", min_value=20, max_value=top_n_max, value=min(120, top_n_max), step=20)
    show_cols = [c for c in [dataset.id_col, dataset.group_col, dataset.year_col, dataset.value_col, "_lon", "_lat"] if c in sdf.columns]
    tdf = sdf[show_cols].sort_values(dataset.value_col, ascending=False).head(top_n).copy()
    gid_options = tdf[dataset.id_col].astype(str).tolist() if not tdf.empty else fdf[dataset.id_col].astype(str).tolist()
    selected_gid = st.selectbox("상세 격자 선택", options=gid_options, index=0)
    picked = fdf[fdf[dataset.id_col].astype(str) == selected_gid]
    selected_polygon = picked.copy() if len(picked) == 1 else pd.DataFrame()
    selected_outline = build_constant_polygon_layer(selected_polygon, layer_id="fourcity-selected-outline", fill_color=[0, 0, 0, 0], line_color=[218, 247, 241, 230], line_width_min_pixels=3, pickable=True) if not selected_polygon.empty else None
    hotspot_by_region = (
        sdf.sort_values(dataset.value_col, ascending=False)
        .groupby(dataset.group_col, as_index=False)
        .first()[[dataset.group_col, dataset.id_col, dataset.value_col]]
        .rename(columns={dataset.group_col: "지역", dataset.id_col: "대표 gid", dataset.value_col: "대표 점수"})
        .pipe(order_region_frame)
    )
    selected_score = _safe_float(picked.iloc[0][dataset.value_col]) if len(picked) == 1 else None
    region_summary = order_region_frame(
        fdf.groupby(dataset.group_col)[dataset.value_col]
        .agg(["count", "mean", "max"])
        .reset_index()
        .rename(columns={dataset.group_col: "지역", "count": "전체 격자 수", "mean": "평균 점수", "max": "최대 점수"})
    )
    compare_df = order_region_frame(
        sdf.groupby(dataset.group_col)[dataset.value_col]
        .agg(["count", "mean", "max"])
        .reset_index()
        .rename(columns={dataset.group_col: "지역", "count": f"상위 {top_pct}% 격자 수", "mean": "상위 평균", "max": "상위 최대"})
    )
    compare_df["상위 비중"] = compare_df[f"상위 {top_pct}% 격자 수"].apply(lambda x: f"{(float(x) / max(len(sdf), 1)) * 100:.1f}%")
    leading_region_row = compare_df.sort_values([f"상위 {top_pct}% 격자 수", "상위 최대"], ascending=[False, False]).iloc[0]
    leading_region = str(leading_region_row["지역"])
    leading_region_top_count = int(leading_region_row[f"상위 {top_pct}% 격자 수"])
    selected_region = str(picked.iloc[0][dataset.group_col]) if len(picked) == 1 else None
    selected_region_meta = PROJECT_REGION_META.get(selected_region or "", {})
    selected_rank_all = int((valid_values > selected_score).sum() + 1) if selected_score is not None else None
    if selected_region and selected_score is not None:
        selected_region_values = pd.to_numeric(
            fdf.loc[fdf[dataset.group_col] == selected_region, dataset.value_col],
            errors="coerce",
        ).dropna()
        selected_rank_region = int((selected_region_values > selected_score).sum() + 1)
    else:
        selected_region_values = pd.Series(dtype=float)
        selected_rank_region = None
    selection_story = (
        f"{leading_region}이 현재 조건에서 상위 {top_pct}% 격자를 가장 많이 포함합니다. "
        f"지금 선택한 격자 `{selected_gid}`는 전체 {format_count(len(fdf))}개 중 {selected_rank_all}위, "
        f"{selected_region} 내부에서는 {selected_rank_region}위 수준입니다."
        if len(picked) == 1 and selected_rank_all is not None and selected_region and selected_rank_region is not None
        else f"{leading_region}이 현재 조건에서 상위 {top_pct}% 격자를 가장 많이 포함합니다. 현재 선택 조건에서는 총 {leading_region_top_count}개의 상위 격자가 이 권역에 분포합니다."
    )
    render_callout(
        "핵심 메시지",
        selection_story,
        [
            f"선도 권역 {leading_region}",
            f"상위 격자 {leading_region_top_count}개",
            f"선택 격자 백분위 {percentile_rank(valid_values, selected_score)}" if selected_score is not None else "선택 격자 없음",
        ],
    )

    overview_view = pdk.ViewState(latitude=float(fdf["_lat"].mean()), longitude=float(fdf["_lon"].mean()), zoom=10.9, pitch=0, bearing=0)
    top_view = pdk.ViewState(latitude=float(sdf["_lat"].mean()), longitude=float(sdf["_lon"].mean()), zoom=11.45, pitch=52 if render_mode == "3D 격자" else 0, bearing=24 if render_mode == "3D 격자" else 0)
    detail_view = pdk.ViewState(latitude=float(selected_polygon["_lat"].mean()) if not selected_polygon.empty else float(sdf["_lat"].mean()), longitude=float(selected_polygon["_lon"].mean()) if not selected_polygon.empty else float(sdf["_lon"].mean()), zoom=14.2, pitch=48 if render_mode == "3D 격자" else 0, bearing=18 if render_mode == "3D 격자" else 0)

    tab_overview, tab_top, tab_compare, tab_detail = st.tabs(["전체 분포", "상위 격자", "지역 비교", "상세 격자"])

    with tab_overview:
        left, right = st.columns([1.28, 1.0], gap="large")
        layers_all: List[pdk.Layer] = build_deck_layers_polygons(fdf, dataset.value_col)
        if selected_outline is not None:
            layers_all.append(selected_outline)
        with left:
            render_section_head("전체 4개 시·구 분포", "선택한 지표의 실제 격자 polygon 전체 분포를 1:1에 가깝게 맞춘 실지도 위에서 보여줍니다.")
            st.pydeck_chart(build_deck(layers_all, basemap=basemap, view=overview_view, tooltip_html=f"<b>{{{dataset.id_col}}}</b><br/>{dataset.group_col}: {{{dataset.group_col}}}<br/>{dataset.value_col}: {{{dataset.value_col}}}"), use_container_width=True, height=760)
        with right:
            render_section_head("요약", "전체 권역에서 어느 지역이 강하게 드러나는지와 선택 격자의 상대 위치를 함께 봅니다.")
            st.dataframe(region_summary, use_container_width=True, hide_index=True, height=280)
            st.dataframe(hotspot_by_region, use_container_width=True, hide_index=True, height=210)
            if len(picked) == 1:
                c_metric1, c_metric2 = st.columns(2)
                with c_metric1:
                    st.metric("선택 격자 gid", str(selected_gid))
                    st.metric("전체 백분위", percentile_rank(valid_values, selected_score))
                with c_metric2:
                    st.metric("선택 격자 점수", format_float(selected_score))
                    st.metric(f"{selected_region} 내부 순위", f"{selected_rank_region}위" if selected_rank_region is not None else "-")
                if selected_region_meta:
                    render_callout(
                        f"{selected_region} 해석 포인트",
                        f"{selected_region_meta['summary']} 현재 선택 격자는 이 권역의 `{selected_region_meta['focus']}` 전략과 직접 연결됩니다.",
                        [selected_region_meta["theme"], selected_region_meta["focus"]],
                    )

    with tab_top:
        left, right = st.columns([1.58, 1.0], gap="large")
        layers_top: List[pdk.Layer] = [build_extruded_polygon_layer(sdf, dataset.value_col, layer_id="fourcity-top-3d", elevation_scale=4.5, line_color=[220, 240, 236, 40])] if render_mode == "3D 격자" else build_deck_layers_polygons(sdf, dataset.value_col)
        if selected_outline is not None:
            layers_top.append(selected_outline)
        with left:
            render_section_head("상위 격자 지도", "상위 비율로 추린 실제 격자만 별도로 강조합니다.")
            st.pydeck_chart(build_deck(layers_top, basemap=basemap, view=top_view, tooltip_html=f"<b>{{{dataset.id_col}}}</b><br/>{dataset.group_col}: {{{dataset.group_col}}}<br/>{dataset.value_col}: {{{dataset.value_col}}}"), use_container_width=True, height=720)
        with right:
            render_section_head("상위 격자 표", "상위 비율로 남은 격자를 순위처럼 정렬하고, 권역별 대표 격자를 함께 봅니다.")
            st.dataframe(tdf, use_container_width=True, height=420)
            st.dataframe(hotspot_by_region, use_container_width=True, hide_index=True, height=210)
            st.download_button("상위 격자 CSV 다운로드", data=tdf.to_csv(index=False).encode("utf-8-sig"), file_name="top_grids.csv", mime="text/csv", use_container_width=True)

    with tab_compare:
        left, right = st.columns([1.2, 1.35], gap="large")
        with left:
            render_section_head("지역별 비교", "같은 조건에서 어느 지역에 상위 격자가 많이 몰리는지 비교합니다.")
            st.dataframe(compare_df, use_container_width=True, hide_index=True, height=320)
        with right:
            render_section_head("선택 격자 해석", "선택 격자가 전체 분포와 지역 맥락에서 어떤 위치인지 먼저 읽고, 원본 속성은 아래에서 확인합니다.")
            if len(picked) == 1:
                interpretation_df = pd.DataFrame(
                    {
                        "항목": ["gid", "지역", "점수", "전체 백분위", "전체 순위", "지역 내 순위"],
                        "값": [
                            selected_gid,
                            selected_region,
                            format_float(selected_score),
                            percentile_rank(valid_values, selected_score),
                            f"{selected_rank_all}위" if selected_rank_all is not None else "-",
                            f"{selected_rank_region}위" if selected_rank_region is not None else "-",
                        ],
                    }
                )
                st.dataframe(interpretation_df, use_container_width=True, hide_index=True, height=245)
                with st.expander("원본 속성 보기", expanded=False):
                    st.json(dict(picked.iloc[0]["_properties"]))
            else:
                st.info("선택 격자 정보를 찾지 못했습니다.")

    with tab_detail:
        left, right = st.columns([1.58, 1.0], gap="large")
        local_df = fdf.copy()
        if len(picked) == 1:
            sel_lon = float(picked.iloc[0]["_lon"])
            sel_lat = float(picked.iloc[0]["_lat"])
            local_df = local_df[(local_df["_lon"] - sel_lon).abs() < 0.015]
            local_df = local_df[(local_df["_lat"] - sel_lat).abs() < 0.015]
        detail_layers: List[pdk.Layer] = build_deck_layers_polygons(local_df, dataset.value_col)
        if selected_outline is not None:
            detail_layers.append(selected_outline)
        with left:
            render_section_head("선택 격자 포커스", "선택한 격자와 주변 실제 격자 셀을 같이 보면서 위치 맥락을 확인합니다.")
            st.pydeck_chart(build_deck(detail_layers, basemap=basemap, view=detail_view, tooltip_html=f"<b>{{{dataset.id_col}}}</b><br/>{dataset.group_col}: {{{dataset.group_col}}}<br/>{dataset.value_col}: {{{dataset.value_col}}}"), use_container_width=True, height=720)
        with right:
            render_section_head("상세 정보", "선택 격자의 원본 속성과 함께 왜 이 셀이 중요한지까지 바로 읽히게 구성했습니다.")
            if len(picked) == 1:
                props = dict(picked.iloc[0]["_properties"])
                render_callout(
                    "선택 셀 포지션",
                    f"`{selected_gid}`는 {selected_region} 권역에서 {selected_rank_region}위, 전체 분포에서는 상위 {percentile_rank(valid_values, selected_score)} 수준입니다.",
                    [f"점수 {format_float(selected_score)}", f"전체 {selected_rank_all}위" if selected_rank_all is not None else "전체 순위 -"],
                )
                detail_table = pd.DataFrame({"항목": list(props.keys()), "값": list(props.values())})
                st.dataframe(detail_table, use_container_width=True, hide_index=True, height=520)
            else:
                st.info("선택 격자 상세를 찾지 못했습니다.")


def render_gyosan_mode(basemap: str, latest_files: Dict[str, Path], model: str) -> None:
    if not GYOSAN_GRID.path.exists() or not GYOSAN_SELECTED_K20.path.exists():
        st.error("하남교산 시각화에 필요한 데이터 파일을 찾을 수 없습니다.")
        st.stop()
    grid_df = geojson_to_rows(load_geojson(str(GYOSAN_GRID.path)), GYOSAN_GRID)
    k20_df = geojson_to_rows(load_geojson(str(GYOSAN_SELECTED_K20.path)), GYOSAN_SELECTED_K20)
    combined_df = geojson_to_rows(load_geojson(str(GYOSAN_COMBINED_SELECTED.path)), GYOSAN_COMBINED_SELECTED) if GYOSAN_COMBINED_SELECTED.path.exists() else None
    if k20_df.empty:
        st.error("하남교산 후보지 데이터를 읽지 못했습니다.")
        st.stop()

    combined_props = first_properties(combined_df)
    facility_options = sorted({str(props.get("facility")) for props in combined_df["_properties"] if props.get("facility") is not None}) if (combined_df is not None and combined_props and "facility" in combined_props) else []
    c1, c2, c3 = st.columns([1.1, 0.95, 0.95], gap="large")
    with c1:
        facility_filter = st.multiselect("시설 타입 오버레이", options=facility_options, default=facility_options)
    with c2:
        show_base_grid = st.toggle("하남교산 전체 형태 표시", value=True)
    with c3:
        use_3d = st.toggle("3D 표현 강조", value=True)

    overlay_count = 0 if combined_df is None or combined_df.empty else (len(combined_df) if not facility_filter else int(combined_df["_properties"].apply(lambda p: p.get("facility") in set(facility_filter)).sum()))
    render_hero("하남교산 후보지 + 시설 오버레이", "원본 GeoJSON 격자 polygon과 원본 시설 polygon을 실지도 위에 그대로 얹고, 탭별로 전체 분포, 3D 후보지, 시설 타입, 상세 포커스를 나눠 보도록 재구성했습니다.", ["후보지 k=20", f"시설 오버레이 {overlay_count:,}개" if overlay_count else "시설 오버레이 준비", "원본 polygon 기준", "3D 강조" if use_3d else "평면 중심"], "Site Strategy")
    render_metric_tiles([("후보지 수", format_count(len(k20_df)), "선정된 k=20 격자"), ("기본 격자 수", format_count(len(grid_df)), "배경 레이어"), ("오버레이 수", format_count(overlay_count), "선택된 시설 타입 기준"), ("최고 우선순위 점수", format_float(pd.to_numeric(k20_df[GYOSAN_SELECTED_K20.value_col], errors="coerce").max()), "후보지 집합 기준")])
    st.markdown(legend_markdown([("후보지 격자", "#27C2A7"), ("고득점 후보지", "#F4B73E"), ("CCTV", "#FF7C5B"), ("비상벨", "#F4B73E"), ("선택 격자 강조선", "#DAF7F1")]), unsafe_allow_html=True)
    render_callout("해석 포인트", "선택한 후보지와 시설이 모두 원본 polygon 기준으로 보이도록 바꿨습니다. 따라서 실제 어디 셀에 어떤 형태로 설치하는지 설명이 훨씬 직접적입니다.", [*(facility_filter or ["시설 전체"]), "원본 polygon", "선택 연동", "근거 요약 지원"])

    base_grid_df = grid_df.copy()
    candidate_grid_df = k20_df.copy()
    facility_grid_df = combined_df.copy() if combined_df is not None else pd.DataFrame()
    if not facility_grid_df.empty and facility_filter:
        facility_grid_df = facility_grid_df[facility_grid_df["_properties"].apply(lambda p: p.get("facility") in set(facility_filter))]

    rows = [{key: row["_properties"].get(key) for key in ["selected_order", "gid", "우선순위_점수", "우선순위_순위", "미성년자_유동_추정", "blockType", "도로_격자_여부", "incremental_weighted_coverage"]} for _, row in k20_df.iterrows()]
    tdf = pd.DataFrame(rows).sort_values("selected_order").reset_index(drop=True)

    top_controls, side_controls = st.columns([1.6, 1.0], gap="large")
    with top_controls:
        selected_gid = st.selectbox("선택 후보지", options=tdf["gid"].astype(str).tolist(), index=0)
    with side_controls:
        compare_rank = st.slider("상위 강조 개수", min_value=3, max_value=min(20, len(tdf)), value=min(8, len(tdf)), step=1)

    selected_candidate = candidate_grid_df[candidate_grid_df["gid"].astype(str) == selected_gid]
    selected_outline = build_constant_polygon_layer(selected_candidate, layer_id="selected-grid-outline", fill_color=[0, 0, 0, 0], line_color=[218, 247, 241, 220], line_width_min_pixels=4, pickable=True) if not selected_candidate.empty else None
    top_rank_ids = set(tdf.head(compare_rank)["gid"].astype(str).tolist())
    top_rank_df = candidate_grid_df[candidate_grid_df["gid"].astype(str).isin(top_rank_ids)]
    selected_facilities = facility_grid_df[facility_grid_df["gid"].astype(str) == selected_gid] if not facility_grid_df.empty else pd.DataFrame()
    selected_raw = k20_df[k20_df["gid"].astype(str) == selected_gid]
    selected_props = dict(selected_raw.iloc[0]["_properties"]) if not selected_raw.empty else {}
    selected_facility_names = sorted({str(row["_properties"].get("facility")) for _, row in selected_facilities.iterrows() if row["_properties"].get("facility")})
    placement_action = ", ".join(selected_facility_names) if selected_facility_names else "시설 배치 정보 없음"
    selected_priority_score = format_float(_safe_float(selected_props.get("우선순위_점수")))
    selected_incremental_coverage = format_float(_safe_float(selected_props.get("incremental_weighted_coverage")))
    placement_story = (
        f"선택 후보지 `{selected_gid}`는 {selected_props.get('selected_order', '-')}순위 후보지이며, "
        f"우선순위 점수 {selected_priority_score}와 증분 커버리지 {selected_incremental_coverage} 기준으로 읽을 수 있습니다. "
        f"현재 필터 기준 설치 형태는 {placement_action}입니다."
    )
    render_callout(
        "선택 후보지 권고안",
        placement_story,
        [
            f"blockType {selected_props.get('blockType', '-')}",
            f"순위 {selected_props.get('selected_order', '-')}",
            placement_action,
        ],
    )

    overview_view = pdk.ViewState(latitude=float(candidate_grid_df["_lat"].mean()), longitude=float(candidate_grid_df["_lon"].mean()), zoom=12.35, pitch=0, bearing=0)
    view_3d = pdk.ViewState(latitude=float(candidate_grid_df["_lat"].mean()), longitude=float(candidate_grid_df["_lon"].mean()), zoom=12.55, pitch=56 if use_3d else 20, bearing=28)
    detail_view = pdk.ViewState(latitude=float(selected_candidate["_lat"].mean()) if not selected_candidate.empty else float(candidate_grid_df["_lat"].mean()), longitude=float(selected_candidate["_lon"].mean()) if not selected_candidate.empty else float(candidate_grid_df["_lon"].mean()), zoom=14.9, pitch=58 if use_3d else 22, bearing=24)

    tab_overview, tab_3d, tab_facility, tab_detail = st.tabs(["종합 현황", "3D 후보지", "시설 오버레이", "상세 포커스"])

    with tab_overview:
        left, right = st.columns([1.55, 1.0], gap="large")
        overview_layers: List[pdk.Layer] = []
        if show_base_grid and not base_grid_df.empty:
            overview_layers.append(build_constant_polygon_layer(base_grid_df, layer_id="overview-base-grid", fill_color=[204, 212, 216, 18], line_color=[124, 134, 142, 38], line_width_min_pixels=1, pickable=False))
        overview_layers.extend(build_deck_layers_polygons(candidate_grid_df, GYOSAN_SELECTED_K20.value_col))
        overview_layers.append(build_constant_polygon_layer(top_rank_df, layer_id="overview-top-rank", fill_color=[244, 183, 62, 110], line_color=[248, 217, 131, 180], line_width_min_pixels=2, pickable=True))
        if selected_outline is not None:
            overview_layers.append(selected_outline)
        with left:
            render_section_head("전체 후보지 분포", "하남교산 전체 형태를 먼저 보여주고, 그 위에 후보지와 커버리지를 오버레이해서 읽을 수 있게 했습니다.")
            st.pydeck_chart(build_deck(overview_layers, basemap=basemap, view=overview_view, tooltip_html="<b>{gid}</b><br/>우선순위_점수: {우선순위_점수}<br/>selected_order: {selected_order}"), use_container_width=True, height=720)
        with right:
            render_section_head("상위 후보 비교", "선택 후보와 함께 상위권 후보를 비교해서 상대적인 위치와 점수를 바로 확인합니다.")
            st.dataframe(tdf.head(compare_rank), use_container_width=True, height=320)
            if selected_props:
                c_metric1, c_metric2 = st.columns(2)
                with c_metric1:
                    st.metric("선택 후보 순위", selected_props.get("selected_order", "-"))
                    st.metric("설치 형태", placement_action)
                with c_metric2:
                    st.metric("우선순위 점수", format_float(_safe_float(selected_props.get("우선순위_점수"))))
                    st.metric("증분 커버리지", format_float(_safe_float(selected_props.get("incremental_weighted_coverage"))))
                render_callout(
                    "설치 판단",
                    f"{selected_props.get('blockType', '-') or '-'} 유형 블록에서 {placement_action} 조합을 검토하는 흐름입니다. 선택 후보는 상위권 비교에서도 지속적으로 살아남는 셀입니다.",
                    [f"gid {selected_gid}", f"rank {selected_props.get('selected_order', '-')}"],
                )

    with tab_3d:
        left, right = st.columns([1.55, 1.0], gap="large")
        layers_3d: List[pdk.Layer] = []
        if show_base_grid and not base_grid_df.empty:
            layers_3d.append(build_constant_polygon_layer(base_grid_df, layer_id="grid-3d-base", fill_color=[196, 204, 210, 10], line_color=[118, 126, 133, 24], line_width_min_pixels=1, pickable=False))
        layers_3d.append(build_extruded_polygon_layer(candidate_grid_df, GYOSAN_SELECTED_K20.value_col, layer_id="grid-3d-candidate", elevation_scale=4.8 if use_3d else 1.8, line_color=[220, 240, 236, 34]))
        if selected_outline is not None:
            layers_3d.append(selected_outline)
        with left:
            render_section_head("후보지 3D 격자", "점수가 높을수록 더 높게 솟아오르도록 만들어서 어느 위치가 상대적으로 강한지 즉시 읽히게 했습니다.")
            st.pydeck_chart(build_deck(layers_3d, basemap=basemap, view=view_3d, tooltip_html="<b>{gid}</b><br/>우선순위_점수: {우선순위_점수}<br/>우선순위_순위: {우선순위_순위}"), use_container_width=True, height=720)
        with right:
            render_section_head("3D 해석 기준", "높이는 우선순위 점수, 외곽 강조선은 현재 선택 후보를 뜻합니다.")
            st.markdown(legend_markdown([("낮은 우선순위", "#235261"), ("중간 우선순위", "#27C2A7"), ("높은 우선순위", "#F4B73E"), ("선택 후보", "#DAF7F1")]), unsafe_allow_html=True)
            if selected_props:
                detail_df = pd.DataFrame({"항목": ["gid", "selected_order", "우선순위_점수", "우선순위_순위", "미성년자_유동_추정", "blockType"], "값": [selected_props.get("gid"), selected_props.get("selected_order"), selected_props.get("우선순위_점수"), selected_props.get("우선순위_순위"), selected_props.get("미성년자_유동_추정"), selected_props.get("blockType")]})
                st.dataframe(detail_df, use_container_width=True, hide_index=True, height=260)
                render_callout(
                    "3D 해석 문장",
                    f"현재 선택 후보지는 3D 장면에서도 봉우리처럼 분리되어 보여야 하는 셀입니다. 이 장면은 주변 대비 상대 강도를 읽는 분석 용도로 보면 됩니다.",
                    [f"우선순위 {selected_props.get('우선순위_순위', '-')}", f"유동 추정 {selected_props.get('미성년자_유동_추정', '-')}"],
                )

    with tab_facility:
        left, right = st.columns([1.55, 1.0], gap="large")
        facility_layers: List[pdk.Layer] = []
        if show_base_grid and not base_grid_df.empty:
            facility_layers.append(build_constant_polygon_layer(base_grid_df, layer_id="facility-base-grid", fill_color=[204, 212, 216, 16], line_color=[124, 134, 142, 36], line_width_min_pixels=1, pickable=False))
        facility_layers.append(build_constant_polygon_layer(candidate_grid_df, layer_id="facility-candidate-grid", fill_color=[39, 194, 167, 48], line_color=[84, 188, 173, 72], line_width_min_pixels=1, pickable=True))
        if selected_outline is not None:
            facility_layers.append(selected_outline)
        if not facility_grid_df.empty:
            for facility_name, color in FACILITY_PALETTE.items():
                facility_subset = facility_grid_df[facility_grid_df["_properties"].apply(lambda p: p.get("facility") == facility_name)]
                if not facility_subset.empty:
                    facility_layers.append(build_constant_polygon_layer(facility_subset, layer_id=f"facility-{facility_name}", fill_color=color, line_color=[245, 245, 245, 120], line_width_min_pixels=2, pickable=True))
        with left:
            render_section_head("시설 타입 오버레이", "어떤 후보지에 어떤 시설 타입을 올릴지 실지도 위에서 격자 단위로 구분해서 보여줍니다.")
            st.pydeck_chart(build_deck(facility_layers, basemap=basemap, view=overview_view, tooltip_html="<b>{gid}</b><br/>facility: {facility}<br/>selected_order: {selected_order}"), use_container_width=True, height=720)
        with right:
            render_section_head("시설 배치 요약", "선택한 시설 필터 기준으로 몇 개가 어떤 타입으로 배정됐는지 확인합니다.")
            if not facility_grid_df.empty:
                facility_summary = pd.DataFrame(
                    [{"시설": name, "개수": int((facility_grid_df["_properties"].apply(lambda p: p.get("facility") == name)).sum())} for name in facility_filter]
                )
                st.dataframe(facility_summary, use_container_width=True, hide_index=True, height=180)
            if not selected_facilities.empty:
                selected_facility_table = pd.DataFrame(
                    [{"facility": row["_properties"].get("facility"), "selected_order": row["_properties"].get("selected_order"), "incremental_gain": row["_properties"].get("incremental_gain")} for _, row in selected_facilities.iterrows()]
                )
                st.dataframe(selected_facility_table, use_container_width=True, hide_index=True, height=220)
                render_callout(
                    "선택 후보지 배치 해석",
                    f"`{selected_gid}`에는 현재 {placement_action}가 연결되어 있습니다. 오버레이 탭에서는 설치 타입을 격자 단위로 분리해 보여주므로, 실제 어느 셀에 무엇을 두는지 바로 읽을 수 있습니다.",
                    [f"시설 {len(selected_facility_names)}종", f"gid {selected_gid}"],
                )
            else:
                st.info("선택 후보지에 연결된 시설 오버레이가 현재 필터 기준으로 없습니다.")

    with tab_detail:
        left, right = st.columns([1.45, 1.1], gap="large")
        detail_layers: List[pdk.Layer] = []
        local_base = base_grid_df.copy()
        if not selected_candidate.empty and not local_base.empty:
            sel_lon = float(selected_candidate.iloc[0]["_lon"])
            sel_lat = float(selected_candidate.iloc[0]["_lat"])
            local_base = local_base[(local_base["_lon"] - sel_lon).abs() < 0.01]
            local_base = local_base[(local_base["_lat"] - sel_lat).abs() < 0.01]
        if show_base_grid and not local_base.empty:
            detail_layers.append(build_constant_polygon_layer(local_base, layer_id="detail-base-grid", fill_color=[196, 204, 210, 12], line_color=[118, 126, 133, 28], line_width_min_pixels=1, pickable=False))
        if not selected_candidate.empty:
            detail_layers.append(build_extruded_polygon_layer(selected_candidate, GYOSAN_SELECTED_K20.value_col, layer_id="detail-selected-3d", elevation_scale=7.0 if use_3d else 2.2, line_color=[255, 248, 230, 180], line_width_min_pixels=3, opacity_boost=240))
            detail_layers.append(build_constant_polygon_layer(selected_candidate, layer_id="detail-selected-outline", fill_color=[0, 0, 0, 0], line_color=[255, 250, 232, 255], line_width_min_pixels=4, pickable=True))
        if not selected_facilities.empty:
            for facility_name, color in FACILITY_PALETTE.items():
                subset = selected_facilities[selected_facilities["_properties"].apply(lambda p: p.get("facility") == facility_name)]
                if not subset.empty:
                    detail_layers.append(build_constant_polygon_layer(subset, layer_id=f"detail-{facility_name}", fill_color=color, line_color=[250, 250, 250, 180], line_width_min_pixels=2, pickable=True))
        with left:
            render_section_head("선택 후보지 포커스", "선택한 후보지를 크게 띄우고, 주변 격자와 시설 타입을 함께 보면서 실제 배치 장면처럼 읽히게 했습니다.")
            st.pydeck_chart(build_deck(detail_layers, basemap=basemap, view=detail_view, tooltip_html="<b>{gid}</b><br/>facility: {facility}<br/>우선순위_점수: {우선순위_점수}"), use_container_width=True, height=760)
        with right:
            render_section_head("상세 패널", "선택 후보지 속성, 시설 배치 형태, 근거 요약을 한곳에 모았습니다.")
            uploaded = st.file_uploader("지도/도표 스크린샷 업로드(선택)", type=["png", "jpg", "jpeg"])
            if selected_props:
                summary_df = pd.DataFrame({"항목": ["gid", "selected_order", "우선순위_점수", "우선순위_순위", "미성년자_유동_추정", "incremental_weighted_coverage", "blockType", "도로_격자_여부"], "값": [selected_props.get("gid"), selected_props.get("selected_order"), selected_props.get("우선순위_점수"), selected_props.get("우선순위_순위"), selected_props.get("미성년자_유동_추정"), selected_props.get("incremental_weighted_coverage"), selected_props.get("blockType"), selected_props.get("도로_격자_여부")]})
                st.dataframe(summary_df, use_container_width=True, hide_index=True, height=280)
                render_callout(
                    "최종 제안 문장",
                    f"`{selected_gid}`는 {selected_props.get('selected_order', '-')}순위 후보지이며, {placement_action} 형태를 우선 검토하는 안으로 정리할 수 있습니다. 이 패널은 점수, 커버리지, 블록 유형, 시설 타입을 한 번에 묶어 보여줍니다.",
                    [f"rank {selected_props.get('selected_order', '-')}", f"coverage {selected_incremental_coverage}"],
                )
                if not selected_facilities.empty:
                    facility_lines = [f"{row['_properties'].get('facility')} / incremental_gain={row['_properties'].get('incremental_gain')}" for _, row in selected_facilities.iterrows()]
                else:
                    facility_lines = ["시설 오버레이 정보 없음"]
                st.markdown("**배치 해석**")
                st.markdown(f"- 선택 후보지: `{selected_gid}`")
                st.markdown(f"- 설치 형태: {', '.join(facility_lines)}")
                st.markdown(f"- 해석 포인트: 순위 {selected_props.get('selected_order')}번 후보지이며 우선순위 점수 {selected_props.get('우선순위_점수')} 기준으로 선정되었습니다.")
                context_lines = ["- dataset: 하남교산 설치 후보지(k=20)", f"- gid: {selected_gid}", "", "격자 속성:", json.dumps(selected_props, ensure_ascii=False), "", "시설 배치:", *facility_lines]
                if latest_files:
                    global_imp = try_load_csv(latest_files.get("global", Path(""))) if latest_files.get("global") else None
                    shap_imp = try_load_csv(latest_files.get("shap", Path(""))) if latest_files.get("shap") else None
                    if global_imp is not None:
                        context_lines += ["", "global_importance 상위 15행:", global_imp.head(15).to_csv(index=False)]
                    if shap_imp is not None:
                        context_lines += ["", "shap_importance 상위 15행:", shap_imp.head(15).to_csv(index=False)]
                prompt = "\n".join(context_lines) + "\n\n요청: 위 근거만 사용해서 (1) 왜 여기가 후보로 선택됐는지 5줄, (2) 어떤 형태로 설치하는 게 적절한지 3줄로 설명해줘. 근거 없으면 근거 부족이라고 해."
                if st.button("근거 요약 생성", type="primary", use_container_width=True):
                    if not llm_available():
                        st.error("OPENAI_API_KEY 또는 openai 패키지가 없어 요약이 비활성화됩니다.")
                    else:
                        with st.spinner("요약 생성 중..."):
                            try:
                                summary = llm_analyze_image(uploaded.getvalue(), prompt=prompt, model=model) if uploaded is not None else llm_summarize(prompt=prompt, model=model)
                                st.markdown(summary)
                            except Exception as e:
                                st.exception(e)


def main() -> None:
    st.set_page_config(page_title=APP_TITLE, layout="wide", initial_sidebar_state="expanded")
    inject_css()
    with st.sidebar:
        render_sidebar_brand()
        st.header("탐색 모드")
        mode = st.radio("보기", ["4개 시·구 (관측 위험/우선순위)", "하남교산 (적용/설치 오버레이)", "도구: 격자 위치 생성기"], index=0)
        basemap = MAP_STYLES[st.selectbox("지도 스타일", options=list(MAP_STYLES.keys()), index=0)]
        st.divider()
        st.subheader("데이터 상태")
        grf_dir = st.text_input("grf_06_outputs 경로", value=str(GRF_OUTPUT_DIR))
        latest_files = pick_latest_run_files(Path(grf_dir))
        if latest_files:
            timestamps = [ts for ts in (extract_run_timestamp(path) for path in latest_files.values()) if ts is not None]
            st.success(f"최신 run 감지: {max(timestamps).strftime('%Y-%m-%d %H:%M:%S')}" if timestamps else "최신 run 감지")
        else:
            st.caption("공간 RF/SHAP 결과가 없어도 대시보드는 동작합니다.")
        st.divider()
        st.subheader("분석 어시스턴트")
        model = st.text_input("모델명", value=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"))
        if os.getenv("OPENAI_API_KEY") and not llm_available():
            st.warning("OPENAI_API_KEY는 있으나 `openai` 패키지가 없어 비활성화되어 있습니다.")
            st.caption("필요 시: `pip install openai`")
        elif llm_available():
            st.success("근거 요약 기능 사용 가능")
        else:
            st.caption("키가 없으면 요약 기능은 비활성화됩니다.")
        st.markdown('<p class="small-note">필터, 지도, 상세 패널을 분석 중심으로 정리했습니다.</p>', unsafe_allow_html=True)

    if mode.startswith("도구"):
        render_tool_mode(basemap)
    elif not dashboard_data_available():
        render_public_safe_mode(mode=mode, basemap=basemap, latest_files=latest_files)
    elif mode.startswith("4개"):
        render_four_city_mode(basemap)
    else:
        render_gyosan_mode(basemap, latest_files=latest_files, model=model)


if __name__ == "__main__":
    main()
