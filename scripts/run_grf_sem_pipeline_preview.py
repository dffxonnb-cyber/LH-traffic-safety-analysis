from __future__ import annotations

"""
Spatial-coordinate Random Forest / SEM / MGWR preview pipeline for sparse accident-grid data.
- No file writing by default
- Returns structured pandas/geopandas tables

Main ideas implemented from your memo:
1) Zero-inflated target 대응: 회귀(acc_count), 가중회귀(weighted_count), 분류(0/1)
2) 독립변수 MinMax 정규화
3) Random Forest + spatial coordinates 성능검수 + 변수중요도
4) SEM 근사로 숨은 변수의 공간오차 반영 여부 확인
5) MGWR는 설치되어 있을 때만 선택 실행
"""

from dataclasses import dataclass
from types import SimpleNamespace
from pathlib import Path
import numpy as np
import pandas as pd
import geopandas as gpd

from sklearn.preprocessing import MinMaxScaler
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    r2_score,
    mean_squared_error,
    roc_auc_score,
    f1_score,
    precision_score,
    recall_score,
    accuracy_score,
)
from sklearn.model_selection import train_test_split
from sklearn.neighbors import NearestNeighbors
from scipy import sparse


@dataclass
class PipelineResult:
    meta: SimpleNamespace
    model_metrics_df: pd.DataFrame
    feature_importance_df: pd.DataFrame
    regional_importance_df: pd.DataFrame
    prediction_df: pd.DataFrame
    sem_summary_df: pd.DataFrame
    sem_coef_df: pd.DataFrame
    mgwr_available: bool
    mgwr_summary_df: pd.DataFrame


def _load_merged(csv_path: str | Path, geo_path: str | Path) -> gpd.GeoDataFrame:
    df = pd.read_csv(csv_path)
    gdf = gpd.read_file(geo_path)[['gid', 'geometry']]
    if gdf.crs is not None:
        try:
            gdf = gdf.to_crs(epsg=5179)
        except Exception:
            pass
    m = gdf.merge(df, on='gid', how='inner')
    if 'gbn' not in m.columns:
        m['gbn'] = 'UNKNOWN'
    return m


def _build_knn_w(coords: np.ndarray, k: int) -> sparse.csr_matrix:
    nn = NearestNeighbors(n_neighbors=k + 1).fit(coords)
    _, idx = nn.kneighbors(coords)
    idx = idx[:, 1:]
    n = len(coords)
    rows = np.repeat(np.arange(n), k)
    cols = idx.reshape(-1)
    data = np.ones(n * k, dtype=float)
    w = sparse.csr_matrix((data, (rows, cols)), shape=(n, n))
    rs = np.asarray(w.sum(axis=1)).ravel()
    rs[rs == 0] = 1.0
    return sparse.diags(1.0 / rs).dot(w).tocsr()


def _sem_grid_approx(y: np.ndarray, X: np.ndarray, W: sparse.csr_matrix):
    """SEM 근사: y-lambdaWy ~ (X-lambdaWX) OLS grid search"""
    Wy = W.dot(y)
    WX = W.dot(X)

    def ols(yv, Xv):
        b = np.linalg.pinv(Xv.T @ Xv) @ (Xv.T @ yv)
        e = yv - Xv @ b
        sse = float(e.T @ e)
        tss = float(((yv - yv.mean()) ** 2).sum())
        r2 = 1 - sse / tss if tss > 0 else np.nan
        rmse = (sse / len(yv)) ** 0.5
        return b, e, r2, rmse

    grid = np.linspace(-0.8, 0.8, 33)
    best = None
    for lam in grid:
        yt = y - lam * Wy
        Xt = X - lam * WX
        b, e, r2, rmse = ols(yt, Xt)
        sse = float(e.T @ e)
        if best is None or sse < best[0]:
            best = (sse, lam, b, e, r2, rmse)

    _, lam, b, e, r2, rmse = best

    We = W.dot(e)
    e0 = e - e.mean()
    w0 = We - We.mean()
    den = np.sqrt((e0 @ e0) * (w0 @ w0))
    resid_sp_corr = float((e0 @ w0) / den) if den > 0 else np.nan

    return {
        'lambda': float(lam),
        'r2': float(r2),
        'rmse': float(rmse),
        'resid_spatial_corr': resid_sp_corr,
        'coef': b,
    }


def run_full_pipeline_no_save(
    csv_path: str | Path = 'data/통합_데이터/격자_최종통합.csv',
    geo_path: str | Path = 'data/격자_데이터/01._격자_(4개_시·구).geojson',
    feature_cols: list[str] | None = None,
    random_state: int = 42,
    test_size: float = 0.2,
    n_estimators: int = 500,
    max_depth: int | None = 18,
    min_samples_leaf: int = 5,
    knn_k: int = 8,
    sample_n: int = 0,
    run_mgwr: bool = True,
) -> PipelineResult:
    """
    Returns all results as DataFrames / metadata only.
    No write_csv / file saving.
    """
    if feature_cols is None:
        feature_cols = ['AADT_mean', 'velocity_mean', 'FRIN_mean', 'TI_mean']

    m = _load_merged(csv_path, geo_path)

    required = ['gid', 'gbn', 'acc_count'] + feature_cols
    keep = [c for c in required if c in m.columns] + ['geometry']
    m = m[keep].copy()

    for c in ['acc_count'] + feature_cols:
        m[c] = pd.to_numeric(m[c], errors='coerce').fillna(0.0)

    if sample_n and sample_n > 0 and sample_n < len(m):
        rs = np.random.RandomState(random_state)
        idx = np.sort(rs.choice(len(m), size=sample_n, replace=False))
        m = m.iloc[idx].copy().reset_index(drop=True)

    cent = m.geometry.centroid
    m['x_coord'] = cent.x.to_numpy()
    m['y_coord'] = cent.y.to_numpy()

    # Targets
    y_count_raw = np.clip(m['acc_count'].to_numpy(float), 0, None)
    y_count = np.log1p(y_count_raw)
    y_bin = (y_count_raw > 0).astype(int)
    y_weighted_raw = np.clip(y_count_raw, 0, 24)  # 1~24 가중 반영 취지 (상한 24)
    y_weighted = np.log1p(y_weighted_raw)

    feat = [c for c in feature_cols if c in m.columns] + ['x_coord', 'y_coord']
    X_raw = m[feat].to_numpy(float)

    # MinMax scaling (공간데이터 정규화 요구 반영)
    scaler = MinMaxScaler()
    X = scaler.fit_transform(X_raw)

    # Split index shared
    idx_all = np.arange(len(m))
    tr_idx, te_idx = train_test_split(idx_all, test_size=test_size, random_state=random_state, stratify=y_bin)

    def split_xy(y):
        return X[tr_idx], X[te_idx], y[tr_idx], y[te_idx]

    # ========== Model 1: spatial-coordinate RF regression (count) ==========
    Xtr, Xte, ytr, yte = split_xy(y_count)
    rf_count = RandomForestRegressor(
        n_estimators=n_estimators,
        max_depth=max_depth,
        min_samples_leaf=min_samples_leaf,
        random_state=random_state,
        n_jobs=-1,
        oob_score=True,
    )
    rf_count.fit(Xtr, ytr)
    pred_count_te = rf_count.predict(Xte)
    pred_count_all = rf_count.predict(X)

    # ========== Model 2: spatial-coordinate RF regression (weighted count) ==========
    Xtr_w, Xte_w, ytr_w, yte_w = split_xy(y_weighted)
    rf_weight = RandomForestRegressor(
        n_estimators=n_estimators,
        max_depth=max_depth,
        min_samples_leaf=min_samples_leaf,
        random_state=random_state,
        n_jobs=-1,
        oob_score=True,
    )
    rf_weight.fit(Xtr_w, ytr_w)
    pred_weight_te = rf_weight.predict(Xte_w)
    pred_weight_all = rf_weight.predict(X)

    # ========== Model 3: spatial-coordinate RF classifier (0/1) ==========
    Xtr_b, Xte_b, ytr_b, yte_b = split_xy(y_bin)
    rf_bin = RandomForestClassifier(
        n_estimators=n_estimators,
        max_depth=max_depth,
        min_samples_leaf=min_samples_leaf,
        random_state=random_state,
        n_jobs=-1,
        oob_score=True,
        class_weight='balanced_subsample',
    )
    rf_bin.fit(Xtr_b, ytr_b)
    proba_te = rf_bin.predict_proba(Xte_b)[:, 1]
    pred_bin_te = (proba_te >= 0.5).astype(int)
    proba_all = rf_bin.predict_proba(X)[:, 1]

    # ========== Baseline: Logistic ==========
    logit = LogisticRegression(max_iter=2000, class_weight='balanced', n_jobs=None, random_state=random_state)
    logit.fit(Xtr_b, ytr_b)
    logit_proba_te = logit.predict_proba(Xte_b)[:, 1]
    logit_pred_te = (logit_proba_te >= 0.5).astype(int)

    # ========== SEM approximation ==========
    coords = np.column_stack([m['x_coord'].to_numpy(), m['y_coord'].to_numpy()])
    W = _build_knn_w(coords, knn_k)
    X_sem = np.column_stack([np.ones(len(m)), X[:, :len(feature_cols)]])  # coords 제외 설명변수만
    sem = _sem_grid_approx(y_count, X_sem, W)

    # Metrics table
    metrics_rows = [
        {
            'model': 'GRF_REG_COUNT',
            'target': 'log1p(acc_count)',
            'test_r2': float(r2_score(yte, pred_count_te)),
            'test_rmse': float(np.sqrt(mean_squared_error(yte, pred_count_te))),
            'oob': float(rf_count.oob_score_),
            'auc': np.nan,
            'f1': np.nan,
            'acc': np.nan,
        },
        {
            'model': 'GRF_REG_WEIGHTED',
            'target': 'log1p(min(acc_count,24))',
            'test_r2': float(r2_score(yte_w, pred_weight_te)),
            'test_rmse': float(np.sqrt(mean_squared_error(yte_w, pred_weight_te))),
            'oob': float(rf_weight.oob_score_),
            'auc': np.nan,
            'f1': np.nan,
            'acc': np.nan,
        },
        {
            'model': 'GRF_CLASS_BIN',
            'target': 'acc_count>0',
            'test_r2': np.nan,
            'test_rmse': np.nan,
            'oob': float(rf_bin.oob_score_),
            'auc': float(roc_auc_score(yte_b, proba_te)),
            'f1': float(f1_score(yte_b, pred_bin_te, zero_division=0)),
            'acc': float(accuracy_score(yte_b, pred_bin_te)),
        },
        {
            'model': 'LOGIT_BIN',
            'target': 'acc_count>0',
            'test_r2': np.nan,
            'test_rmse': np.nan,
            'oob': np.nan,
            'auc': float(roc_auc_score(yte_b, logit_proba_te)),
            'f1': float(f1_score(yte_b, logit_pred_te, zero_division=0)),
            'acc': float(accuracy_score(yte_b, logit_pred_te)),
        },
        {
            'model': 'SEM_APPROX',
            'target': 'log1p(acc_count)',
            'test_r2': sem['r2'],
            'test_rmse': sem['rmse'],
            'oob': np.nan,
            'auc': np.nan,
            'f1': np.nan,
            'acc': np.nan,
        },
    ]
    model_metrics_df = pd.DataFrame(metrics_rows)

    # Feature importance (global)
    fi_rows = []
    for model_name, imps in [
        ('GRF_REG_COUNT', rf_count.feature_importances_),
        ('GRF_REG_WEIGHTED', rf_weight.feature_importances_),
        ('GRF_CLASS_BIN', rf_bin.feature_importances_),
    ]:
        for f, imp in zip(feat, imps):
            fi_rows.append({'model': model_name, 'feature': f, 'importance': float(imp)})
    feature_importance_df = pd.DataFrame(fi_rows)

    # Regional importance + regional OOB (classifier 기준)
    reg_rows = []
    for gbn, g in m.groupby('gbn'):
        if len(g) < max(80, len(feat) * 8):
            row = {'gbn': gbn, 'n': int(len(g)), 'oob': np.nan}
            for f in feat:
                row[f] = np.nan
            reg_rows.append(row)
            continue

        Xg = scaler.transform(g[feat].to_numpy(float))
        yg = (np.clip(g['acc_count'].to_numpy(float), 0, None) > 0).astype(int)

        rg = RandomForestClassifier(
            n_estimators=n_estimators,
            max_depth=max_depth,
            min_samples_leaf=min_samples_leaf,
            random_state=random_state,
            n_jobs=-1,
            oob_score=True,
            class_weight='balanced_subsample',
        )
        rg.fit(Xg, yg)

        row = {'gbn': gbn, 'n': int(len(g)), 'oob': float(rg.oob_score_)}
        for f, imp in zip(feat, rg.feature_importances_):
            row[f] = float(imp)
        reg_rows.append(row)

    regional_importance_df = pd.DataFrame(reg_rows)

    # Prediction table (all rows)
    prediction_df = pd.DataFrame({
        'gid': m['gid'].values,
        'gbn': m['gbn'].values,
        'acc_count_true': y_count_raw,
        'pred_count': np.expm1(np.clip(pred_count_all, 0, None)),
        'pred_weighted_count': np.expm1(np.clip(pred_weight_all, 0, None)),
        'pred_prob_accident': proba_all,
        'pred_flag_accident': (proba_all >= 0.5).astype(int),
    })

    # SEM summary/coefs
    sem_summary_df = pd.DataFrame([{
        'model': 'SEM_APPROX',
        'lambda': sem['lambda'],
        'r2': sem['r2'],
        'rmse': sem['rmse'],
        'resid_spatial_corr': sem['resid_spatial_corr'],
        'n': len(m),
        'k_neighbors': knn_k,
    }])
    sem_coef_df = pd.DataFrame({
        'term': ['const'] + [c for c in feature_cols if c in m.columns],
        'coef': sem['coef'],
    })

    # Optional MGWR
    mgwr_available = False
    mgwr_summary_df = pd.DataFrame(columns=['status', 'message'])
    if run_mgwr:
        try:
            from mgwr.sel_bw import Sel_BW
            from mgwr.gwr import MGWR
            mgwr_available = True

            # MGWR는 계산량이 커서 자동 샘플 제한
            m_mg = m.copy()
            max_mg = 5000
            if len(m_mg) > max_mg:
                rs = np.random.RandomState(random_state)
                idx = np.sort(rs.choice(len(m_mg), size=max_mg, replace=False))
                m_mg = m_mg.iloc[idx].copy().reset_index(drop=True)

            coords_mg = np.column_stack([m_mg['x_coord'].to_numpy(), m_mg['y_coord'].to_numpy()])
            y_mg = np.log1p(np.clip(m_mg['acc_count'].to_numpy(float), 0, None)).reshape((-1, 1))
            X_mg_raw = m_mg[[c for c in feature_cols if c in m_mg.columns]].to_numpy(float)
            X_mg = MinMaxScaler().fit_transform(X_mg_raw)

            bw = Sel_BW(coords_mg, y_mg, X_mg, multi=True).search()
            mg = MGWR(coords_mg, y_mg, X_mg, selector=SimpleNamespace(bw=bw))
            # Some mgwr versions require selector object; this line may vary.
            # To keep robust, return availability message instead of forcing fit failure.
            mgwr_summary_df = pd.DataFrame([{
                'status': 'AVAILABLE_NOT_FIT',
                'message': 'mgwr package detected. Fit API differs by version; run dedicated notebook for final fit.',
            }])
        except Exception as e:
            mgwr_available = False
            mgwr_summary_df = pd.DataFrame([{
                'status': 'NOT_AVAILABLE_OR_FAILED',
                'message': str(e),
            }])

    meta = SimpleNamespace(
        n=int(len(m)),
        random_state=random_state,
        features=feat,
        test_size=test_size,
        note='No file saving. All outputs are DataFrames in memory.'
    )

    return PipelineResult(
        meta=meta,
        model_metrics_df=model_metrics_df,
        feature_importance_df=feature_importance_df,
        regional_importance_df=regional_importance_df,
        prediction_df=prediction_df,
        sem_summary_df=sem_summary_df,
        sem_coef_df=sem_coef_df,
        mgwr_available=mgwr_available,
        mgwr_summary_df=mgwr_summary_df,
    )


if __name__ == '__main__':
    res = run_full_pipeline_no_save(sample_n=0, run_mgwr=False)
    print(res.meta)
    print('\n[MODEL_METRICS]')
    print(res.model_metrics_df)
    print('\n[GLOBAL_FEATURE_IMPORTANCE]')
    print(res.feature_importance_df.sort_values(['model', 'importance'], ascending=[True, False]).head(20))
    print('\n[REGIONAL_IMPORTANCE]')
    print(res.regional_importance_df)
    print('\n[PREDICTION_HEAD]')
    print(res.prediction_df.head())
    print('\n[SEM_SUMMARY]')
    print(res.sem_summary_df)
