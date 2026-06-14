#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PPT 슬라이드 3(분석 흐름)용 5단계 파이프라인 다이어그램 PNG를 생성합니다.

흐름: 공간 좌표 포함 RF → 위험지수(블렌딩) → 시나리오 → 4시구→교산 전이 → 배치·시설 패키지

출력: data/통합_데이터/시각화_공유/파이프라인_5단계.png
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def _set_korean_font():
    import matplotlib.pyplot as plt
    import matplotlib.font_manager as fm
    for name in ["Malgun Gothic", "맑은 고딕", "NanumGothic", "Nanum Gothic", "AppleGothic"]:
        if any(f.name == name for f in fm.fontManager.ttflist):
            plt.rcParams["font.family"] = name
            plt.rcParams["axes.unicode_minus"] = False
            return


def main() -> None:
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

    _set_korean_font()

    steps = [
        ("① 공간 RF", "4개 시구\n피처·좌표·중요도"),
        ("② 위험지수", "블렌딩 → 5그룹 가중치\nRisk_Base"),
        ("③ 시나리오", "상대 위험도×가정 감소율\n예상 변화"),
        ("④ 4시구→교산 전이", "검증·LORO\n설치 후보지"),
        ("⑤ 배치·시설 패키지", "취약축·우선순위\n맞춤 패키지"),
    ]

    n = len(steps)
    box_w, box_h = 1.35, 0.85
    gap = 0.28
    arrow_len = 0.22
    total_w = n * box_w + (n - 1) * (gap + arrow_len)
    total_h = box_h + 0.5
    fig, ax = plt.subplots(1, 1, figsize=(total_w * 1.1, total_h * 1.4))
    ax.set_xlim(-0.15, total_w + 0.15)
    ax.set_ylim(-0.1, total_h + 0.1)
    ax.set_aspect("equal")
    ax.set_axis_off()

    colors = ["#3b82f6", "#8b5cf6", "#06b6d4", "#f59e0b", "#10b981"]
    for i, (title, sub) in enumerate(steps):
        x = i * (box_w + gap + arrow_len) + 0.1
        y = (total_h - box_h) / 2
        box = FancyBboxPatch(
            (x, y), box_w, box_h,
            boxstyle="round,pad=0.02,rounding_size=0.08",
            facecolor=colors[i],
            edgecolor="#1e293b",
            linewidth=1.2,
            alpha=0.92,
        )
        ax.add_patch(box)
        ax.text(x + box_w / 2, y + box_h - 0.22, title, ha="center", va="center", fontsize=11, fontweight="bold", color="white")
        ax.text(x + box_w / 2, y + box_h / 2 - 0.15, sub, ha="center", va="center", fontsize=8, color="white", linespacing=1.25)

        if i < n - 1:
            ax_x = x + box_w + gap / 2
            ax_y = y + box_h / 2
            arrow = FancyArrowPatch(
                (ax_x, ax_y), (ax_x + arrow_len, ax_y),
                arrowstyle="->", mutation_scale=18, linewidth=2, color="#475569",
            )
            ax.add_patch(arrow)

    ax.set_title("공간 좌표 포함 RF → 위험지수 → 시나리오 → 교산 적용", fontsize=13, fontweight="bold", pad=12)
    plt.tight_layout()

    out_dir = ROOT / "data" / "통합_데이터" / "시각화_공유"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "파이프라인_5단계.png"
    plt.savefig(out_path, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close()
    print(f"저장: {out_path}")


if __name__ == "__main__":
    main()
