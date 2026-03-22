#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import annotations

from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


def _set_font() -> None:
    # Windows Korean font fallback.
    try:
        plt.rcParams["font.family"] = "Malgun Gothic"
    except Exception:
        pass
    plt.rcParams["axes.unicode_minus"] = False


def _load(out_dir: Path, name: str) -> pd.DataFrame:
    p = out_dir / name
    if not p.exists():
        raise FileNotFoundError(f"Missing required file: {p}")
    return pd.read_csv(p)


def fig01_transfer_by_region(detail: pd.DataFrame, out_dir: Path) -> None:
    d = detail.copy()
    d = d.sort_values("auc", ascending=False)

    fig, axes = plt.subplots(1, 2, figsize=(13, 5))

    axes[0].bar(d["holdout_region"], d["auc"], color="#2563eb")
    axes[0].set_title("LORO AUC by Holdout Region")
    axes[0].set_ylim(0.6, 1.0)
    axes[0].set_ylabel("AUC")
    axes[0].tick_params(axis="x", rotation=20)

    axes[1].bar(d["holdout_region"], d["top10_lift"], color="#f59e0b")
    axes[1].set_title("Top10 Lift by Holdout Region")
    axes[1].set_ylabel("Lift")
    axes[1].tick_params(axis="x", rotation=20)

    fig.tight_layout()
    fig.savefig(out_dir / "fig01_transfer_by_region.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


def fig02_feature_stability(feat: pd.DataFrame, out_dir: Path) -> None:
    d = feat.copy().sort_values("mean_importance", ascending=False)

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.bar(d["feature"], d["mean_importance"], yerr=d["std_importance"], color="#10b981", capsize=4)
    ax.set_title("Feature Stability: Mean Importance ± Std")
    ax.set_ylabel("Importance")
    ax.set_xlabel("Feature")

    for i, r in d.reset_index(drop=True).iterrows():
        ax.text(i, r["mean_importance"] + r["std_importance"] + 0.003, f"top3={r['top3_rate']:.2f}", ha="center", fontsize=8)

    fig.tight_layout()
    fig.savefig(out_dir / "fig02_feature_stability.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


def fig03_mc_robustness(mc: pd.DataFrame, out_dir: Path) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8))

    axes[0].hist(mc["jaccard_vs_current_top20"], bins=12, color="#7c3aed", edgecolor="white")
    axes[0].set_title("MC Robustness: Jaccard Distribution")
    axes[0].set_xlabel("Jaccard vs Current Top20")
    axes[0].set_ylabel("Count")

    axes[1].hist(mc["coverage_ratio"], bins=12, color="#ef4444", edgecolor="white")
    axes[1].set_title("MC Robustness: Coverage Distribution")
    axes[1].set_xlabel("Coverage Ratio")
    axes[1].set_ylabel("Count")

    fig.tight_layout()
    fig.savefig(out_dir / "fig03_mc_robustness.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


def fig04_scenario_tradeoff(sc: pd.DataFrame, out_dir: Path) -> None:
    d = sc.copy()

    fig, ax = plt.subplots(figsize=(7.5, 5.5))
    ax.scatter(d["jaccard_vs_current_top20"], d["coverage_ratio"], s=180, c=["#2563eb", "#10b981", "#f59e0b"])

    for _, r in d.iterrows():
        ax.annotate(r["scenario"], (r["jaccard_vs_current_top20"], r["coverage_ratio"]), textcoords="offset points", xytext=(7, 7))

    ax.set_title("Scenario Tradeoff: Consistency vs Coverage")
    ax.set_xlabel("Jaccard vs Current Top20")
    ax.set_ylabel("Coverage Ratio")
    ax.grid(alpha=0.3)

    fig.tight_layout()
    fig.savefig(out_dir / "fig04_scenario_tradeoff.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


def fig05_top20_confidence(bp: pd.DataFrame, conf_all: pd.DataFrame, out_dir: Path) -> None:
    tier_order = ["very_high", "high", "medium", "low"]
    tier_color = {
        "very_high": "#dc2626",
        "high": "#f59e0b",
        "medium": "#2563eb",
        "low": "#94a3b8",
    }

    c = conf_all.copy()
    c["selection_prob"] = pd.to_numeric(c["selection_prob"], errors="coerce").fillna(0.0)
    c["confidence_tier"] = c["confidence_tier"].astype(str)

    b = bp.copy()
    b["selection_prob"] = pd.to_numeric(b["selection_prob"], errors="coerce").fillna(0.0)
    b["confidence_tier"] = b["confidence_tier"].astype(str)

    # Top20 table의 확률이 0/1 한쪽으로 쏠릴 때는 전체 신뢰도 분포 기반으로 표현을 보강한다.
    uniq_prob = int(b["selection_prob"].nunique())
    positive_cnt = int((b["selection_prob"] > 0).sum())
    degenerate_top20 = uniq_prob <= 2 and positive_cnt <= 2

    fig, axes = plt.subplots(1, 2, figsize=(14, 5.8))

    tier_counts = c["confidence_tier"].value_counts().reindex(tier_order, fill_value=0)
    axes[0].bar(tier_counts.index, tier_counts.values, color=[tier_color[t] for t in tier_order])
    axes[0].set_title("Confidence Tier Distribution (All Candidate Cells)")
    axes[0].set_ylabel("Count")
    for i, v in enumerate(tier_counts.values):
        axes[0].text(i, v + max(1, int(max(tier_counts.values) * 0.01)), str(int(v)), ha="center", fontsize=9)

    if degenerate_top20:
        top = c.sort_values(["selection_prob", "confidence_rank"], ascending=[False, True]).head(10).copy()
        axes[1].set_title("Top10 Selection Probability (from full confidence table)")
    else:
        top = b.sort_values("selection_prob", ascending=False).head(10).copy()
        axes[1].set_title("Top10 Selection Probability (from Top20 blueprint)")

    colors = [tier_color.get(str(x), "#64748b") for x in top["confidence_tier"]]
    axes[1].barh(top["gid"].astype(str), top["selection_prob"], color=colors)
    axes[1].invert_yaxis()
    axes[1].set_xlim(0.0, 1.0)
    axes[1].set_xlabel("Selection Probability")
    axes[1].set_ylabel("GID")

    fig.tight_layout()
    fig.savefig(out_dir / "fig05_top20_confidence.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


def fig06_top20_package_mix(bp: pd.DataFrame, out_dir: Path) -> None:
    d = bp.copy()
    vc = d["recommended_package"].value_counts().sort_values(ascending=True)

    fig, ax = plt.subplots(figsize=(11, 5.5))
    ax.barh(vc.index.astype(str), vc.values, color="#0ea5e9")
    ax.set_title("Top20 Package Mix")
    ax.set_xlabel("Count")
    ax.set_ylabel("Recommended Package")

    fig.tight_layout()
    fig.savefig(out_dir / "fig06_top20_package_mix.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


def fig07_key_kpi(summary: pd.DataFrame, out_dir: Path) -> None:
    s = summary.set_index("metric")
    auc = float(s.loc["auc", "mean"]) if "auc" in s.index else np.nan
    lift = float(s.loc["top10_lift", "mean"]) if "top10_lift" in s.index else np.nan
    f1 = float(s.loc["f1", "mean"]) if "f1" in s.index else np.nan
    rec = float(s.loc["recall", "mean"]) if "recall" in s.index else np.nan

    fig, ax = plt.subplots(figsize=(10, 3.5))
    ax.axis("off")
    txt = (
        f"AUC (mean): {auc:.4f}\n"
        f"Top10 Lift (mean): {lift:.2f}x\n"
        f"F1 (mean): {f1:.4f}\n"
        f"Recall (mean): {rec:.4f}"
    )
    ax.text(0.03, 0.5, "Transfer Validation KPI", fontsize=18, fontweight="bold", va="center")
    ax.text(0.55, 0.5, txt, fontsize=14, va="center", bbox=dict(boxstyle="round,pad=0.5", fc="#f3f4f6", ec="#9ca3af"))

    fig.tight_layout()
    fig.savefig(out_dir / "fig07_transfer_kpi_card.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    _set_font()

    root = Path(__file__).resolve().parents[1]
    out = root / "data" / "통합_데이터" / "top35_outputs"
    fig_dir = out / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)

    transfer_detail = _load(out, "transfer_loro_detail.csv")
    transfer_summary = _load(out, "transfer_loro_summary.csv")
    feature_summary = _load(out, "feature_stability_summary.csv")
    mc_runs = _load(out, "gyosan_mc_runs.csv")
    scenario = _load(out, "gyosan_scenario_sensitivity.csv")
    blueprint = _load(out, "gyosan_top20_facility_blueprint.csv")
    confidence_all = _load(out, "gyosan_selection_confidence.csv")

    fig01_transfer_by_region(transfer_detail, fig_dir)
    fig02_feature_stability(feature_summary, fig_dir)
    fig03_mc_robustness(mc_runs, fig_dir)
    fig04_scenario_tradeoff(scenario, fig_dir)
    fig05_top20_confidence(blueprint, confidence_all, fig_dir)
    fig06_top20_package_mix(blueprint, fig_dir)
    fig07_key_kpi(transfer_summary, fig_dir)

    print("[DONE] PPT figures generated:")
    for p in sorted(fig_dir.glob("*.png")):
        print("-", p)


if __name__ == "__main__":
    main()
