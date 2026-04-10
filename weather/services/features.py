import pandas as pd

def build_lag_features(df: pd.DataFrame, y_col="temp_c", lags=(1,2,3,6,12,24)):
    """构造时间序列滞后特征 + 时间特征
    需要 df 包含 obs_time, y_col
    """
    out = df.copy()
    out = out.sort_values("obs_time")

    for l in lags:
        out[f"{y_col}_lag{l}"] = out[y_col].shift(l)

    dt = pd.to_datetime(out["obs_time"])
    out["hour"] = dt.dt.hour
    out["dow"] = dt.dt.dayofweek

    out = out.dropna().reset_index(drop=True)
    X_cols = [c for c in out.columns if c.startswith(f"{y_col}_lag")] + ["hour", "dow"]
    return out, X_cols
