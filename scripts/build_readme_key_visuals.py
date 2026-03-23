#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap


ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parent
TOOLS_DIR = WORKSPACE / "tools" / "lh_readme_vis_data"
OUT_IMG_DIR = ROOT / "docs" / "images"
OUT_DATA_DIR = ROOT / "docs" / "data"


def set_korean_font() -> None:
    candidates = [
        "Malgun Gothic",
        "AppleGothic",
        "NanumGothic",
        "Nanum Gothic",
    ]
    for name in candidates:
        try:
            mpl.rcParams["font.family"] = name
            mpl.rcParams["axes.unicode_minus"] = False
            return
        except Exception:
            continue


def risk_cmap() -> LinearSegmentedColormap:
    return LinearSegmentedColormap.from_list(
        "risk",
        ["#f7fbff", "#dceaf4", "#f1c453", "#e56b2e", "#8f1d21"],
    )


def reduction_cmap() -> LinearSegmentedColormap:
    return LinearSegmentedColormap.from_list(
        "reduction",
        ["#f7f7f7", "#d6efe7", "#7ecdbb", "#1f8f78", "#0b5d4b"],
    )


def load_four_city_risk() -> gpd.GeoDataFrame:
    grid = gpd.read_file(TOOLS_DIR / "four_city_grid.geojson").to_crs(5179)
    risk = pd.read_csv(TOOLS_DIR / "four_city_risk_simple.csv")
    merged = grid.merge(risk, on="gid", how="left")
    if "gbn_x" in merged.columns:
        merged = merged.rename(columns={"gbn_x": "gbn"})
    if "gbn_y" in merged.columns:
        merged = merged.drop(columns=["gbn_y"])
    merged["risk_norm"] = merged["risk_norm"].fillna(0.0)
    return merged


def decode_gid_center(gid: str) -> tuple[float, float]:
    digits = "".join(ch for ch in str(gid) if ch.isdigit())
    x_idx = int(digits[:3])
    y_idx = int(digits[3:])
    return 900050 + x_idx * 100, 1900050 + y_idx * 100


def rebuild_gyosan_grid_scores() -> pd.DataFrame:
    grid = gpd.read_file(TOOLS_DIR / "gyosan_grid.geojson").to_crs(5179)
    risk_poly = gpd.read_file(TOOLS_DIR / "gyosan_direction_A_result.gpkg").to_crs(5179)

    overlay = gpd.overlay(
        grid[["gid", "geometry"]],
        risk_poly[["RiskScore_A", "RiskScore_A_norm", "geometry"]],
        how="intersection",
    )
    overlay["piece_area"] = overlay.geometry.area
    overlay["weighted_score"] = overlay["RiskScore_A"] * overlay["piece_area"]
    overlay["weighted_score_norm"] = overlay["RiskScore_A_norm"] * overlay["piece_area"]

    grouped = (
        overlay.groupby("gid", as_index=False)
        .agg(
            RiskScore_A_raw=("weighted_score", "sum"),
            RiskScore_A_norm_raw=("weighted_score_norm", "sum"),
            grid_area=("piece_area", "sum"),
            piece_count=("piece_area", "size"),
        )
        .assign(
            RiskScore_A_grid=lambda df: df["RiskScore_A_raw"] / df["grid_area"],
            RiskScore_A_norm_grid=lambda df: df["RiskScore_A_norm_raw"] / df["grid_area"],
        )
        .drop(columns=["RiskScore_A_raw", "RiskScore_A_norm_raw"])
    )

    grouped = grouped.sort_values(
        ["RiskScore_A_norm_grid", "gid"],
        ascending=[False, True],
    ).reset_index(drop=True)
    grouped["grid_rank"] = grouped.index + 1
    original_reduction = pd.read_csv(TOOLS_DIR / "gyosan_reduction.csv")
    top_n = len(original_reduction)
    grouped["is_top15"] = grouped["grid_rank"] <= top_n
    grouped["예상_감소량_상대"] = np.where(
        grouped["is_top15"],
        grouped["RiskScore_A_norm_grid"] * 0.10,
        0.0,
    )
    grouped["적용후_위험도"] = grouped["RiskScore_A_norm_grid"] - grouped["예상_감소량_상대"]

    return grouped


def save_gyosan_reduction_csv(grouped: pd.DataFrame) -> Path:
    OUT_DATA_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DATA_DIR / "gyosan_effect_reduction_by_gid.csv"
    out_cols = [
        "gid",
        "grid_rank",
        "RiskScore_A_grid",
        "RiskScore_A_norm_grid",
        "예상_감소량_상대",
        "적용후_위험도",
        "is_top15",
        "grid_area",
        "piece_count",
    ]
    grouped[out_cols].to_csv(out_path, index=False, encoding="utf-8-sig")
    return out_path


def load_region_extent(path: Path) -> tuple[float, float, float, float]:
    gdf = gpd.read_file(path).to_crs(5179)
    return tuple(gdf.total_bounds)


def expand_bounds(bounds: tuple[float, float, float, float], pad_ratio: float = 0.04) -> tuple[float, float, float, float]:
    minx, miny, maxx, maxy = bounds
    dx = maxx - minx
    dy = maxy - miny
    pad_x = dx * pad_ratio
    pad_y = dy * pad_ratio
    return (minx - pad_x, miny - pad_y, maxx + pad_x, maxy + pad_y)


def plot_region_panel(
    ax: plt.Axes,
    gdf: gpd.GeoDataFrame,
    bounds: tuple[float, float, float, float],
    title: str,
    band_colors: dict[str, str],
) -> None:
    minx, miny, maxx, maxy = bounds
    clipped = gdf.cx[minx:maxx, miny:maxy].copy()
    clipped.plot(ax=ax, color="#edf3f8", linewidth=0.0)
    clipped.boundary.plot(ax=ax, color="#d5dde6", linewidth=0.09, alpha=0.28)
    high = clipped[clipped["risk_band"].notna()].copy()
    for label, color in band_colors.items():
        part = high[high["risk_band"] == label]
        if part.empty:
            continue
        part.plot(
            ax=ax,
            color=color,
            linewidth=0.18,
            edgecolor=color,
        )
    ax.set_xlim(minx, maxx)
    ax.set_ylim(miny, maxy)
    ax.set_title(title, fontsize=14, fontweight="bold", pad=10)
    ax.set_axis_off()


def build_four_city_overview() -> Path:
    OUT_IMG_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_IMG_DIR / "four-city-risk-overview-ko.png"

    city = load_four_city_risk()
    q95 = city["risk_norm"].quantile(0.95)
    q98 = city["risk_norm"].quantile(0.98)
    q99 = city["risk_norm"].quantile(0.99)
    q995 = city["risk_norm"].quantile(0.995)
    band_colors = {
        "상위 5%": "#f6c65b",
        "상위 2%": "#f19a38",
        "상위 1%": "#d35a2d",
        "상위 0.5%": "#8f1d21",
    }

    city["risk_band"] = np.select(
        [
            city["risk_norm"] >= q995,
            city["risk_norm"] >= q99,
            city["risk_norm"] >= q98,
            city["risk_norm"] >= q95,
        ],
        ["상위 0.5%", "상위 1%", "상위 2%", "상위 5%"],
        default=None,
    )

    dongtan_bounds = expand_bounds(load_region_extent(TOOLS_DIR / "dongtan.gpkg"), 0.02)
    pangyo_bounds = expand_bounds(load_region_extent(TOOLS_DIR / "pangyo.gpkg"), 0.02)
    misa_bounds = expand_bounds(load_region_extent(TOOLS_DIR / "misa.gpkg"), 0.02)
    songpa = city[city["gbn"] == "서울특별시 송파구"].copy()
    songpa_bounds = expand_bounds(tuple(songpa.total_bounds), 0.03)

    fig, axes = plt.subplots(2, 2, figsize=(14, 12), dpi=220)
    fig.patch.set_facecolor("white")

    plot_region_panel(axes[0, 0], city, pangyo_bounds, "판교 100m 격자 위험도", band_colors)
    plot_region_panel(axes[0, 1], city, dongtan_bounds, "동탄 100m 격자 위험도", band_colors)
    plot_region_panel(axes[1, 0], city, songpa_bounds, "송파 100m 격자 위험도", band_colors)
    plot_region_panel(axes[1, 1], city, misa_bounds, "미사 100m 격자 위험도", band_colors)

    from matplotlib.patches import Patch
    legend_handles = [
        Patch(facecolor="#edf3f8", edgecolor="#d5dde6", label="기타 격자"),
        Patch(facecolor=band_colors["상위 5%"], edgecolor=band_colors["상위 5%"], label="상위 5%"),
        Patch(facecolor=band_colors["상위 2%"], edgecolor=band_colors["상위 2%"], label="상위 2%"),
        Patch(facecolor=band_colors["상위 1%"], edgecolor=band_colors["상위 1%"], label="상위 1%"),
        Patch(facecolor=band_colors["상위 0.5%"], edgecolor=band_colors["상위 0.5%"], label="상위 0.5%"),
    ]
    fig.legend(
        handles=legend_handles,
        loc="lower center",
        ncol=5,
        frameon=False,
        fontsize=10.5,
        bbox_to_anchor=(0.5, 0.06),
    )

    fig.suptitle("4개 시구 100m 격자 위험도 비교", fontsize=20, fontweight="bold", y=0.98)
    fig.text(
        0.5,
        0.03,
        "연속형 색 대신 전역 기준 상위 위험 격자만 강조했습니다. 화성 전체 대신 동탄 생활권 범위만 잘라서 비교했습니다.",
        ha="center",
        fontsize=11,
        color="#505050",
    )
    fig.tight_layout(rect=[0.02, 0.10, 0.98, 0.94])
    fig.savefig(out_path, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return out_path


def build_gyosan_before_after(grouped: pd.DataFrame) -> Path:
    OUT_IMG_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_IMG_DIR / "gyosan-before-after-ko.png"

    grid = gpd.read_file(TOOLS_DIR / "gyosan_grid.geojson").to_crs(5179)
    selected = gpd.read_file(TOOLS_DIR / "gyosan_selected.geojson").to_crs(5179)
    existing = pd.read_csv(TOOLS_DIR / "gyosan_existing_reflection_analysis.csv")

    grid = grid.merge(grouped, on="gid", how="left")
    top15 = grid[grid["is_top15"]].copy()

    before_cmap = risk_cmap()
    after_cmap = reduction_cmap()

    fig, axes = plt.subplots(1, 2, figsize=(15, 7.5), dpi=220)
    fig.patch.set_facecolor("white")

    grid.plot(
        ax=axes[0],
        column="RiskScore_A_norm_grid",
        cmap=before_cmap,
        linewidth=0.0,
        vmin=0.0,
        vmax=1.0,
    )
    if not top15.empty:
        top15.boundary.plot(ax=axes[0], color="#111827", linewidth=0.8, alpha=0.8)
    axes[0].set_title("적용 전: 교산 격자 위험도", fontsize=15, fontweight="bold", pad=10)
    axes[0].set_axis_off()

    grid.plot(
        ax=axes[1],
        column="적용후_위험도",
        cmap=after_cmap,
        linewidth=0.0,
        vmin=0.0,
        vmax=1.0,
    )
    if not top15.empty:
        top15.boundary.plot(ax=axes[1], color="#0f172a", linewidth=0.7, alpha=0.45)
    if not selected.empty:
        selected_cent = selected.geometry.centroid
        axes[1].scatter(
            selected_cent.x,
            selected_cent.y,
            s=26,
            marker="*",
            color="#111827",
            edgecolor="white",
            linewidth=0.4,
            zorder=5,
        )
    axes[1].set_title("적용 후: 예상 위험도 감소 반영", fontsize=15, fontweight="bold", pad=10)
    axes[1].set_axis_off()

    norm_left = mpl.colors.Normalize(vmin=0.0, vmax=1.0)
    sm_left = mpl.cm.ScalarMappable(norm=norm_left, cmap=before_cmap)
    cbar_left = fig.colorbar(
        sm_left,
        ax=axes[0],
        location="bottom",
        fraction=0.045,
        pad=0.04,
        aspect=32,
    )
    cbar_left.set_label("설치 전 정규화 위험도", fontsize=10)

    norm_right = mpl.colors.Normalize(vmin=0.0, vmax=1.0)
    sm_right = mpl.cm.ScalarMappable(norm=norm_right, cmap=after_cmap)
    cbar_right = fig.colorbar(
        sm_right,
        ax=axes[1],
        location="bottom",
        fraction=0.045,
        pad=0.04,
        aspect=32,
    )
    cbar_right.set_label("적용 후 정규화 위험도", fontsize=10)

    existing_row = existing.iloc[0].to_dict() if not existing.empty else {}
    total_pct = existing_row.get("coverage_total_pct")
    inc_pct = existing_row.get("coverage_increment_pct")
    weighted_total_pct = existing_row.get("weighted_total_pct")
    weighted_inc_pct = existing_row.get("weighted_increment_pct")

    summary = []
    if pd.notna(total_pct):
        summary.append(f"총 커버리지 {total_pct:.1f}%")
    if pd.notna(inc_pct):
        summary.append(f"신규 증가분 {inc_pct:.1f}%")
    if pd.notna(weighted_total_pct):
        summary.append(f"가중 커버리지 {weighted_total_pct:.1f}%")
    if pd.notna(weighted_inc_pct):
        summary.append(f"가중 증가분 {weighted_inc_pct:.1f}%")
    summary_text = " | ".join(summary)

    fig.suptitle("하남교산 적용 전·후 비교", fontsize=20, fontweight="bold", y=0.98)
    fig.text(
        0.5,
        0.045,
        "오른쪽은 상위 15% 격자에 10% 저감 시나리오를 반영한 예상 위험도이며, 별 표시는 최종 선정 20개 설치 지점입니다.",
        ha="center",
        fontsize=10.5,
        color="#404040",
    )
    if summary_text:
        fig.text(
            0.5,
            0.018,
            summary_text,
            ha="center",
            fontsize=10.5,
            color="#404040",
        )
    fig.tight_layout(rect=[0.02, 0.09, 0.98, 0.93])
    fig.savefig(out_path, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return out_path


def main() -> None:
    set_korean_font()
    OUT_IMG_DIR.mkdir(parents=True, exist_ok=True)
    OUT_DATA_DIR.mkdir(parents=True, exist_ok=True)

    grouped = rebuild_gyosan_grid_scores()
    csv_path = save_gyosan_reduction_csv(grouped)
    four_city_path = build_four_city_overview()
    gyosan_path = build_gyosan_before_after(grouped)

    print(f"saved: {csv_path}")
    print(f"saved: {four_city_path}")
    print(f"saved: {gyosan_path}")


if __name__ == "__main__":
    main()
