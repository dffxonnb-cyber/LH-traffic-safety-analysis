#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Top-3~5% upgrade pack for the final LH project.

Generated artifacts:
1) 4-region leave-one-region-out transfer validation
2) Feature-importance stability diagnostics
3) Hanam Gyosan coverage-based selection confidence and sensitivity
4) Top-20 facility blueprint and compact markdown report
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    brier_score_loss,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)


def _safe_div(a: float, b: float) -> float:
    return float(a / b) if b not in (0, 0.0) else float("nan")


def _minmax(x: np.ndarray) -> np.ndarray:
    xmin = float(np.nanmin(x))
    xmax = float(np.nanmax(x))
    if not np.isfinite(xmin) or not np.isfinite(xmax) or xmax <= xmin:
        return np.zeros_like(x, dtype=float)
    return (x - xmin) / (xmax - xmin)


def _binary_metrics(y_true: np.ndarray, y_prob: np.ndarray) -> dict[str, float]:
    y_true = np.asarray(y_true).astype(int)
    y_prob = np.asarray(y_prob).astype(float)

    y_pred = (y_prob >= 0.5).astype(int)
    uniq = np.unique(y_true)

    auc = float("nan")
    ap = float("nan")
    brier = float("nan")
    if len(uniq) > 1:
        auc = float(roc_auc_score(y_true, y_prob))
        ap = float(average_precision_score(y_true, y_prob))
        brier = float(brier_score_loss(y_true, y_prob))

    top_k = max(1, int(round(0.10 * len(y_prob))))
    top_idx = np.argpartition(y_prob, -top_k)[-top_k:]
    top10_pos_rate = float(np.mean(y_true[top_idx]))
    base_rate = float(np.mean(y_true))

    return {
        "auc": auc,
        "avg_precision": ap,
        "brier": brier,
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "f1": float(f1_score(y_true, y_pred, zero_division=0)),
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "base_positive_rate": base_rate,
        "top10_positive_rate": top10_pos_rate,
        "top10_lift": _safe_div(top10_pos_rate, base_rate),
    }


def discover_integrated_csv(data_dir: Path) -> Path:
    required = {"gid", "gbn", "acc_count", "AADT_mean", "velocity_mean", "FRIN_mean", "TI_mean"}
    candidates: list[Path] = []
    for p in data_dir.rglob("*.csv"):
        try:
            cols = set(pd.read_csv(p, nrows=0).columns)
        except Exception:
            continue
        if required.issubset(cols):
            candidates.append(p)
    if not candidates:
        raise FileNotFoundError("Could not find integrated 4-region CSV with required columns.")
    candidates = sorted(candidates, key=lambda x: x.stat().st_size, reverse=True)
    return candidates[0]


def discover_main_grid_geojson(data_dir: Path) -> Path:
    candidates: list[tuple[int, Path]] = []
    for p in data_dir.rglob("*.geojson"):
        try:
            g = gpd.read_file(p)
        except Exception:
            continue
        if "gid" not in g.columns:
            continue
        candidates.append((len(g), p))

    if not candidates:
        raise FileNotFoundError("Could not find geojson with gid for coordinate merge.")

    # 4-region grid should be the largest gid geojson.
    candidates.sort(key=lambda t: t[0], reverse=True)
    return candidates[0][1]


def discover_gyosan_grid_geojson(data_dir: Path) -> Path:
    candidates: list[tuple[int, Path]] = []
    for p in data_dir.rglob("*.geojson"):
        try:
            g = gpd.read_file(p, rows=5)
        except Exception:
            continue
        if "gid" not in g.columns:
            continue
        try:
            n_rows = len(gpd.read_file(p))
        except Exception:
            continue
        if 200 <= n_rows <= 5000:
            candidates.append((abs(n_rows - 770), p))

    if not candidates:
        raise FileNotFoundError("Could not find Gyosan grid geojson.")

    candidates.sort(key=lambda t: t[0])
    return candidates[0][1]


def load_model_frame(csv_path: Path, geo_path: Path) -> tuple[pd.DataFrame, list[str]]:
    use_cols = ["gid", "gbn", "acc_count", "AADT_mean", "velocity_mean", "FRIN_mean", "TI_mean"]
    df = pd.read_csv(csv_path, usecols=use_cols)

    geo = gpd.read_file(geo_path)
    if "gid" not in geo.columns:
        raise ValueError(f"Geo file has no gid column: {geo_path}")
    geo = geo[["gid", "geometry"]].copy()

    if geo.crs is not None:
        try:
            geo = geo.to_crs(epsg=5179)
        except Exception:
            pass

    cent = geo.geometry.centroid
    geo["x_coord"] = cent.x.to_numpy()
    geo["y_coord"] = cent.y.to_numpy()

    m = df.merge(geo[["gid", "x_coord", "y_coord"]], on="gid", how="left")

    for c in ["acc_count", "AADT_mean", "velocity_mean", "FRIN_mean", "TI_mean", "x_coord", "y_coord"]:
        m[c] = pd.to_numeric(m[c], errors="coerce")
    for c in ["AADT_mean", "velocity_mean", "FRIN_mean", "TI_mean", "x_coord", "y_coord"]:
        if m[c].isna().any():
            m[c] = m[c].fillna(float(m[c].median()))
    m["acc_count"] = m["acc_count"].fillna(0.0)

    m["y_bin"] = (np.clip(m["acc_count"].to_numpy(float), 0, None) > 0).astype(int)
    feat_cols = ["AADT_mean", "velocity_mean", "FRIN_mean", "TI_mean", "x_coord", "y_coord"]

    return m, feat_cols


def run_loro_transfer(df: pd.DataFrame, feat_cols: list[str], seed: int = 42) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows: list[dict[str, float | str | int]] = []
    regions = sorted(df["gbn"].dropna().unique().tolist())

    for rg in regions:
        tr = df[df["gbn"] != rg].copy()
        te = df[df["gbn"] == rg].copy()

        Xtr = tr[feat_cols].to_numpy(float)
        ytr = tr["y_bin"].to_numpy(int)
        Xte = te[feat_cols].to_numpy(float)
        yte = te["y_bin"].to_numpy(int)

        clf = RandomForestClassifier(
            n_estimators=220,
            max_depth=16,
            min_samples_leaf=5,
            n_jobs=-1,
            class_weight="balanced_subsample",
            random_state=seed,
        )
        clf.fit(Xtr, ytr)
        pte = clf.predict_proba(Xte)[:, 1]

        met = _binary_metrics(yte, pte)
        met.update(
            {
                "holdout_region": rg,
                "n_train": int(len(tr)),
                "n_test": int(len(te)),
                "n_test_positive": int(yte.sum()),
                "oob": float("nan"),
            }
        )

        imps = clf.feature_importances_
        for f, imp in zip(feat_cols, imps):
            met[f"imp_{f}"] = float(imp)
        rows.append(met)

    detail_df = pd.DataFrame(rows)

    summary_cols = [
        "auc",
        "avg_precision",
        "brier",
        "accuracy",
        "f1",
        "precision",
        "recall",
        "base_positive_rate",
        "top10_positive_rate",
        "top10_lift",
    ]
    s_rows = []
    for col in summary_cols:
        s_rows.append(
            {
                "metric": col,
                "mean": float(detail_df[col].mean()),
                "std": float(detail_df[col].std(ddof=0)),
                "min": float(detail_df[col].min()),
                "max": float(detail_df[col].max()),
            }
        )
    summary_df = pd.DataFrame(s_rows)
    return detail_df, summary_df


def run_feature_stability(
    df: pd.DataFrame,
    feat_cols: list[str],
    n_runs: int = 16,
    sample_ratio: float = 0.75,
    seed: int = 42,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    rng = np.random.default_rng(seed)
    n = len(df)
    m = max(1000, int(round(sample_ratio * n)))

    records: list[dict[str, float | int | str]] = []

    for run_id in range(1, n_runs + 1):
        idx = rng.choice(n, size=m, replace=True)
        part = df.iloc[idx]

        X = part[feat_cols].to_numpy(float)
        y = part["y_bin"].to_numpy(int)

        clf = RandomForestClassifier(
            n_estimators=140,
            max_depth=14,
            min_samples_leaf=5,
            n_jobs=-1,
            class_weight="balanced_subsample",
            random_state=1000 + run_id,
        )
        clf.fit(X, y)
        imp = clf.feature_importances_

        order = np.argsort(imp)[::-1]
        rank = np.empty_like(order)
        rank[order] = np.arange(1, len(imp) + 1)

        for j, f in enumerate(feat_cols):
            records.append(
                {
                    "run_id": run_id,
                    "feature": f,
                    "importance": float(imp[j]),
                    "rank": int(rank[j]),
                }
            )

    runs_df = pd.DataFrame(records)

    grp = runs_df.groupby("feature", as_index=False)
    summary_df = grp.agg(
        mean_importance=("importance", "mean"),
        std_importance=("importance", "std"),
        min_importance=("importance", "min"),
        max_importance=("importance", "max"),
        mean_rank=("rank", "mean"),
        median_rank=("rank", "median"),
        p25_rank=("rank", lambda s: float(np.percentile(s, 25))),
        p75_rank=("rank", lambda s: float(np.percentile(s, 75))),
        top3_rate=("rank", lambda s: float(np.mean(np.asarray(s) <= 3))),
    )
    summary_df["importance_cv"] = summary_df["std_importance"] / summary_df["mean_importance"].replace(0, np.nan)
    summary_df = summary_df.sort_values(["mean_importance", "top3_rate"], ascending=[False, False]).reset_index(drop=True)

    return runs_df, summary_df


def discover_priority_csv(data_dir: Path) -> Path:
    candidates: list[tuple[int, Path]] = []
    for p in data_dir.rglob("*.csv"):
        try:
            df = pd.read_csv(p)
        except Exception:
            continue

        cols = list(df.columns)
        if len(cols) != 13:
            continue
        if cols[0] != "gid":
            continue
        if len(df) < 200 or len(df) > 5000:
            continue
        first_col = df.iloc[:, 0].astype(str)
        if float((first_col.str.startswith("다사")).mean()) < 0.6:
            continue

        candidates.append((len(df), p))

    if not candidates:
        raise FileNotFoundError("Could not locate Hanam Gyosan priority grid CSV.")

    candidates.sort(key=lambda t: t[0], reverse=True)
    return candidates[0][1]


def discover_reference_top20_csv(data_dir: Path) -> Path | None:
    # Prefer the basic safety-site top20 for robustness comparison.
    preferred_name = "hanam_gyosan_safety_site_selected_k20.csv"
    for p in data_dir.rglob("*.csv"):
        if p.name.lower() == preferred_name:
            return p

    cands: list[tuple[int, Path]] = []
    need = {"gid", "selected_order"}
    for p in data_dir.rglob("*.csv"):
        try:
            df = pd.read_csv(p)
        except Exception:
            continue
        cols = set(df.columns)
        if not need.issubset(cols):
            continue
        if len(df) < 10 or len(df) > 60:
            continue
        cands.append((len(df.columns), p))

    if not cands:
        return None
    cands.sort(key=lambda x: x[0], reverse=True)
    return cands[0][1]


def discover_blueprint_top20_csv(data_dir: Path) -> Path | None:
    # Prefer the richer table with facility split labels.
    cands: list[tuple[int, int, Path]] = []
    need = {"gid", "selected_order"}
    for p in data_dir.rglob("*.csv"):
        try:
            df = pd.read_csv(p)
        except Exception:
            continue
        cols = set(df.columns)
        if not need.issubset(cols):
            continue
        if len(df) < 10 or len(df) > 60:
            continue
        has_facility = int("facility" in cols)
        cands.append((has_facility, len(df.columns), p))

    if not cands:
        return None
    cands.sort(key=lambda x: (x[0], x[1]), reverse=True)
    return cands[0][2]


def load_gyosan_priority_with_coords(priority_csv: Path, gyosan_geo: Path) -> pd.DataFrame:
    p = pd.read_csv(priority_csv)
    gid_col = p.columns[0]

    g = gpd.read_file(gyosan_geo)
    if gid_col not in g.columns and "gid" in g.columns:
        g = g.rename(columns={"gid": gid_col})
    if gid_col not in g.columns:
        raise ValueError("Gyosan geojson has no compatible gid column.")

    g = g[[gid_col, "geometry"]].copy()
    if g.crs is not None:
        try:
            g = g.to_crs(epsg=5179)
        except Exception:
            pass

    cent = g.geometry.centroid
    g["x_coord"] = cent.x.to_numpy()
    g["y_coord"] = cent.y.to_numpy()

    m = p.merge(g[[gid_col, "x_coord", "y_coord"]], on=gid_col, how="left")
    for c in ["x_coord", "y_coord"]:
        m[c] = pd.to_numeric(m[c], errors="coerce")
        if m[c].isna().any():
            m[c] = m[c].fillna(float(m[c].median()))
    return m


def build_cover_matrix(coords: np.ndarray, radius_m: float) -> np.ndarray:
    x = coords[:, 0]
    y = coords[:, 1]
    dx = x[:, None] - x[None, :]
    dy = y[:, None] - y[None, :]
    d2 = dx * dx + dy * dy
    return d2 <= float(radius_m * radius_m)


def greedy_cover_selection(cover: np.ndarray, demand: np.ndarray, k: int) -> tuple[np.ndarray, float]:
    n = len(demand)
    selected = np.zeros(n, dtype=bool)
    covered = np.zeros(n, dtype=bool)
    chosen: list[int] = []

    for _ in range(min(k, n)):
        uncovered_weight = demand * (~covered)
        gains = cover.astype(float) @ uncovered_weight
        gains[selected] = -1.0

        best = int(np.argmax(gains))
        best_gain = float(gains[best])

        if best_gain <= 1e-12:
            rem = np.where(~selected)[0]
            if len(rem) == 0:
                break
            best = int(rem[np.argmax(demand[rem])])

        chosen.append(best)
        selected[best] = True
        covered = covered | cover[best]

    coverage_ratio = _safe_div(float(demand[covered].sum()), float(demand.sum() + 1e-12))
    return np.asarray(chosen, dtype=int), coverage_ratio


def _recommend_package(row: pd.Series, ratio_cols: list[str], high_col: str) -> tuple[str, str]:
    dom = row["dominant_zone"]
    high = float(row[high_col])

    road, residential, commercial, school, green = ratio_cols

    if dom == road:
        if high >= 1:
            return (
                "Traffic calming + Smart crossing + CCTV",
                "Road-dominant and matched to historical high-risk pattern",
            )
        return ("Traffic calming + LED warning sign", "Road-dominant hotspot")

    if dom == school:
        return (
            "School-zone signal + Guardrail + CCTV",
            "School-related zone requires crossing protection",
        )

    if dom == residential:
        return (
            "CCTV + Emergency bell + Streetlight",
            "Residential surveillance and personal safety demand",
        )

    if dom == commercial:
        return (
            "CCTV + Dynamic warning sign + Marking",
            "Commercial crossing complexity",
        )

    if dom == green:
        return (
            "Streetlight + Emergency bell + Patrol beacon",
            "Green/open zone visibility and emergency response",
        )

    return ("CCTV + Basic safety marking", "General-purpose baseline package")


def run_gyosan_confidence(
    priority_df: pd.DataFrame,
    reference_df: pd.DataFrame | None,
    blueprint_df: pd.DataFrame | None,
    k: int = 20,
    n_runs: int = 200,
    radius_m: float = 250.0,
    seed: int = 42,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    p = priority_df.copy()
    cols = list(p.columns)

    gid_col = cols[0]
    high_col = cols[3]
    ratio_cols = cols[4:9]
    score_col = cols[10]
    flow_col = cols[12]

    for c in [high_col] + ratio_cols + [score_col, flow_col, "x_coord", "y_coord"]:
        p[c] = pd.to_numeric(p[c], errors="coerce").fillna(0.0)

    risk_n = _minmax(p[score_col].to_numpy(float))
    flow_n = _minmax(p[flow_col].to_numpy(float))
    high_v = p[high_col].to_numpy(float)

    coords = p[["x_coord", "y_coord"]].to_numpy(float)
    cover = build_cover_matrix(coords, radius_m=radius_m)

    current_set: set[str] = set()
    if reference_df is not None and gid_col in reference_df.columns:
        current_set = set(reference_df[gid_col].astype(str).tolist())

    rng = np.random.default_rng(seed)
    hit = np.zeros(len(p), dtype=int)
    run_rows: list[dict[str, float | int]] = []

    for run_id in range(1, n_runs + 1):
        w_risk = float(rng.uniform(0.55, 0.9))
        w_flow = float(1.0 - w_risk)
        w_high = float(rng.uniform(0.05, 0.25))

        demand = w_risk * risk_n + w_flow * flow_n + w_high * high_v
        sel_idx, cov_ratio = greedy_cover_selection(cover, demand, k)
        hit[sel_idx] += 1

        top_gid = set(p.iloc[sel_idx][gid_col].astype(str).tolist())
        jac = float("nan")
        if current_set:
            jac = _safe_div(len(top_gid & current_set), len(top_gid | current_set))

        run_rows.append(
            {
                "run_id": run_id,
                "w_risk": w_risk,
                "w_flow": w_flow,
                "w_high": w_high,
                "coverage_ratio": cov_ratio,
                "jaccard_vs_current_top20": jac,
            }
        )

    conf = p[[gid_col, score_col, flow_col, high_col] + ratio_cols + ["x_coord", "y_coord"]].copy()
    conf["selection_prob"] = hit / float(n_runs)
    conf["is_in_current_top20"] = conf[gid_col].astype(str).isin(current_set)
    conf["confidence_rank"] = conf["selection_prob"].rank(ascending=False, method="first").astype(int)
    conf["confidence_tier"] = pd.cut(
        conf["selection_prob"],
        bins=[-0.001, 0.20, 0.50, 0.80, 1.01],
        labels=["low", "medium", "high", "very_high"],
    ).astype(str)
    conf["dominant_zone"] = conf[ratio_cols].idxmax(axis=1)

    sens_runs_df = pd.DataFrame(run_rows)

    scenario_rows = []
    scenarios = [
        ("risk60_flow40", 0.60, 0.40, 0.10),
        ("risk70_flow30", 0.70, 0.30, 0.15),
        ("risk80_flow20", 0.80, 0.20, 0.20),
    ]
    for key, wr, wf, wh in scenarios:
        demand = wr * risk_n + wf * flow_n + wh * high_v
        sel_idx, cov_ratio = greedy_cover_selection(cover, demand, k)
        top_gid = set(p.iloc[sel_idx][gid_col].astype(str).tolist())
        jac = float("nan")
        if current_set:
            jac = _safe_div(len(top_gid & current_set), len(top_gid | current_set))

        scenario_rows.append(
            {
                "scenario": key,
                "w_risk": wr,
                "w_flow": wf,
                "w_high": wh,
                "radius_m": radius_m,
                "selected_count": int(k),
                "coverage_ratio": cov_ratio,
                "mean_priority_score_raw": float(np.mean(p.iloc[sel_idx][score_col].to_numpy(float))),
                "mean_flow_raw": float(np.mean(p.iloc[sel_idx][flow_col].to_numpy(float))),
                "highrisk_share": float(np.mean(p.iloc[sel_idx][high_col].to_numpy(float))),
                "jaccard_vs_current_top20": jac,
            }
        )

    scenario_df = pd.DataFrame(scenario_rows)

    if blueprint_df is not None and gid_col in blueprint_df.columns:
        top20 = blueprint_df.copy()
    elif reference_df is not None and gid_col in reference_df.columns:
        top20 = reference_df.copy()
    else:
        top20 = conf.sort_values("selection_prob", ascending=False).head(k).copy()

    keep_cols = [gid_col]
    for c in ["selected_order", "facility"]:
        if c in top20.columns:
            keep_cols.append(c)
    top20 = top20[keep_cols].copy()

    blueprint = top20.merge(
        conf[[gid_col, score_col, flow_col, high_col, "selection_prob", "confidence_tier", "dominant_zone"] + ratio_cols],
        on=gid_col,
        how="left",
    )

    packs = blueprint.apply(lambda r: _recommend_package(r, ratio_cols, high_col), axis=1)
    blueprint["recommended_package"] = [z[0] for z in packs]
    blueprint["recommendation_reason"] = [z[1] for z in packs]
    blueprint = blueprint.sort_values(["selection_prob", score_col], ascending=[False, False]).reset_index(drop=True)

    return conf, sens_runs_df, scenario_df, blueprint


def render_report(
    out_md: Path,
    csv_train: Path,
    geo_train: Path,
    priority_csv: Path,
    reference_csv: Path | None,
    blueprint_csv: Path | None,
    transfer_summary: pd.DataFrame,
    transfer_detail: pd.DataFrame,
    feat_summary: pd.DataFrame,
    scenario_df: pd.DataFrame,
    mc_runs_df: pd.DataFrame,
    blueprint: pd.DataFrame,
) -> None:
    m_auc = float(transfer_summary.loc[transfer_summary["metric"] == "auc", "mean"].iloc[0])
    m_lift = float(transfer_summary.loc[transfer_summary["metric"] == "top10_lift", "mean"].iloc[0])

    worst = transfer_detail.sort_values("auc", ascending=True).head(1)
    worst_rg = str(worst["holdout_region"].iloc[0])
    worst_auc = float(worst["auc"].iloc[0])

    top_feat = feat_summary.head(3)[["feature", "mean_importance", "top3_rate"]].copy()

    cur = blueprint.copy()
    vhigh_rate = float(np.mean(cur["confidence_tier"].astype(str) == "very_high")) if len(cur) else float("nan")
    mean_jaccard = float(mc_runs_df["jaccard_vs_current_top20"].mean()) if len(mc_runs_df) else float("nan")

    lines: list[str] = []
    lines.append("# TOP35 Upgrade Report")
    lines.append("")
    lines.append("## 1) Input Discovery")
    lines.append(f"- 4-region integrated CSV: `{csv_train.as_posix()}`")
    lines.append(f"- 4-region grid geojson: `{geo_train.as_posix()}`")
    lines.append(f"- Gyosan priority CSV: `{priority_csv.as_posix()}`")
    lines.append(
        f"- Robustness reference top20 CSV: `{reference_csv.as_posix() if reference_csv else 'not found (fallback used)'}`"
    )
    lines.append(
        f"- Blueprint source top20 CSV: `{blueprint_csv.as_posix() if blueprint_csv else 'not found (fallback used)'}`"
    )
    lines.append("")
    lines.append("## 2) Transfer Validation (Leave-One-Region-Out)")
    lines.append(f"- Mean AUC across holdout regions: **{m_auc:.4f}**")
    lines.append(f"- Mean top-10% lift: **{m_lift:.2f}x**")
    lines.append(f"- Worst holdout region: **{worst_rg}** (AUC={worst_auc:.4f})")
    lines.append("")
    lines.append("## 3) Feature Stability")
    lines.append("Top stable drivers (high mean importance and high top3_rate):")
    for _, r in top_feat.iterrows():
        lines.append(
            f"- {r['feature']}: mean_importance={float(r['mean_importance']):.4f}, top3_rate={float(r['top3_rate']):.2f}"
        )
    lines.append("")
    lines.append("## 4) Gyosan Selection Robustness (Coverage-Based)")
    if len(scenario_df):
        best_j = scenario_df.sort_values("jaccard_vs_current_top20", ascending=False).iloc[0]
        lines.append(
            "- Best deterministic sensitivity scenario: "
            f"**{best_j['scenario']}** (Jaccard={float(best_j['jaccard_vs_current_top20']):.3f}, coverage={float(best_j['coverage_ratio']):.3f})"
        )
    lines.append(
        f"- Monte Carlo mean Jaccard vs current top20: **{mean_jaccard:.3f}**"
        if np.isfinite(mean_jaccard)
        else "- Monte Carlo mean Jaccard could not be computed"
    )
    lines.append(
        f"- Share of current top20 in `very_high` confidence tier: **{vhigh_rate * 100:.1f}%**"
        if np.isfinite(vhigh_rate)
        else "- Confidence tier share could not be computed"
    )
    lines.append("")
    lines.append("## 5) Actionable Top20 Blueprint")
    lines.append("- `recommended_package` and `recommendation_reason` columns are ready for slides.")
    lines.append("- Use this table for Q&A when asked: why this facility at this location?")
    lines.append("")
    lines.append("## 6) Suggested Slide Tie-in")
    lines.append("- Validation slide: transfer_loro_detail + transfer_loro_summary")
    lines.append("- Robustness slide: gyosan_mc_runs + gyosan_scenario_sensitivity")
    lines.append("- Execution slide: gyosan_top20_facility_blueprint")

    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--k", type=int, default=20)
    parser.add_argument("--bootstrap-runs", type=int, default=16)
    parser.add_argument("--mc-runs", type=int, default=200)
    parser.add_argument("--radius-m", type=float, default=250.0)
    args = parser.parse_args()

    root = Path(args.project_root).resolve()
    data_dir = root / "data"
    out_dir = data_dir / "통합_데이터" / "top35_outputs"
    docs_dir = root / "docs"
    out_dir.mkdir(parents=True, exist_ok=True)

    csv_train = discover_integrated_csv(data_dir)
    geo_train = discover_main_grid_geojson(data_dir)

    model_df, feat_cols = load_model_frame(csv_train, geo_train)
    transfer_detail, transfer_summary = run_loro_transfer(model_df, feat_cols)
    feat_runs, feat_summary = run_feature_stability(model_df, feat_cols, n_runs=args.bootstrap_runs)

    priority_csv = discover_priority_csv(data_dir)
    gyosan_geo = discover_gyosan_grid_geojson(data_dir)
    priority_df = load_gyosan_priority_with_coords(priority_csv, gyosan_geo)

    reference_csv = discover_reference_top20_csv(data_dir)
    reference_df = pd.read_csv(reference_csv) if reference_csv is not None else None
    blueprint_csv = discover_blueprint_top20_csv(data_dir)
    blueprint_df = pd.read_csv(blueprint_csv) if blueprint_csv is not None else None

    gy_conf, gy_mc_runs, gy_scen, gy_blueprint = run_gyosan_confidence(
        priority_df=priority_df,
        reference_df=reference_df,
        blueprint_df=blueprint_df,
        k=args.k,
        n_runs=args.mc_runs,
        radius_m=args.radius_m,
    )

    paths = {
        "transfer_loro_detail": out_dir / "transfer_loro_detail.csv",
        "transfer_loro_summary": out_dir / "transfer_loro_summary.csv",
        "feature_stability_runs": out_dir / "feature_stability_runs.csv",
        "feature_stability_summary": out_dir / "feature_stability_summary.csv",
        "gyosan_confidence": out_dir / "gyosan_selection_confidence.csv",
        "gyosan_mc_runs": out_dir / "gyosan_mc_runs.csv",
        "gyosan_scenario_sensitivity": out_dir / "gyosan_scenario_sensitivity.csv",
        "gyosan_top20_facility_blueprint": out_dir / "gyosan_top20_facility_blueprint.csv",
        "report_md": docs_dir / "TOP35_UPGRADE_REPORT.md",
        "manifest_json": out_dir / "top35_manifest.json",
    }

    transfer_detail.to_csv(paths["transfer_loro_detail"], index=False, encoding="utf-8-sig")
    transfer_summary.to_csv(paths["transfer_loro_summary"], index=False, encoding="utf-8-sig")
    feat_runs.to_csv(paths["feature_stability_runs"], index=False, encoding="utf-8-sig")
    feat_summary.to_csv(paths["feature_stability_summary"], index=False, encoding="utf-8-sig")
    gy_conf.to_csv(paths["gyosan_confidence"], index=False, encoding="utf-8-sig")
    gy_mc_runs.to_csv(paths["gyosan_mc_runs"], index=False, encoding="utf-8-sig")
    gy_scen.to_csv(paths["gyosan_scenario_sensitivity"], index=False, encoding="utf-8-sig")
    gy_blueprint.to_csv(paths["gyosan_top20_facility_blueprint"], index=False, encoding="utf-8-sig")

    render_report(
        out_md=paths["report_md"],
        csv_train=csv_train,
        geo_train=geo_train,
        priority_csv=priority_csv,
        reference_csv=reference_csv,
        blueprint_csv=blueprint_csv,
        transfer_summary=transfer_summary,
        transfer_detail=transfer_detail,
        feat_summary=feat_summary,
        scenario_df=gy_scen,
        mc_runs_df=gy_mc_runs,
        blueprint=gy_blueprint,
    )

    manifest = {
        "project_root": str(root),
        "inputs": {
            "integrated_csv": str(csv_train),
            "main_grid_geojson": str(geo_train),
            "gyosan_grid_geojson": str(gyosan_geo),
            "priority_csv": str(priority_csv),
            "reference_top20_csv": str(reference_csv) if reference_csv is not None else None,
            "blueprint_top20_csv": str(blueprint_csv) if blueprint_csv is not None else None,
        },
        "outputs": {k: str(v) for k, v in paths.items()},
        "config": {
            "k": args.k,
            "bootstrap_runs": args.bootstrap_runs,
            "mc_runs": args.mc_runs,
            "radius_m": args.radius_m,
        },
    }
    paths["manifest_json"].write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    print("[DONE] Top35 upgrade pack generated.")
    for k, v in paths.items():
        print(f"- {k}: {v}")


def run_full_pipeline(
    project_root: str | Path | None = None,
    k: int = 20,
    bootstrap_runs: int = 16,
    mc_runs: int = 200,
    radius_m: float = 250.0,
    seed: int = 42,
    save: bool = True,
) -> dict[str, pd.DataFrame | Path | None]:
    """
    Run the full TOP35 pipeline (LORO, feature stability, Gyosan MC/scenario/blueprint).
    Suitable for use as a module from a notebook.

    Returns:
        dict with keys: transfer_detail, transfer_summary, feature_stability_runs,
        feature_stability_summary, gyosan_confidence, gyosan_mc_runs,
        gyosan_scenario_sensitivity, gyosan_top20_facility_blueprint,
        model_df, feat_cols, paths (dict of output paths), project_root
    """
    root = Path(project_root or Path(__file__).resolve().parents[1]).resolve()
    data_dir = root / "data"
    out_dir = data_dir / "통합_데이터" / "top35_outputs"
    docs_dir = root / "docs"
    out_dir.mkdir(parents=True, exist_ok=True)

    csv_train = discover_integrated_csv(data_dir)
    geo_train = discover_main_grid_geojson(data_dir)
    model_df, feat_cols = load_model_frame(csv_train, geo_train)

    transfer_detail, transfer_summary = run_loro_transfer(model_df, feat_cols, seed=seed)
    feat_runs, feat_summary = run_feature_stability(
        model_df, feat_cols, n_runs=bootstrap_runs, seed=seed
    )

    priority_csv = discover_priority_csv(data_dir)
    gyosan_geo = discover_gyosan_grid_geojson(data_dir)
    priority_df = load_gyosan_priority_with_coords(priority_csv, gyosan_geo)

    reference_csv = discover_reference_top20_csv(data_dir)
    reference_df = pd.read_csv(reference_csv) if reference_csv is not None else None
    blueprint_csv = discover_blueprint_top20_csv(data_dir)
    blueprint_df = pd.read_csv(blueprint_csv) if blueprint_csv is not None else None

    gy_conf, gy_mc_runs, gy_scen, gy_blueprint = run_gyosan_confidence(
        priority_df=priority_df,
        reference_df=reference_df,
        blueprint_df=blueprint_df,
        k=k,
        n_runs=mc_runs,
        radius_m=radius_m,
        seed=seed,
    )

    paths: dict[str, Path] = {}
    if save:
        paths = {
            "transfer_loro_detail": out_dir / "transfer_loro_detail.csv",
            "transfer_loro_summary": out_dir / "transfer_loro_summary.csv",
            "feature_stability_runs": out_dir / "feature_stability_runs.csv",
            "feature_stability_summary": out_dir / "feature_stability_summary.csv",
            "gyosan_confidence": out_dir / "gyosan_selection_confidence.csv",
            "gyosan_mc_runs": out_dir / "gyosan_mc_runs.csv",
            "gyosan_scenario_sensitivity": out_dir / "gyosan_scenario_sensitivity.csv",
            "gyosan_top20_facility_blueprint": out_dir / "gyosan_top20_facility_blueprint.csv",
            "manifest_json": out_dir / "top35_manifest.json",
        }
        transfer_detail.to_csv(paths["transfer_loro_detail"], index=False, encoding="utf-8-sig")
        transfer_summary.to_csv(paths["transfer_loro_summary"], index=False, encoding="utf-8-sig")
        feat_runs.to_csv(paths["feature_stability_runs"], index=False, encoding="utf-8-sig")
        feat_summary.to_csv(paths["feature_stability_summary"], index=False, encoding="utf-8-sig")
        gy_conf.to_csv(paths["gyosan_confidence"], index=False, encoding="utf-8-sig")
        gy_mc_runs.to_csv(paths["gyosan_mc_runs"], index=False, encoding="utf-8-sig")
        gy_scen.to_csv(paths["gyosan_scenario_sensitivity"], index=False, encoding="utf-8-sig")
        gy_blueprint.to_csv(
            paths["gyosan_top20_facility_blueprint"], index=False, encoding="utf-8-sig"
        )
        report_md = docs_dir / "TOP35_UPGRADE_REPORT.md"
        render_report(
            out_md=report_md,
            csv_train=csv_train,
            geo_train=geo_train,
            priority_csv=priority_csv,
            reference_csv=reference_csv,
            blueprint_csv=blueprint_csv,
            transfer_summary=transfer_summary,
            transfer_detail=transfer_detail,
            feat_summary=feat_summary,
            scenario_df=gy_scen,
            mc_runs_df=gy_mc_runs,
            blueprint=gy_blueprint,
        )
        manifest = {
            "project_root": str(root),
            "inputs": {
                "integrated_csv": str(csv_train),
                "main_grid_geojson": str(geo_train),
                "gyosan_grid_geojson": str(gyosan_geo),
                "priority_csv": str(priority_csv),
                "reference_top20_csv": str(reference_csv) if reference_csv else None,
                "blueprint_top20_csv": str(blueprint_csv) if blueprint_csv else None,
            },
            "outputs": {k: str(v) for k, v in paths.items()},
            "config": {"k": k, "bootstrap_runs": bootstrap_runs, "mc_runs": mc_runs, "radius_m": radius_m},
        }
        paths["manifest_json"] = out_dir / "top35_manifest.json"
        paths["manifest_json"].write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    return {
        "transfer_detail": transfer_detail,
        "transfer_summary": transfer_summary,
        "feature_stability_runs": feat_runs,
        "feature_stability_summary": feat_summary,
        "gyosan_confidence": gy_conf,
        "gyosan_mc_runs": gy_mc_runs,
        "gyosan_scenario_sensitivity": gy_scen,
        "gyosan_top20_facility_blueprint": gy_blueprint,
        "model_df": model_df,
        "feat_cols": feat_cols,
        "paths": paths if paths else None,
        "project_root": root,
    }


def save_pipeline_results(results: dict[str, pd.DataFrame | Path | None], project_root: str | Path | None = None) -> dict[str, Path]:
    """
    Save pipeline results (from run_full_pipeline or step-by-step runs) to top35_outputs.
    results must contain the dataframe keys returned by run_full_pipeline.
    """
    root = Path(project_root or results.get("project_root") or Path(__file__).resolve().parents[1]).resolve()
    out_dir = root / "data" / "통합_데이터" / "top35_outputs"
    out_dir.mkdir(parents=True, exist_ok=True)
    # result_key -> filename
    to_save = [
        ("transfer_detail", "transfer_loro_detail.csv"),
        ("transfer_summary", "transfer_loro_summary.csv"),
        ("feature_stability_runs", "feature_stability_runs.csv"),
        ("feature_stability_summary", "feature_stability_summary.csv"),
        ("gyosan_confidence", "gyosan_selection_confidence.csv"),
        ("gyosan_mc_runs", "gyosan_mc_runs.csv"),
        ("gyosan_scenario_sensitivity", "gyosan_scenario_sensitivity.csv"),
        ("gyosan_top20_facility_blueprint", "gyosan_top20_facility_blueprint.csv"),
    ]
    paths = {}
    for result_key, fname in to_save:
        df = results.get(result_key)
        if df is not None and isinstance(df, pd.DataFrame):
            p = out_dir / fname
            df.to_csv(p, index=False, encoding="utf-8-sig")
            paths[result_key] = p
    return paths


if __name__ == "__main__":
    main()
