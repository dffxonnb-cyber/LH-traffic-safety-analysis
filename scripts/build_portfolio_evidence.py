#!/usr/bin/env python
"""Build public-safe portfolio evidence from the tracked Gyosan scenario CSV.

This script does not read private source data or regenerate model metrics. The
validation values shown in the SVGs are the documented public summary values.
"""

from __future__ import annotations

import csv
from html import escape
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_CSV = ROOT / "docs" / "data" / "gyosan_effect_reduction_by_gid.csv"
OUTPUT_CSV = ROOT / "docs" / "data" / "public_top20_priority.csv"
EVIDENCE_STATUS_CSV = ROOT / "docs" / "data" / "public_evidence_status.csv"
IMAGE_DIR = ROOT / "docs" / "images"


def svg_text(
    x: int,
    y: int,
    text: str,
    *,
    size: int = 26,
    weight: int = 500,
    fill: str = "#dce7e3",
    anchor: str = "start",
) -> str:
    return (
        f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{weight}" '
        f'fill="{fill}" text-anchor="{anchor}">{escape(text)}</text>'
    )


def svg_document(body: list[str], *, width: int = 1440, height: int = 900) -> str:
    return "\n".join(
        [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
            "<style>",
            "text { font-family: Pretendard, 'Noto Sans KR', Arial, sans-serif; }",
            ".mono { font-family: 'Cascadia Code', Consolas, monospace; }",
            "</style>",
            f'<rect width="{width}" height="{height}" rx="32" fill="#0d1416"/>',
            f'<rect x="24" y="24" width="{width - 48}" height="{height - 48}" rx="24" fill="#121c1f" stroke="#35515a" stroke-width="2"/>',
            *body,
            "</svg>",
        ]
    )


def metric_card(x: int, y: int, width: int, label: str, value: str, note: str) -> list[str]:
    return [
        f'<rect x="{x}" y="{y}" width="{width}" height="170" rx="18" fill="#172428" stroke="#3c5c64"/>',
        svg_text(x + 24, y + 38, label.upper(), size=18, weight=700, fill="#8db6ae"),
        svg_text(x + 24, y + 94, value, size=40, weight=800, fill="#f3d38a"),
        svg_text(x + 24, y + 132, note, size=18, fill="#b5c7c4"),
    ]


def build_performance_summary() -> None:
    body = [
        svg_text(72, 92, "LH TRAFFIC SAFETY · PUBLIC EVIDENCE", size=20, weight=800, fill="#8db6ae"),
        svg_text(72, 154, "100m 격자 교통사고 고위험 신호 분석", size=42, weight=800, fill="#f3f7f5"),
        svg_text(
            72,
            198,
            "기존 4개 시·구의 공간 패턴을 검증하고 하남교산 현장 검토 우선 후보로 전환",
            size=22,
            fill="#b5c7c4",
        ),
    ]
    cards = [
        (72, 258, 300, "Spatial unit", "100m × 100m", "시설 검토를 위한 세밀한 공간 단위"),
        (394, 258, 300, "Training scope", "99,323 grids", "4개 기존 시·구 학습 격자"),
        (716, 258, 300, "Target scope", "770 grids", "하남교산 대상 격자"),
        (1038, 258, 300, "Model", "Spatial RF", "공간 좌표 포함 Random Forest"),
        (72, 452, 405, "LORO mean AUC", "0.8604", "지역을 바꿔도 유지되는 위험 구분력"),
        (517, 452, 405, "Top-10% Lift", "4.39×", "상위 위험 후보군의 신호 집중도"),
        (962, 452, 376, "Worst holdout AUC", "0.7979", "가장 불리한 홀드아웃 결과"),
    ]
    for card in cards:
        body.extend(metric_card(*card))
    body.extend(
        [
            '<rect x="72" y="670" width="1266" height="118" rx="18" fill="#102025" stroke="#4c736d"/>',
            svg_text(96, 710, "INTERPRETATION", size=17, weight=800, fill="#8db6ae"),
            svg_text(
                96,
                750,
                "이 수치는 실제 사고 감소 효과가 아니라 현장 점검 후보를 우선순위화하는 의사결정 보조 신호입니다.",
                size=22,
                weight=650,
                fill="#e6efeb",
            ),
            svg_text(
                96,
                780,
                "검증 원본 재산출에는 비공개 공모전 데이터가 필요하며, 공개 저장소는 요약 지표와 안전한 산출물을 제공합니다.",
                size=17,
                fill="#a9bebb",
            ),
            svg_text(1338, 832, "Generated from public-safe repository evidence", size=15, fill="#718c89", anchor="end"),
        ]
    )
    (IMAGE_DIR / "portfolio-performance-summary.svg").write_text(
        svg_document(body), encoding="utf-8"
    )


def build_validation_summary() -> None:
    body = [
        svg_text(72, 92, "VALIDATION SUMMARY", size=20, weight=800, fill="#8db6ae"),
        svg_text(72, 154, "지역 전이 가능성을 먼저 검증", size=42, weight=800, fill="#f3f7f5"),
        svg_text(
            72,
            198,
            "랜덤 분할이 아니라 한 지역씩 제외하는 Leave-One-Region-Out 방식으로 위험 신호를 점검",
            size=22,
            fill="#b5c7c4",
        ),
    ]
    steps = [
        ("01", "한 지역 제외", "4개 기존 시·구 중 한 곳을 holdout"),
        ("02", "나머지 지역 학습", "공간 좌표 포함 Random Forest 위험 모델"),
        ("03", "holdout 평가", "AUC와 상위 10% Lift로 위험 신호 확인"),
        ("04", "후보 안정성 점검", "Monte Carlo Top-20 Jaccard 비교"),
    ]
    for index, (number, title, note) in enumerate(steps):
        x = 72 + index * 322
        body.extend(
            [
                f'<rect x="{x}" y="258" width="290" height="190" rx="18" fill="#172428" stroke="#3c5c64"/>',
                svg_text(x + 24, 300, number, size=18, weight=800, fill="#f3d38a"),
                svg_text(x + 24, 350, title, size=25, weight=750, fill="#eef4f1"),
                svg_text(x + 24, 388, note, size=16, fill="#b5c7c4"),
            ]
        )
    meanings = [
        ("Mean AUC 0.8604", "위험 격자와 비위험 격자를 전반적으로 구분하는 정도"),
        ("Top-10% Lift 4.39×", "상위 위험 후보군에 사고 발생 신호가 평균보다 집중된 정도"),
        ("Worst holdout AUC 0.7979", "가장 불리한 지역을 제외·검증했을 때의 구분력"),
        ("Mean Jaccard 0.503", "반복 실험에서 Top-20 후보군이 겹치는 안정성 참고값"),
    ]
    for index, (metric, meaning) in enumerate(meanings):
        y = 500 + index * 70
        body.extend(
            [
                f'<rect x="72" y="{y}" width="1266" height="54" rx="12" fill="#102025" stroke="#29444a"/>',
                svg_text(96, y + 35, metric, size=19, weight=750, fill="#f3d38a"),
                svg_text(390, y + 35, meaning, size=18, fill="#c2d2cf"),
            ]
        )
    body.extend(
        [
            svg_text(
                72,
                824,
                "주의: 검증 지표는 우선 검토 신호의 품질을 설명하며 실제 시설 설치 효과나 사고 예방의 인과효과를 증명하지 않습니다.",
                size=17,
                fill="#9db2ae",
            )
        ]
    )
    (IMAGE_DIR / "portfolio-validation-summary.svg").write_text(
        svg_document(body), encoding="utf-8"
    )


def build_score_comparison_note() -> None:
    body = [
        svg_text(72, 92, "SCORE COMPARISON · PUBLIC DIAGNOSTIC", size=20, weight=800, fill="#8db6ae"),
        svg_text(72, 154, "R²=0.006은 무엇을 뜻하는가", size=42, weight=800, fill="#f3f7f5"),
        svg_text(
            72,
            198,
            "두 정규화 점수 사이의 선형 설명력이 매우 낮다는 진단 결과",
            size=22,
            fill="#b5c7c4",
        ),
        *metric_card(72, 258, 390, "Compared score A", "Legacy GWRF", "공간 위험도 정규화 점수"),
        *metric_card(525, 258, 390, "Compared score B", "09번 점수", "시설 입지 선정 정규화 점수"),
        *metric_card(978, 258, 360, "Linear agreement", "R² = 0.006", "선형 설명력이 매우 낮음"),
        '<rect x="72" y="486" width="1266" height="240" rx="18" fill="#102025" stroke="#4c736d"/>',
        svg_text(96, 532, "해석 원칙", size=20, weight=800, fill="#8db6ae"),
        svg_text(96, 580, "1. R²는 순위상관 지표가 아니며, 두 점수의 순위 일치 여부를 직접 증명하지 않습니다.", size=20, fill="#e6efeb"),
        svg_text(96, 626, "2. 모델 실패가 아니라 서로 다른 위험 개념과 가중치를 반영할 가능성을 보여줍니다.", size=20, fill="#e6efeb"),
        svg_text(96, 672, "3. 두 점수는 별도 위험 신호로 비교하고 현장에서 확인해야 합니다.", size=20, fill="#e6efeb"),
        '<rect x="72" y="758" width="1266" height="72" rx="14" fill="#172428" stroke="#3c5c64"/>',
        svg_text(
            96,
            802,
            "공개 상태: 비교 이미지와 R² 요약은 공개 · 비교 원본 테이블과 재산출 데이터는 needs confirmation",
            size=18,
            fill="#b8cac6",
        ),
    ]
    (IMAGE_DIR / "portfolio-score-comparison-note.svg").write_text(
        svg_document(body), encoding="utf-8"
    )


def write_public_evidence_status() -> None:
    rows = [
        {
            "evidence": "LORO summary metrics",
            "status": "confirmed public summary",
            "public_scope": "mean AUC 0.8604; worst holdout AUC 0.7979; mean top-10% lift 4.39x",
            "limitation": "fold-level transfer_loro_detail.csv is not public",
        },
        {
            "evidence": "Monte Carlo candidate stability",
            "status": "confirmed public summary",
            "public_scope": "mean Jaccard 0.503",
            "limitation": "run-level gyosan_mc_runs.csv is not public",
        },
        {
            "evidence": "facility package and recommendation reason",
            "status": "needs confirmation",
            "public_scope": "generation logic only",
            "limitation": "final public-safe result file is not available",
        },
        {
            "evidence": "dashboard deployment URL",
            "status": "needs confirmation",
            "public_scope": "dashboard code and deployment guide only",
            "limitation": "no verifiable public deployment URL",
        },
        {
            "evidence": "score-system comparison",
            "status": "confirmed public diagnostic",
            "public_scope": "legacy GWRF normalized risk vs 09 normalized priority score; R2 0.006",
            "limitation": "underlying comparison table is not public",
        },
        {
            "evidence": "field inspection and accident reduction",
            "status": "not available",
            "public_scope": "none",
            "limitation": "Top-k is an inspection-priority proposal, not field-validated impact",
        },
    ]
    fieldnames = ["evidence", "status", "public_scope", "limitation"]
    with EVIDENCE_STATUS_CSV.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def load_top20() -> list[dict[str, str]]:
    with SOURCE_CSV.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    rows.sort(key=lambda row: int(row["grid_rank"]))
    return rows[:20]


def write_public_top20(rows: list[dict[str, str]]) -> None:
    fieldnames = [
        "rank",
        "grid_id",
        "normalized_risk_score",
        "public_evidence_scope",
        "facility_package_public_status",
        "recommendation_reason_public_status",
    ]
    with OUTPUT_CSV.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "rank": row["grid_rank"],
                    "grid_id": row["gid"],
                    "normalized_risk_score": f'{float(row["RiskScore_A_norm_grid"]):.4f}',
                    "public_evidence_scope": "tracked scenario CSV top-20",
                    "facility_package_public_status": "needs confirmation: non-public output",
                    "recommendation_reason_public_status": "needs confirmation: non-public output",
                }
            )


def build_top20_preview(rows: list[dict[str, str]]) -> None:
    body = [
        svg_text(72, 86, "PUBLIC TOP-20 PREVIEW", size=20, weight=800, fill="#8db6ae"),
        svg_text(72, 142, "하남교산 현장 검토 우선 후보", size=40, weight=800, fill="#f3f7f5"),
        svg_text(
            72,
            182,
            "공개 시나리오 CSV의 격자 순위와 정규화 위험도만 사용한 portfolio-safe 표",
            size=21,
            fill="#b5c7c4",
        ),
        '<rect x="72" y="226" width="1296" height="56" rx="12" fill="#203238"/>',
        svg_text(100, 260, "Rank", size=17, weight=750, fill="#8db6ae"),
        svg_text(230, 260, "Grid ID", size=17, weight=750, fill="#8db6ae"),
        svg_text(560, 260, "Normalized risk", size=17, weight=750, fill="#8db6ae"),
        svg_text(890, 260, "Public evidence status", size=17, weight=750, fill="#8db6ae"),
    ]
    for index, row in enumerate(rows):
        y = 298 + index * 43
        fill = "#172428" if index % 2 == 0 else "#142024"
        body.extend(
            [
                f'<rect x="72" y="{y}" width="1296" height="39" rx="6" fill="{fill}"/>',
                svg_text(106, y + 27, row["grid_rank"], size=17, weight=700, fill="#f3d38a"),
                svg_text(230, y + 27, row["gid"], size=17, weight=650, fill="#e7efec"),
                svg_text(560, y + 27, f'{float(row["RiskScore_A_norm_grid"]):.4f}', size=17, fill="#c2d2cf"),
                svg_text(890, y + 27, "scenario CSV에서 공개 확인", size=17, fill="#a9bebb"),
            ]
        )
    body.extend(
        [
            '<rect x="72" y="1182" width="1296" height="64" rx="12" fill="#102025" stroke="#4c736d"/>',
            svg_text(
                96,
                1222,
                "시설 패키지·추천 사유 원본은 공개 저장소에 없어 needs confirmation으로 유지합니다. 실제 현장 결정에는 별도 검증이 필요합니다.",
                size=17,
                fill="#b8cac6",
            ),
        ]
    )
    (IMAGE_DIR / "public-top20-priority-preview.svg").write_text(
        svg_document(body, height=1280), encoding="utf-8"
    )


def main() -> None:
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    rows = load_top20()
    write_public_top20(rows)
    build_performance_summary()
    build_validation_summary()
    build_score_comparison_note()
    build_top20_preview(rows)
    write_public_evidence_status()
    print(
        f"Wrote {OUTPUT_CSV.relative_to(ROOT)}, {EVIDENCE_STATUS_CSV.relative_to(ROOT)}, "
        "and 4 public-safe SVG evidence assets."
    )


if __name__ == "__main__":
    main()
