#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
4개 시·구(동탄·판교·위례·미사)와 하남 교산 지역 지도를 생성합니다.
PPT 프로젝트 개요 슬라이드용: 2기 신도시(4개 시구) → 3기 신도시(하남 교산) 적용.

- 지역별 연한 채우기 + 경계선, 미사는 화살표 라벨로 하남·교산과 구분
- 범례(참조 지역 / 적용 지역), 제목·부제, 교산은 점선으로 강조

출력: data/통합_데이터/시각화_공유/4개시구_하남교산_경계_지도.png
"""
from __future__ import annotations

import sys
from pathlib import Path

# 프로젝트 루트
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# 배경 지도 사용 여부 (contextily 필요, 네트워크 필요)
USE_BASEMAP = False

# mg.gpkg 경로 (있으면 레이어 목록에서 4시구·교산 경계 추출 시도, 없으면 GeoJSON만 사용)
MG_GPKG_PATH = None  # 예: ROOT / "data" / "mg.gpkg" 또는 Path(r"c:/Users/a0109/Downloads/mg.gpkg")


def _set_korean_font():
    """한글 표시를 위해 matplotlib 폰트를 한글 지원 폰트로 설정."""
    import matplotlib.pyplot as plt
    import matplotlib.font_manager as fm
    candidates = ["Malgun Gothic", "맑은 고딕", "NanumGothic", "Nanum Gothic", "AppleGothic"]
    for name in candidates:
        if any(f.name == name for f in fm.fontManager.ttflist):
            plt.rcParams["font.family"] = name
            plt.rcParams["axes.unicode_minus"] = False
            return
    # 한글 폰트를 못 찾으면 경고만 하고 기본값 유지
    import warnings
    warnings.warn("한글 폰트를 찾지 못했습니다. 라벨이 깨질 수 있습니다.", UserWarning)


def main() -> None:
    import geopandas as gpd
    import matplotlib.pyplot as plt

    _set_korean_font()

    # 4개 시구 gbn → 표시명 (동탄·판교·위례·미사)
    GBN_TO_LABEL = {
        "경기도 성남시": "판교",
        "경기도 화성시": "동탄",
        "경기도 하남시": "미사",
        "서울특별시 송파구": "위례",
        "서울 송파구": "위례",
    }

    # 01: 4개 시·구 격자
    path_01 = ROOT / "data" / "격자_데이터" / "01._격자_(4개_시·구).geojson"
    if not path_01.exists():
        raise FileNotFoundError(f"격자 파일 없음: {path_01}")
    gdf_01 = gpd.read_file(path_01)
    gdf_01 = gdf_01.to_crs(epsg=4326)

    if "gbn" not in gdf_01.columns:
        raise ValueError("01 격자에 'gbn' 컬럼이 없습니다.")
    dissolved_01 = gdf_01.dissolve(by="gbn", as_index=False)

    # 02: 하남 교산 격자
    path_02 = ROOT / "data" / "격자_데이터" / "02._격자_(하남교산).geojson"
    if not path_02.exists():
        raise FileNotFoundError(f"격자 파일 없음: {path_02}")
    gdf_02 = gpd.read_file(path_02)
    gdf_02 = gdf_02.to_crs(epsg=4326)
    boundary_02 = gdf_02.geometry.union_all() if hasattr(gdf_02.geometry, "union_all") else gdf_02.geometry.unary_union

    # 전체 범위 (배경/축 한계)
    all_bounds = list(dissolved_01.total_bounds)
    if boundary_02 and not boundary_02.is_empty:
        b = boundary_02.bounds
        all_bounds = [
            min(all_bounds[0], b[0]), min(all_bounds[1], b[1]),
            max(all_bounds[2], b[2]), max(all_bounds[3], b[3]),
        ]
    margin = 0.02
    all_bounds[0] -= margin
    all_bounds[1] -= margin
    all_bounds[2] += margin
    all_bounds[3] += margin

    # 색상: 라벨별 고정 (참조 지역)
    LABEL_COLOR = {"판교": "#2563eb", "위례": "#dc2626", "동탄": "#16a34a", "미사": "#ca8a04"}
    fill_alpha = 0.22
    edge_lw = 2.2

    fig, ax = plt.subplots(1, 1, figsize=(10, 10))
    ax.set_xlim(all_bounds[0], all_bounds[2])
    ax.set_ylim(all_bounds[1], all_bounds[3])
    ax.set_aspect("equal")
    ax.set_facecolor("#fafafa")

    if USE_BASEMAP:
        try:
            import contextily as ctx
            ctx.add_basemap(ax, crs=4326, source=ctx.providers.CartoDB.Positron)
        except Exception as e:
            print(f"배경 지도 스킵: {e}")

    # 4개 시구: 연한 채우기 + 경계선, 라벨(미사 제외 → 화살표로 따로)
    misa_geom = None
    misa_color = None
    for i, row in dissolved_01.iterrows():
        gbn = row["gbn"]
        label = GBN_TO_LABEL.get(gbn, gbn)
        geom = row.geometry
        if geom is None:
            continue
        color = LABEL_COLOR.get(label, "#666666")
        if label == "미사":
            misa_geom = geom
            misa_color = color
        gpd.GeoSeries([geom]).plot(ax=ax, facecolor=color, edgecolor=color, linewidth=edge_lw, alpha=fill_alpha)
        gpd.GeoSeries([geom]).boundary.plot(ax=ax, color=color, linewidth=edge_lw)
        if label != "미사":
            try:
                c = geom.centroid
                ax.annotate(label, (c.x, c.y), fontsize=13, fontweight="bold", ha="center", va="center")
            except Exception:
                pass

    # 하남 교산: 연한 보라 채우기 + 점선 경계 (적용 대상 강조)
    if boundary_02 and not boundary_02.is_empty:
        gpd.GeoSeries([boundary_02]).plot(ax=ax, facecolor="#7c3aed", edgecolor="none", alpha=fill_alpha)
        try:
            bnd = boundary_02.boundary if hasattr(boundary_02, "boundary") and boundary_02.boundary else None
            if bnd is not None and not getattr(bnd, "is_empty", True):
                gpd.GeoSeries([bnd]).plot(ax=ax, color="#5b21b6", linewidth=edge_lw, linestyle="--")
            else:
                gpd.GeoSeries([boundary_02]).boundary.plot(ax=ax, color="#5b21b6", linewidth=edge_lw, linestyle="--")
        except Exception:
            gpd.GeoSeries([boundary_02]).boundary.plot(ax=ax, color="#5b21b6", linewidth=edge_lw, linestyle="--")
        b = boundary_02.bounds
        cx_gyo, cy_gyo = (b[0] + b[2]) / 2, (b[1] + b[3]) / 2
        ax.annotate("하남 교산", (cx_gyo, cy_gyo), fontsize=13, fontweight="bold", ha="center", va="center", color="#4c1d95")

    # 미사: 화살표 라벨 (하남 쪽이므로 라벨은 영역 밖·화살표가 미사(교산 제외) 쪽을 가리키게)
    if misa_geom is not None and misa_color is not None and boundary_02 and not boundary_02.is_empty:
        try:
            diff = misa_geom.difference(boundary_02)
            if diff and not diff.is_empty and getattr(diff, "area", 0) > 1e-12:
                pt_arrow = diff.centroid  # 화살표가 가리킬 점: 미사 중 교산 제외 영역
            else:
                pt_arrow = misa_geom.centroid
        except Exception:
            pt_arrow = misa_geom.centroid
        # 라벨 텍스트 위치: 미사 영역 북쪽 바깥(위쪽)
        bx = misa_geom.bounds
        label_x = (bx[0] + bx[2]) / 2
        label_y = bx[3] + 0.012
        ax.annotate(
            "미사",
            xy=(pt_arrow.x, pt_arrow.y),
            xytext=(label_x, label_y),
            fontsize=13,
            fontweight="bold",
            ha="center",
            va="center",
            color=misa_color,
            arrowprops=dict(arrowstyle="->", color=misa_color, lw=1.8, connectionstyle="arc3,rad=0"),
        )

    ax.set_axis_off()
    # 범례: 참조 지역(2기) / 적용 지역(3기)
    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch
    leg_ref = [Patch(facecolor=LABEL_COLOR[l], edgecolor=LABEL_COLOR[l], alpha=fill_alpha, label=l) for l in ["판교", "위례", "동탄", "미사"]]
    leg_app = [Patch(facecolor="#7c3aed", edgecolor="#5b21b6", alpha=fill_alpha, label="하남 교산")]
    leg1 = ax.legend(handles=leg_ref, title="참조 지역 (2기 신도시)", loc="upper left", fontsize=10, title_fontsize=10)
    ax.add_artist(leg1)
    ax.legend(handles=leg_app, title="적용 지역 (3기 신도시)", loc="lower left", fontsize=10, title_fontsize=10)
    ax.set_title("4개 시·구(동탄·판교·위례·미사) 및 하남 교산", fontsize=15, fontweight="bold")
    ax.text(0.5, 0.02, "2기 신도시 4개 시·구 데이터 → 하남 교산(3기) 적용", transform=ax.transAxes, fontsize=11, ha="center", color="#555")
    plt.tight_layout(rect=[0, 0.02, 1, 0.98])

    out_dir = ROOT / "data" / "통합_데이터" / "시각화_공유"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "4개시구_하남교산_경계_지도.png"
    plt.savefig(out_path, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close()
    print(f"저장: {out_path}")


if __name__ == "__main__":
    main()
