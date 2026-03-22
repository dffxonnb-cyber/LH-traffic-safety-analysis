#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Run approximate spatial econometric models on full grid data:
- OLS baseline
- SLM (SAR-lag, 2SLS approximation)
- SEM (error model, lambda-grid FGLS approximation)
- SAM (SAC, lambda-grid + lag 2SLS approximation)

Note:
- This implementation is designed to run without PySAL (spreg/libpysal).
- For publication-grade inference (p-values, robust SE), rerun with PySAL.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import numpy as np
import pandas as pd
import geopandas as gpd
from sklearn.neighbors import NearestNeighbors
from scipy import sparse


def build_knn_weights(coords: np.ndarray, k: int) -> sparse.csr_matrix:
    nbrs = NearestNeighbors(n_neighbors=k + 1, algorithm="auto").fit(coords)
    _, idx = nbrs.kneighbors(coords)
    idx = idx[:, 1:]
    n = coords.shape[0]
    rows = np.repeat(np.arange(n), k)
    cols = idx.reshape(-1)
    data = np.ones(n * k, dtype=float)
    w = sparse.csr_matrix((data, (rows, cols)), shape=(n, n))
    row_sum = np.asarray(w.sum(axis=1)).ravel()
    row_sum[row_sum == 0] = 1.0
    w = sparse.diags(1.0 / row_sum).dot(w).tocsr()
    return w


def ols_fit(y: np.ndarray, x: np.ndarray):
    b = np.linalg.pinv(x.T @ x) @ (x.T @ y)
    e = y - x @ b
    sse = float(e.T @ e)
    tss = float(((y - y.mean()) ** 2).sum())
    r2 = 1.0 - sse / tss if tss > 0 else np.nan
    rmse = (sse / len(y)) ** 0.5
    return b, e, r2, rmse


def tsls_fit(y: np.ndarray, d: np.ndarray, x_exog: np.ndarray, z: np.ndarray):
    x1 = np.column_stack([d, x_exog])
    ztz_inv = np.linalg.pinv(z.T @ z)
    b = np.linalg.pinv(x1.T @ (z @ (ztz_inv @ (z.T @ x1)))) @ (
        x1.T @ (z @ (ztz_inv @ (z.T @ y)))
    )
    e = y - x1 @ b
    sse = float(e.T @ e)
    tss = float(((y - y.mean()) ** 2).sum())
    r2 = 1.0 - sse / tss if tss > 0 else np.nan
    rmse = (sse / len(y)) ** 0.5
    return b, e, r2, rmse


def spatial_resid_corr(e: np.ndarray, w: sparse.csr_matrix) -> float:
    we = w.dot(e)
    e0 = e - e.mean()
    w0 = we - we.mean()
    den = np.sqrt((e0 @ e0) * (w0 @ w0))
    return float((e0 @ w0) / den) if den > 0 else np.nan


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", default="data/통합_데이터/격자_최종통합.csv")
    parser.add_argument("--geo", default="data/격자_데이터/01._격자_(4개_시·구).geojson")
    parser.add_argument("--target", default="acc_count", choices=["acc_count", "ARI"])
    parser.add_argument("--k", type=int, default=8)
    parser.add_argument("--sample-n", type=int, default=0, help="0 means full data")
    parser.add_argument("--out-dir", default="outputs")
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    use_cols = ["gid", "acc_count", "ARI", "AADT_mean", "velocity_mean", "FRIN_mean", "TI_mean"]
    df = pd.read_csv(args.csv, usecols=use_cols)

    gdf = gpd.read_file(args.geo)[["gid", "geometry"]]
    if gdf.crs is not None:
        try:
            gdf = gdf.to_crs(epsg=5179)
        except Exception:
            pass

    m = gdf.merge(df, on="gid", how="inner")
    for c in use_cols[1:]:
        m[c] = pd.to_numeric(m[c], errors="coerce").fillna(0.0)

    y_raw = np.clip(m[args.target].to_numpy(float), 0, None)
    y = np.log1p(y_raw)

    feat_cols = ["AADT_mean", "velocity_mean", "FRIN_mean", "TI_mean"]
    x0 = m[feat_cols].to_numpy(float)
    mu = x0.mean(axis=0)
    sd = x0.std(axis=0)
    sd[sd == 0] = 1.0
    x = np.column_stack([np.ones(len(x0)), (x0 - mu) / sd])

    n = len(m)
    if args.sample_n and args.sample_n > 0 and args.sample_n < n:
        rs = np.random.RandomState(42)
        idx = np.sort(rs.choice(n, size=args.sample_n, replace=False))
        m = m.iloc[idx].copy()
        y = y[idx]
        x = x[idx]

    cent = m.geometry.centroid
    coords = np.column_stack([cent.x.to_numpy(), cent.y.to_numpy()])
    w = build_knn_weights(coords, args.k)

    wy = w.dot(y)
    wx = w.dot(x)
    w2y = w.dot(wy)

    # OLS
    b0, e0, r20, rm0 = ols_fit(y, x)

    # SLM (2SLS approx)
    z_slm = np.column_stack([x, wx[:, 1:]])
    b_slm, e_slm, r2_slm, rm_slm = tsls_fit(y, wy, x, z_slm)

    # SEM (lambda grid)
    grid = np.linspace(-0.8, 0.8, 33)
    best_sem = None
    for lam in grid:
        yt = y - lam * wy
        xt = x - lam * wx
        b, e, r2, rm = ols_fit(yt, xt)
        sse = float(e.T @ e)
        if best_sem is None or sse < best_sem[0]:
            best_sem = (sse, lam, b, e, r2, rm)
    _, lam_sem, b_sem, e_sem, r2_sem, rm_sem = best_sem

    # SAM (lambda grid + lag 2SLS)
    best_sam = None
    for lam in grid:
        yt = y - lam * wy
        xt = x - lam * wx
        dt = wy - lam * w2y
        wxt = w.dot(xt)
        zt = np.column_stack([xt, wxt[:, 1:]])
        b, e, r2, rm = tsls_fit(yt, dt, xt, zt)
        sse = float(e.T @ e)
        if best_sam is None or sse < best_sam[0]:
            best_sam = (sse, lam, b, e, r2, rm)
    _, lam_sam, b_sam, e_sam, r2_sam, rm_sam = best_sam

    summary = pd.DataFrame([
        {
            "model": "OLS",
            "rho": np.nan,
            "lambda": np.nan,
            "r2": r20,
            "rmse": rm0,
            "resid_spatial_corr": spatial_resid_corr(e0, w),
            "n": len(y),
            "k": args.k,
            "target": args.target,
        },
        {
            "model": "SLM",
            "rho": float(b_slm[0]),
            "lambda": np.nan,
            "r2": r2_slm,
            "rmse": rm_slm,
            "resid_spatial_corr": spatial_resid_corr(e_slm, w),
            "n": len(y),
            "k": args.k,
            "target": args.target,
        },
        {
            "model": "SEM",
            "rho": np.nan,
            "lambda": float(lam_sem),
            "r2": r2_sem,
            "rmse": rm_sem,
            "resid_spatial_corr": spatial_resid_corr(e_sem, w),
            "n": len(y),
            "k": args.k,
            "target": args.target,
        },
        {
            "model": "SAM",
            "rho": float(b_sam[0]),
            "lambda": float(lam_sam),
            "r2": r2_sam,
            "rmse": rm_sam,
            "resid_spatial_corr": spatial_resid_corr(e_sam, w),
            "n": len(y),
            "k": args.k,
            "target": args.target,
        },
    ])

    coef_rows = []
    names = ["const"] + feat_cols
    for model_name, coef in [
        ("SLM", b_slm),
        ("SEM", b_sem),
        ("SAM", b_sam),
    ]:
        if model_name in ["SLM", "SAM"]:
            coef_rows.append({"model": model_name, "term": "rho", "coef": float(coef[0])})
            offset = 1
        else:
            offset = 0
        for i, nm in enumerate(names):
            coef_rows.append({"model": model_name, "term": nm, "coef": float(coef[i + offset])})

    coef_df = pd.DataFrame(coef_rows)

    summary_path = out_dir / f"spatial_summary_{args.target}.csv"
    coef_path = out_dir / f"spatial_coefs_{args.target}.csv"
    summary.to_csv(summary_path, index=False, encoding="utf-8-sig")
    coef_df.to_csv(coef_path, index=False, encoding="utf-8-sig")

    print("[DONE]", summary_path)
    print("[DONE]", coef_path)
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
