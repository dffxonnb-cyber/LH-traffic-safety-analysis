from __future__ import annotations

from types import SimpleNamespace
from dataclasses import dataclass
from pathlib import Path
import numpy as np
import pandas as pd
import geopandas as gpd
from sklearn.neighbors import NearestNeighbors
from sklearn.ensemble import RandomForestRegressor
from scipy import sparse


@dataclass
class GWRReturn:
    results: SimpleNamespace
    params_df: pd.DataFrame
    local_r2_df: pd.DataFrame
    pred_df: pd.DataFrame
    gwr_gdf: gpd.GeoDataFrame


@dataclass
class SLMReturn:
    results: SimpleNamespace
    coef_table_df: pd.DataFrame
    rho_df: pd.DataFrame
    residual_df: pd.DataFrame
    pred_df: pd.DataFrame


@dataclass
class GRFReturn:
    results: SimpleNamespace
    regional_importance_df: pd.DataFrame
    prediction_df: pd.DataFrame
    oob_df: pd.DataFrame


def _load_base(
    csv_path: str | Path = 'data/통합_데이터/격자_최종통합.csv',
    geo_path: str | Path = 'data/격자_데이터/01._격자_(4개_시·구).geojson',
) -> gpd.GeoDataFrame:
    df = pd.read_csv(csv_path)
    gdf = gpd.read_file(geo_path)[['gid', 'geometry']]
    if gdf.crs is not None:
        try:
            gdf = gdf.to_crs(epsg=5179)
        except Exception:
            pass
    m = gdf.merge(df, on='gid', how='inner')
    return m


def _zscore(x: np.ndarray):
    mu = x.mean(axis=0)
    sd = x.std(axis=0)
    sd[sd == 0] = 1.0
    return (x - mu) / sd, mu, sd


def run_gwr_no_save(
    target: str = 'acc_count',
    feature_cols: list[str] | None = None,
    bandwidth_k: int = 120,
    sample_n: int | None = 3000,
    random_state: int = 42,
    csv_path: str | Path = 'data/통합_데이터/격자_최종통합.csv',
    geo_path: str | Path = 'data/격자_데이터/01._격자_(4개_시·구).geojson',
) -> GWRReturn:
    """
    GWR-like local weighted regression using kNN Gaussian kernel.
    Returns only in-memory objects; does not write files.
    """
    if feature_cols is None:
        feature_cols = ['AADT_mean', 'velocity_mean', 'FRIN_mean', 'TI_mean']

    m = _load_base(csv_path, geo_path)
    keep = ['gid', 'geometry', target] + feature_cols
    keep = [c for c in keep if c in m.columns]
    m = m[keep].copy()

    for c in [target] + feature_cols:
        if c in m.columns:
            m[c] = pd.to_numeric(m[c], errors='coerce').fillna(0.0)

    if sample_n is not None and sample_n > 0 and sample_n < len(m):
        rs = np.random.RandomState(random_state)
        idx = np.sort(rs.choice(len(m), size=sample_n, replace=False))
        m = m.iloc[idx].copy().reset_index(drop=True)

    y_raw = np.clip(m[target].to_numpy(float), 0, None)
    y = np.log1p(y_raw)
    x0 = m[feature_cols].to_numpy(float)
    xz, _, _ = _zscore(x0)
    X = np.column_stack([np.ones(len(m)), xz])

    cent = m.geometry.centroid
    coords = np.column_stack([cent.x.to_numpy(), cent.y.to_numpy()])

    # local neighbors for each point
    nn = NearestNeighbors(n_neighbors=bandwidth_k).fit(coords)
    dist, idx = nn.kneighbors(coords)

    n, p = X.shape
    betas = np.zeros((n, p), dtype=float)
    yhat = np.zeros(n, dtype=float)
    local_r2 = np.zeros(n, dtype=float)

    eps = 1e-9
    for i in range(n):
        ni = idx[i]
        di = dist[i]
        # adaptive Gaussian kernel
        bw = max(di[-1], eps)
        wi = np.exp(-0.5 * (di / bw) ** 2)

        Xi = X[ni]
        yi = y[ni]
        W = np.diag(wi)

        XtWX = Xi.T @ W @ Xi
        XtWy = Xi.T @ W @ yi
        b = np.linalg.pinv(XtWX) @ XtWy
        betas[i] = b

        yhat_i = float(X[i] @ b)
        yhat[i] = yhat_i

        # weighted local R2 around i
        ybar = float(np.sum(wi * yi) / np.sum(wi))
        sse = float(np.sum(wi * (yi - Xi @ b) ** 2))
        tss = float(np.sum(wi * (yi - ybar) ** 2))
        local_r2[i] = 1.0 - sse / tss if tss > eps else np.nan

    resid = y - yhat
    global_r2 = 1.0 - float((resid @ resid) / np.sum((y - y.mean()) ** 2))

    coef_names = ['const'] + feature_cols
    params_df = pd.DataFrame(betas, columns=coef_names)
    params_df.insert(0, 'gid', m['gid'].values)

    local_r2_df = pd.DataFrame({
        'gid': m['gid'].values,
        'local_r2': local_r2,
    })

    pred_df = pd.DataFrame({
        'gid': m['gid'].values,
        'y_true_log1p': y,
        'y_pred_log1p': yhat,
        'residual': resid,
        'y_true': y_raw,
        'y_pred': np.expm1(np.clip(yhat, 0, None)),
    })

    gwr_gdf = m[['gid', 'geometry']].merge(params_df, on='gid').merge(local_r2_df, on='gid').merge(pred_df, on='gid')

    results = SimpleNamespace(
        model='GWR_like_kNN_Gaussian',
        n=n,
        p=p,
        target=target,
        feature_cols=feature_cols,
        bandwidth_k=bandwidth_k,
        sample_n=sample_n,
        global_r2=float(global_r2),
    )

    return GWRReturn(
        results=results,
        params_df=params_df,
        local_r2_df=local_r2_df,
        pred_df=pred_df,
        gwr_gdf=gwr_gdf,
    )


def run_slm_no_save(
    target: str = 'acc_count',
    feature_cols: list[str] | None = None,
    k_neighbors: int = 8,
    sample_n: int | None = 0,
    random_state: int = 42,
    csv_path: str | Path = 'data/통합_데이터/격자_최종통합.csv',
    geo_path: str | Path = 'data/격자_데이터/01._격자_(4개_시·구).geojson',
) -> SLMReturn:
    """
    Spatial Lag Model (SLM/SAR-lag) via 2SLS approximation.
    Returns structured DataFrames only; does not write files.
    """
    if feature_cols is None:
        feature_cols = ['AADT_mean', 'velocity_mean', 'FRIN_mean', 'TI_mean']

    m = _load_base(csv_path, geo_path)
    keep = ['gid', target] + feature_cols + ['geometry']
    keep = [c for c in keep if c in m.columns]
    m = m[keep].copy()

    for c in [target] + feature_cols:
        if c in m.columns:
            m[c] = pd.to_numeric(m[c], errors='coerce').fillna(0.0)

    if sample_n is not None and sample_n > 0 and sample_n < len(m):
        rs = np.random.RandomState(random_state)
        idx = np.sort(rs.choice(len(m), size=sample_n, replace=False))
        m = m.iloc[idx].copy().reset_index(drop=True)

    y_raw = np.clip(m[target].to_numpy(float), 0, None)
    y = np.log1p(y_raw)
    x0 = m[feature_cols].to_numpy(float)
    xz, _, _ = _zscore(x0)
    X = np.column_stack([np.ones(len(m)), xz])

    cent = m.geometry.centroid
    coords = np.column_stack([cent.x.to_numpy(), cent.y.to_numpy()])

    nn = NearestNeighbors(n_neighbors=k_neighbors + 1).fit(coords)
    _, idx = nn.kneighbors(coords)
    idx = idx[:, 1:]

    n = len(m)
    rows = np.repeat(np.arange(n), k_neighbors)
    cols = idx.reshape(-1)
    data = np.ones(n * k_neighbors, dtype=float)
    W = sparse.csr_matrix((data, (rows, cols)), shape=(n, n))
    rsum = np.asarray(W.sum(axis=1)).ravel()
    rsum[rsum == 0] = 1.0
    W = sparse.diags(1.0 / rsum).dot(W).tocsr()

    Wy = W.dot(y)
    WX = W.dot(X)

    # 2SLS: y = rho*Wy + X*beta + e
    Z = np.column_stack([X, WX[:, 1:]])
    X1 = np.column_stack([Wy, X])

    ZtZ_inv = np.linalg.pinv(Z.T @ Z)
    b = np.linalg.pinv(X1.T @ (Z @ (ZtZ_inv @ (Z.T @ X1)))) @ (X1.T @ (Z @ (ZtZ_inv @ (Z.T @ y))))

    rho = float(b[0])
    beta = b[1:]

    y_pred = X1 @ b
    resid = y - y_pred

    sse = float(resid.T @ resid)
    tss = float(((y - y.mean()) ** 2).sum())
    r2 = 1.0 - sse / tss if tss > 0 else np.nan

    coef_terms = ['const'] + feature_cols
    coef_table_df = pd.DataFrame({
        'term': coef_terms,
        'coef': beta,
    })

    rho_df = pd.DataFrame({'rho': [rho], 'target': [target], 'k_neighbors': [k_neighbors], 'n': [n], 'r2': [r2]})

    residual_df = pd.DataFrame({
        'gid': m['gid'].values,
        'residual': resid,
    })

    pred_df = pd.DataFrame({
        'gid': m['gid'].values,
        'y_true_log1p': y,
        'y_pred_log1p': y_pred,
        'y_true': y_raw,
        'y_pred': np.expm1(np.clip(y_pred, 0, None)),
    })

    results = SimpleNamespace(
        model='SLM_2SLS_approx',
        n=n,
        target=target,
        feature_cols=feature_cols,
        k_neighbors=k_neighbors,
        rho=rho,
        r2=float(r2),
    )

    return SLMReturn(
        results=results,
        coef_table_df=coef_table_df,
        rho_df=rho_df,
        residual_df=residual_df,
        pred_df=pred_df,
    )


def run_grf_no_save(
    target: str = 'acc_count',
    feature_cols: list[str] | None = None,
    n_estimators: int = 500,
    max_depth: int | None = 18,
    min_samples_leaf: int = 5,
    sample_n: int | None = 0,
    random_state: int = 42,
    csv_path: str | Path = 'data/통합_데이터/격자_최종통합.csv',
    geo_path: str | Path = 'data/격자_데이터/01._격자_(4개_시·구).geojson',
) -> GRFReturn:
    """
    Geographical Random Forest-like workflow:
    - global RF with spatial coordinates included
    - region-wise RF (by gbn) for regional feature importance and regional OOB
    Returns structured DataFrames only; does not write files.
    """
    if feature_cols is None:
        feature_cols = ['AADT_mean', 'velocity_mean', 'FRIN_mean', 'TI_mean']

    m = _load_base(csv_path, geo_path)
    keep = ['gid', 'gbn', target, 'geometry'] + feature_cols
    keep = [c for c in keep if c in m.columns]
    m = m[keep].copy()

    if 'gbn' not in m.columns:
        m['gbn'] = 'UNKNOWN'

    for c in [target] + feature_cols:
        if c in m.columns:
            m[c] = pd.to_numeric(m[c], errors='coerce').fillna(0.0)

    if sample_n is not None and sample_n > 0 and sample_n < len(m):
        rs = np.random.RandomState(random_state)
        idx = np.sort(rs.choice(len(m), size=sample_n, replace=False))
        m = m.iloc[idx].copy().reset_index(drop=True)

    cent = m.geometry.centroid
    m['x_coord'] = cent.x.to_numpy()
    m['y_coord'] = cent.y.to_numpy()

    y_raw = np.clip(m[target].to_numpy(float), 0, None)
    y = np.log1p(y_raw)

    feat = [c for c in feature_cols if c in m.columns] + ['x_coord', 'y_coord']
    X = m[feat].to_numpy(float)

    rf = RandomForestRegressor(
        n_estimators=n_estimators,
        max_depth=max_depth,
        min_samples_leaf=min_samples_leaf,
        random_state=random_state,
        n_jobs=-1,
        oob_score=True,
    )
    rf.fit(X, y)

    pred_log = rf.predict(X)
    pred = np.expm1(np.clip(pred_log, 0, None))
    resid = y - pred_log

    prediction_df = pd.DataFrame({
        'gid': m['gid'].values,
        'gbn': m['gbn'].values,
        'y_true_log1p': y,
        'y_pred_log1p': pred_log,
        'residual': resid,
        'y_true': y_raw,
        'y_pred': pred,
    })

    # global + regional OOB
    oob_rows = [{
        'scope': 'GLOBAL',
        'gbn': 'ALL',
        'n': int(len(m)),
        'oob_score': float(rf.oob_score_),
    }]

    # regional feature importance (fit per gbn)
    reg_rows = []
    for gbn, g in m.groupby('gbn'):
        if len(g) < max(50, len(feat) * 5):
            # too small for stable local RF
            row = {'gbn': gbn, 'n': int(len(g))}
            for f in feat:
                row[f] = np.nan
            reg_rows.append(row)
            oob_rows.append({'scope': 'REGION', 'gbn': gbn, 'n': int(len(g)), 'oob_score': np.nan})
            continue

        Xg = g[feat].to_numpy(float)
        yg = np.log1p(np.clip(g[target].to_numpy(float), 0, None))
        rg = RandomForestRegressor(
            n_estimators=n_estimators,
            max_depth=max_depth,
            min_samples_leaf=min_samples_leaf,
            random_state=random_state,
            n_jobs=-1,
            oob_score=True,
        )
        rg.fit(Xg, yg)

        row = {'gbn': gbn, 'n': int(len(g))}
        for f, imp in zip(feat, rg.feature_importances_):
            row[f] = float(imp)
        reg_rows.append(row)
        oob_rows.append({'scope': 'REGION', 'gbn': gbn, 'n': int(len(g)), 'oob_score': float(rg.oob_score_)})

    regional_importance_df = pd.DataFrame(reg_rows)
    oob_df = pd.DataFrame(oob_rows)

    results = SimpleNamespace(
        model='GRF_like_RF_with_coords',
        n=int(len(m)),
        target=target,
        feature_cols=feature_cols,
        final_features=feat,
        n_estimators=n_estimators,
        max_depth=max_depth,
        min_samples_leaf=min_samples_leaf,
        global_oob=float(rf.oob_score_),
    )

    return GRFReturn(
        results=results,
        regional_importance_df=regional_importance_df,
        prediction_df=prediction_df,
        oob_df=oob_df,
    )
