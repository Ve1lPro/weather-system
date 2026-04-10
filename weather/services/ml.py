import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from .features import build_lag_features

def train_and_predict_temp(df: pd.DataFrame, horizon_hours: int = 12, model_name="rf_lag") -> pd.DataFrame:
    """随机森林 + 滞后特征：训练并递推预测未来 horizon_hours 小时温度"""
    df2, X_cols = build_lag_features(df, y_col="temp_c")
    X = df2[X_cols].values
    y = df2["temp_c"].values

    model = RandomForestRegressor(
        n_estimators=400,
        random_state=42,
        n_jobs=-1
    )
    model.fit(X, y)

    df_sorted = df.sort_values("obs_time").reset_index(drop=True)
    last_time = pd.to_datetime(df_sorted["obs_time"].iloc[-1])

    history = df_sorted["temp_c"].astype(float).tolist()
    preds = []

    # lags 固定与 features.py 一致
    lags = (1,2,3,6,12,24)

    for i in range(1, horizon_hours + 1):
        target_time = last_time + pd.Timedelta(hours=i)

        def lag(k):
            return history[-k] if len(history) >= k else np.nan

        row = {f"temp_c_lag{k}": lag(k) for k in lags}
        row["hour"] = target_time.hour
        row["dow"] = target_time.dayofweek

        if any(pd.isna(v) for v in row.values()):
            break

        x = np.array([[row[c] for c in [f"temp_c_lag{k}" for k in lags] + ["hour","dow"]]])
        yhat = float(model.predict(x)[0])
        history.append(yhat)

        preds.append({"target_time": target_time, "yhat_temp_c": yhat, "model_name": model_name})

    return pd.DataFrame(preds)

def detect_anomalies_simple(df: pd.DataFrame, metric="temp_c", z_thresh=2.8):
    """简单异常检测：z-score"""
    s = df[metric].astype(float)
    mu = float(s.mean())
    sigma = float(s.std(ddof=0) or 1.0)
    z = (s - mu) / sigma

    out = []
    for t, v, zz in zip(pd.to_datetime(df["obs_time"]), s, z):
        if abs(float(zz)) >= z_thresh:
            out.append({
                "time": t,
                "value": float(v),
                "score": float(abs(zz)),
                "reason": f"z-score={float(zz):.2f} >= {z_thresh}"
            })
    return out
