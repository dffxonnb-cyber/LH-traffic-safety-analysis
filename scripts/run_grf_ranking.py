#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Run the spatial-coordinate Random Forest risk ranking model:
- Target: log1p(acc_count) or log1p(ARI)
- Features: traffic indicators + centroid coordinates
- Output: full-grid predicted risk ranking for policy prioritization

Note:
- This implementation uses sklearn RandomForestRegressor with centroid coordinates.
- The legacy script filename is retained for compatibility; this is not a dedicated
  geographically weighted random forest implementation.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import numpy as np
import pandas as pd
import geopandas as gpd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.model_selection import train_test_split


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", default="data/통합_데이터/격자_최종통합.csv")
    parser.add_argument("--geo", default="data/격자_데이터/01._격자_(4개_시·구).geojson")
    parser.add_argument("--target", default="acc_count", choices=["acc_count", "ARI"])
    parser.add_argument("--n-estimators", type=int, default=500)
    parser.add_argument("--max-depth", type=int, default=18)
    parser.add_argument("--test-size", type=float, default=0.2)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--out-dir", default="outputs")
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    use_cols = ["gid", "gbn", "acc_count", "ARI", "AADT_mean", "velocity_mean", "FRIN_mean", "TI_mean"]
    df = pd.read_csv(args.csv, usecols=use_cols)

    gdf = gpd.read_file(args.geo)[["gid", "geometry"]]
    if gdf.crs is not None:
        try:
            gdf = gdf.to_crs(epsg=5179)
        except Exception:
            pass

    m = gdf.merge(df, on="gid", how="inner")

    for c in ["acc_count", "ARI", "AADT_mean", "velocity_mean", "FRIN_mean", "TI_mean"]:
        m[c] = pd.to_numeric(m[c], errors="coerce").fillna(0.0)

    cent = m.geometry.centroid
    m["x_coord"] = cent.x.to_numpy()
    m["y_coord"] = cent.y.to_numpy()

    y_raw = np.clip(m[args.target].to_numpy(float), 0, None)
    y = np.log1p(y_raw)

    feat_cols = ["AADT_mean", "velocity_mean", "FRIN_mean", "TI_mean", "x_coord", "y_coord"]
    X = m[feat_cols].to_numpy(float)

    X_train, X_test, y_train, y_test, idx_train, idx_test = train_test_split(
        X, y, np.arange(len(m)), test_size=args.test_size, random_state=args.seed
    )

    rf = RandomForestRegressor(
        n_estimators=args.n_estimators,
        max_depth=args.max_depth,
        min_samples_leaf=5,
        n_jobs=-1,
        random_state=args.seed,
        oob_score=True,
    )
    rf.fit(X_train, y_train)

    pred_test = rf.predict(X_test)
    test_rmse = float(np.sqrt(mean_squared_error(y_test, pred_test)))
    test_r2 = float(r2_score(y_test, pred_test))
    oob = float(rf.oob_score_)

    # Full-grid predictions for ranking
    pred_all = rf.predict(X)
    out = m[["gid", "gbn"]].copy()
    out["pred_log_risk"] = pred_all
    out["pred_risk"] = np.expm1(np.clip(pred_all, 0, None))
    out["rank_desc"] = out["pred_risk"].rank(ascending=False, method="first").astype(int)
    out["rank_pct"] = out["pred_risk"].rank(pct=True)

    imp = pd.DataFrame({
        "feature": feat_cols,
        "importance": rf.feature_importances_,
    }).sort_values("importance", ascending=False)

    metric_df = pd.DataFrame([
        {
            "target": args.target,
            "n_rows": len(m),
            "n_estimators": args.n_estimators,
            "max_depth": args.max_depth,
            "test_rmse": test_rmse,
            "test_r2": test_r2,
            "oob_r2": oob,
        }
    ])

    rank_path = out_dir / f"grf_ranking_{args.target}.csv"
    imp_path = out_dir / f"grf_feature_importance_{args.target}.csv"
    met_path = out_dir / f"grf_metrics_{args.target}.csv"

    out.to_csv(rank_path, index=False, encoding="utf-8-sig")
    imp.to_csv(imp_path, index=False, encoding="utf-8-sig")
    metric_df.to_csv(met_path, index=False, encoding="utf-8-sig")

    print("[DONE]", rank_path)
    print("[DONE]", imp_path)
    print("[DONE]", met_path)
    print(metric_df.to_string(index=False))
    print("\nTop feature importance")
    print(imp.head(10).to_string(index=False))


if __name__ == "__main__":
    main()
